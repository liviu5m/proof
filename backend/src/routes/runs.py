import csv
import io
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy import desc
from sqlmodel import select

from src.db import SessionDep, supabase
from src.deps import get_llm_provider
from src.judge import judge_questions
from src.models import Datasets, ProofUserRole, Results, Runs, Users
from src.rate_limit import check_concurrent_run, rate_limit_runs, release_concurrent_run
from src.runner import run_tests
from src.utils import (
    get_current_user,
    require_member,
    require_viewer,
    sanitize_prompt,
    sanitize_text,
    verify_csrf,
    verifyUserTokenSession,
)
from src.validators import validate_csv_headers, validate_csv_rows

router = APIRouter(
    prefix="/api/runs",
    dependencies=[Depends(verifyUserTokenSession), Depends(rate_limit_runs)],
)


class RunCreateRequest(BaseModel):
    dataset_id: int
    model: str = "gemini-3.5-flash-lite"
    system_prompt: str = "You are a helpful assistant."
    judge_model: str = "gemini-3.5-flash-lite"
    provider: str = "google"
    judge_provider: str = "google"
    ollama_base_url: str | None = None
    ollama_base_url_judge: str | None = None


@router.post("/")
async def createRun(
    payload: RunCreateRequest,
    session: SessionDep,
    user: Users = Depends(get_current_user),
    _: Users = Depends(require_member),
    __: Request = Depends(verify_csrf),
):
    if not user or not user.id:
        raise HTTPException(
            status_code=404, detail={"error": "User not found", "code": "not_found"}
        )
    dataset = session.get(Datasets, payload.dataset_id)
    if not dataset or dataset.deleted_at is not None:
        raise HTTPException(
            status_code=404, detail={"error": "Dataset not found", "code": "not_found"}
        )
    if user.role != ProofUserRole.ADMIN and dataset.user_id != user.id:
        raise HTTPException(
            status_code=403, detail={"error": "Not your dataset", "code": "forbidden"}
        )
    try:
        file_bytes = supabase.storage.from_("datasets").download(dataset.source_path)
        csv_file = io.StringIO(file_bytes.decode("utf-8"))
        reader = csv.DictReader(csv_file)
        rows = list(reader)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "error": f"Failed to load dataset file: {e!s}",
                "code": "dataset_load_failed",
            },
        ) from None

    if not rows:
        raise HTTPException(
            status_code=400,
            detail={"error": "Dataset is empty", "code": "empty_dataset"},
        )

    header_errors = validate_csv_headers(reader.fieldnames or [])
    if header_errors:
        raise HTTPException(
            status_code=400, detail={"errors": header_errors, "code": "invalid_headers"}
        )

    valid_rows, row_errors = validate_csv_rows(rows)
    if row_errors:
        raise HTTPException(
            status_code=400, detail={"errors": row_errors, "code": "invalid_rows"}
        )

    clean_system_prompt = sanitize_prompt(payload.system_prompt)
    clean_judge_model = sanitize_text(payload.judge_model, max_length=100)
    await check_concurrent_run(user.id)
    provider = get_llm_provider(
        provider=payload.provider,
        user_id=user.id,
        session=session,
        ollama_base_url=payload.ollama_base_url,
    )
    provider_judge = get_llm_provider(
        provider=payload.judge_provider,
        user_id=user.id,
        session=session,
        ollama_base_url=payload.ollama_base_url_judge,
    )
    try:
        rows_as_dicts = [r.model_dump() for r in valid_rows]
        data = await run_tests(
            rows_as_dicts, clean_system_prompt, payload.model, provider
        )
        scores = await judge_questions(data, clean_judge_model, provider_judge)
    finally:
        await release_concurrent_run(user.id)
    avg_score = sum(s["score"] for s in scores) / len(scores) if scores else 0.0
    run = Runs(
        dataset_id=payload.dataset_id,
        model=payload.model,
        provider=payload.provider,
        provider_judge=payload.judge_provider,
        system_prompt=clean_system_prompt,
        judge_model=clean_judge_model,
        avg_score=avg_score,
        total=len(data),
        status="Completed",
    )
    session.add(run)
    session.commit()
    session.refresh(run)

    for idx, (row, result, score) in enumerate(
        zip(valid_rows, data, scores, strict=False)
    ):
        res = Results(
            run_id=run.id,
            idx=idx,
            question=row.input,
            expected=row.expected,
            response=result.get("response"),
            score=score["score"],
            reason=score["reason"],
        )
        session.add(res)
    session.commit()

    return {
        "run_id": run.id,
        "avg_score": avg_score,
        "total": len(data),
        "status": "completed",
    }


@router.get("/")
async def getRuns(
    search: str | None = None,
    session: SessionDep = None,  # type: ignore
    user: Users = Depends(get_current_user),
    _: Users = Depends(require_viewer),
):
    runs_stmt = (
        select(Runs, Datasets.name)
        .join(Datasets)
        .where(Datasets.deleted_at is None)
        .where(Runs.deleted_at is None)
    )
    if user.role != ProofUserRole.ADMIN:
        runs_stmt = runs_stmt.where(Datasets.user_id == user.id)
    if search:
        from sqlalchemy import String, cast, or_

        runs_stmt = runs_stmt.where(
            or_(
                Datasets.name.ilike(f"%{search}%"),
                Runs.model.ilike(f"%{search}%"),
                cast(Runs.id, String).ilike(f"%{search}%"),
            )
        )
    runs_stmt = runs_stmt.order_by(desc(Runs.created_at))
    runs = session.exec(runs_stmt).all()

    response = []
    for run, dataset_name in runs:
        results_stmt = (
            select(Results)
            .where(Results.run_id == run.id, Results.deleted_at is None)
            .order_by(Results.idx)
        )
        results = session.exec(results_stmt).all()

        response.append(
            {
                **run.model_dump(),
                "datasetName": dataset_name,
                "results": [r.model_dump() for r in results],
            }
        )
    return response


@router.get("/{run_id}")
async def get_run(
    run_id: int,
    session: SessionDep,
    user: Users = Depends(get_current_user),
    _: Users = Depends(require_viewer),
):
    run = session.get(Runs, run_id)
    if not run or run.deleted_at is not None:
        raise HTTPException(
            status_code=404, detail={"error": "Run not found", "code": "not_found"}
        )

    dataset = session.get(Datasets, run.dataset_id)
    if not dataset:
        raise HTTPException(
            status_code=404, detail={"error": "Dataset not found", "code": "not_found"}
        )

    if user.role != ProofUserRole.ADMIN and dataset.user_id != user.id:
        raise HTTPException(
            status_code=403, detail={"error": "Not your run", "code": "forbidden"}
        )

    results_stmt = (
        select(Results)
        .where(
            Results.run_id == run.id,
            Results.deleted_at is None,
        )
        .order_by(Results.idx)
    )
    results = session.exec(results_stmt).all()

    return {
        **run.model_dump(),
        "datasetName": dataset.name,
        "results": [r.model_dump() for r in results],
    }


@router.delete("/{run_id}")
async def delete_run(
    run_id: int,
    session: SessionDep,
    user: Users = Depends(get_current_user),
    _: Users = Depends(require_member),
    __: Request = Depends(verify_csrf),
):
    run = session.get(Runs, run_id)
    if not run or run.deleted_at is not None:
        raise HTTPException(
            status_code=404, detail={"error": "Run not found", "code": "not_found"}
        )

    dataset = session.get(Datasets, run.dataset_id)
    if not dataset:
        raise HTTPException(
            status_code=404, detail={"error": "Dataset not found", "code": "not_found"}
        )

    if user.role != ProofUserRole.ADMIN and dataset.user_id != user.id:
        raise HTTPException(
            status_code=403, detail={"error": "Not your run", "code": "forbidden"}
        )

    run.deleted_at = datetime.now(UTC)
    session.add(run)
    session.commit()
    return {"success": "Run deleted"}
