from typing import Any
import csv
import io
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import desc
from sqlmodel import select
from db import SessionDep, supabase
from models import Datasets, Runs, Results
from utils import verifyUserTokenSession
from runner import run_tests
from judge import judge_questions

router = APIRouter(prefix="/api/runs", dependencies=[Depends(verifyUserTokenSession)])

class RunCreateRequest(BaseModel):
    dataset_id: int
    model: str = "gemini-3.5-flash-lite"
    system_prompt: str = "You are a helpful assistant."
    judge_model: str = "gemini-3.5-flash-lite"

@router.post("/")
async def createRun(
    payload: RunCreateRequest,
    session: SessionDep,
    user: dict[Any, Any] = Depends(verifyUserTokenSession),
):
    dataset = session.get(Datasets, payload.dataset_id)
    if not dataset or dataset.user_id != user["id"]:
        raise HTTPException(status_code=404, detail="Dataset not found")

    try:
        file_bytes = supabase.storage.from_("datasets").download(dataset.source_path)
        csv_file = io.StringIO(file_bytes.decode("utf-8"))
        rows = list(csv.DictReader(csv_file))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load dataset file: {str(e)}")

    if not rows:
        raise HTTPException(status_code=400, detail="Dataset is empty")

    data = await run_tests(rows, payload.system_prompt, payload.model)
    scores = await judge_questions(data, payload.judge_model)

    avg_score = sum(s["score"] for s in scores) / len(scores) if scores else 0.0

    run = Runs(
        dataset_id=payload.dataset_id,
        model=payload.model,
        system_prompt=payload.system_prompt,
        judge_model=payload.judge_model,
        avg_score=avg_score,
        total=len(data),
        status="Completed"
    )
    session.add(run)
    session.commit()
    session.refresh(run)

    for idx, (row, result, score) in enumerate(zip(rows, data, scores)):
        res = Results(
            run_id=run.id,
            idx=idx,
            question=row.get("input", ""),
            expected=row.get("expected"),
            response=result["response"],
            score=score["score"],
            reason=score["reason"],
        )
        session.add(res)
    session.commit()

    return {
        "run_id": run.id,
        "avg_score": avg_score,
        "total": len(data),
        "status": "completed"
    }

@router.get("/")
async def getRuns(
    search: str | None = None,
    session: SessionDep = None,# type: ignore
    user: dict[Any, Any] = Depends(verifyUserTokenSession),
):
    runs_stmt = (
        select(Runs, Datasets.name)
        .join(Datasets)
        .where(Datasets.user_id == user["id"])
    )
    if search:
        from sqlalchemy import or_, cast, String
        runs_stmt = runs_stmt.where(
            or_(
                Datasets.name.ilike(f"%{search}%"),
                Runs.model.ilike(f"%{search}%"),
                cast(Runs.id, String).ilike(f"%{search}%")
            )
        )
    runs_stmt = runs_stmt.order_by(desc(Runs.created_at))
    runs = session.exec(runs_stmt).all()
    
    response = []
    for run, dataset_name in runs:
        results_stmt = select(Results).where(Results.run_id == run.id).order_by(Results.idx)
        results = session.exec(results_stmt).all()
        
        response.append({
            **run.model_dump(),
            "datasetName": dataset_name,
            "results": [r.model_dump() for r in results]
        })
    return response

