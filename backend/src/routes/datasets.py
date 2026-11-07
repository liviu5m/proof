from typing import Any
import hashlib
import uuid
import csv
import io
from fastapi import APIRouter, Depends, File, Form, UploadFile, HTTPException
from pydantic import BaseModel
from sqlmodel import select
from src.db import SessionDep, supabase
from src.models import Datasets, Users
from src.utils import get_current_user, scan_file, verifyUserTokenSession, sanitize_text
from src.validators import validate_csv_headers, validate_csv_rows, REQUIRED_COLUMNS

router = APIRouter(prefix="/api/dataset", dependencies=[Depends(verifyUserTokenSession)])

class Dataset(BaseModel):
    name: str
    file: str

@router.post("/")
async def createDataset(
    session: SessionDep, 
    file: UploadFile = File(...),
    name: str = Form(...),
    user: Users = Depends(get_current_user),
    ):

    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(
            status_code=400,
            detail={"error": "Only CSV files are allowed", "code": "invalid_file_type"}
        )

    MAX_FILE_SIZE = 5 * 1024 * 1024  
    contents = await file.read()
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail={"error": f"File too large. Max size is 5 MB.", "code": "file_too_large"}
        )

    await scan_file(file)
    name = sanitize_text(name, max_length=200)
    text = contents.decode("utf-8")
    
    csv_file = io.StringIO(text)
    reader = csv.DictReader(csv_file)
    rows = list(reader)
    
    header_errors = validate_csv_headers(reader.fieldnames or [])
    if header_errors:
        raise HTTPException(status_code=400, detail={"errors": header_errors, "code": "invalid_headers"})
    
    valid_rows, row_errors = validate_csv_rows(rows)
    if row_errors:
        raise HTTPException(status_code=400, detail={"errors": row_errors, "code": "invalid_rows"})

    file_hash = hashlib.sha256(contents).hexdigest()
    item_count = len(valid_rows)

    file_id = uuid.uuid4().hex[:8]
    file_path = f"{user.id}/{file_id}_{file.filename}"

    res = supabase.storage.from_("datasets").upload(
        path=file_path,
        file=contents,
        file_options={"content-type": "text/csv", "upsert": "true"}
    )

    dataset = Datasets(
        name=name,
        source_path=file_path,
        item_count=item_count,
        hash=file_hash,
        user_id=user.id
    )
    session.add(dataset)
    session.commit()
    session.refresh(dataset)
    return {"id": dataset.id, "path": file_path}

@router.get("/")
async def getDatasets(
    session: SessionDep,
    searchQuery: str = "",
    user: Users = Depends(get_current_user),
):
    stmt = select(Datasets).where(Datasets.user_id == user.id)
    if searchQuery:
        stmt = stmt.where(Datasets.name.ilike(f"%{searchQuery}%"))
    datasets = session.exec(stmt).all()
    return [d.model_dump() for d in datasets]

@router.get("/{dataset_id}")
async def getDataset(dataset_id: int, session: SessionDep, user: Users = Depends(get_current_user)):
    stmt = select(Datasets).where(Datasets.id == dataset_id, Datasets.user_id == user.id)
    dataset = session.exec(stmt).first()
    if dataset is None:
        return {"error": "Dataset not found"}
    return dataset.model_dump()

@router.delete("/{dataset_id}")
async def deleteDataset(dataset_id: int, session: SessionDep, user: Users = Depends(get_current_user)):
    stmt = select(Datasets).where(Datasets.id == dataset_id, Datasets.user_id == user.id)
    dataset = session.exec(stmt).first()
    if dataset is None:
        return {"error": "Dataset not found"}
    session.delete(dataset)
    session.commit()
    return {"success": "Dataset deleted"}

@router.get("/{dataset_id}/download")
async def downloadDataset(dataset_id: int, session: SessionDep, user: Users = Depends(get_current_user)):
    stmt = select(Datasets).where(Datasets.id == dataset_id, Datasets.user_id == user.id)
    dataset = session.exec(stmt).first()
    if dataset is None:
        return {"error": "Dataset not found"}
    try:
        res = supabase.storage.from_("datasets").create_signed_url(dataset.source_path, 3600)
        url = res.get("signedURL") or res.get("signedUrl")
        return {"url": url}
    except Exception as e:
        return {"error": str(e)}
