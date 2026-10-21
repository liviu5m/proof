from typing import Any
import hashlib
import uuid
from fastapi import APIRouter, Depends, File, Form, UploadFile
from pydantic import BaseModel
from db import SessionDep, supabase
from models import Datasets
from utils import verifyUserTokenSession

router = APIRouter(prefix="/api/dataset", dependencies=[Depends(verifyUserTokenSession)])

class Dataset(BaseModel):
    name: str
    file: str

@router.post("/")
async def createDataset(
    session: SessionDep, 
    file: UploadFile = File(...),
    name: str = Form(...),
    user: dict[Any, Any] = Depends(verifyUserTokenSession),
    ):
    contents = await file.read()
    file_hash = hashlib.sha256(contents).hexdigest()
    item_count = max(0, len(contents.decode("utf-8").splitlines()) - 1)

    file_id = uuid.uuid4().hex[:8]
    file_path = f"{user['id']}/{file_id}_{file.filename}"

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
        user_id=user["id"]
    )
    session.add(dataset)
    session.commit()
    session.refresh(dataset)
    return {"id": dataset.id, "path": file_path}
@router.get("/")
async def getDatasets(session: SessionDep, user: dict[Any, Any] = Depends(verifyUserTokenSession)):
    return [dataset.dict() for dataset in session.query(Datasets).filter(Datasets.user_id == user["id"])]

@router.get("/{dataset_id}")
async def getDataset(dataset_id: int, session: SessionDep, user: dict[Any, Any] = Depends(verifyUserTokenSession)):
    dataset = session.query(Datasets).filter(Datasets.id == dataset_id, Datasets.user_id == user["id"]).first()
    if dataset is None:
        return {"error": "Dataset not found"}
    return dataset.dict()

@router.delete("/{dataset_id}")
async def deleteDataset(dataset_id: int, session: SessionDep, user: dict[Any, Any] = Depends(verifyUserTokenSession)):
    dataset = session.query(Datasets).filter(Datasets.id == dataset_id, Datasets.user_id == user["id"]).first()
    if dataset is None:
        return {"error": "Dataset not found"}
    session.delete(dataset)
    session.commit()
    return {"success": "Dataset deleted"}
