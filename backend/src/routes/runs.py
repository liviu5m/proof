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
from src.models import Datasets, ProofUserRole, Results, Runs, TokenUsage, Users
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
    scorer_weights: dict | None = None


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

    header_errors = validate_csv_headers(list(reader.fieldnames or []))
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
        model=payload.model,
    )
    provider_judge = get_llm_provider(
        provider=payload.judge_provider,
        user_id=user.id,
        session=session,
        ollama_base_url=payload.ollama_base_url_judge,
        model=payload.judge_model,
    )
    try:
        rows_as_dicts = [r.model_dump() for r in valid_rows]
        data = await run_tests(
            rows_as_dicts, clean_system_prompt, payload.model, provider
        )
        scores = await judge_questions(data, clean_judge_model, provider_judge, payload.scorer_weights)
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

    assert run.id is not None, "Run ID should not be None after commit"

    # Aggregate token usage from runner + judge responses
    all_responses = data + scores
    total_prompt = sum(r.get("input_tokens", 0) or 0 for r in all_responses)
    total_completion = sum(r.get("output_tokens", 0) or 0 for r in all_responses)
    total_cost = sum(r.get("cost_usd", 0) or 0 for r in all_responses)
    total_cached = sum(r.get("cached_tokens", 0) or 0 for r in all_responses)
    total_reasoning = sum(r.get("reasoning_tokens", 0) or 0 for r in all_responses)
    total_latency = sum(r.get("latency_s", 0.0) or 0.0 for r in all_responses)
    total_attempts = sum(r.get("attempts", 0) or 0 for r in all_responses)
    usage_estimated = any(r.get("usage_estimated") for r in all_responses)

    # Get prices used (from first response that has them)
    first_with_price = next(
        (r for r in all_responses if r.get("input_cost_per_1m") is not None),
        {}
    )

    from decimal import Decimal
    token_usage = TokenUsage(
        run_id=run.id,
        model=payload.model,
        provider=payload.provider,
        prompt_tokens=total_prompt,
        completion_tokens=total_completion,
        cost_usd=Decimal(str(total_cost)) if total_cost else None,
        input_cost_per_1m=Decimal(str(first_with_price.get("input_cost_per_1m"))) 
                           if first_with_price.get("input_cost_per_1m") else None,
        output_cost_per_1m=Decimal(str(first_with_price.get("output_cost_per_1m"))) 
                            if first_with_price.get("output_cost_per_1m") else None,
        cached_tokens=total_cached,
        reasoning_tokens=total_reasoning,
        total_latency_s=total_latency,
        total_attempts=total_attempts,
        usage_estimated=usage_estimated,
    )
    session.add(token_usage)

    for idx, (row, result, score) in enumerate(
        zip(valid_rows, data, scores, strict=False)
    ):
        res = Results(
            run_id=run.id,  # type: ignore[arg-type]
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
        .where(Datasets.deleted_at == None)
        .where(Runs.deleted_at == None)
    )
    if user.role != ProofUserRole.ADMIN:
        runs_stmt = runs_stmt.where(Datasets.user_id == user.id)
    if search:
        from sqlalchemy import String, cast, or_

        runs_stmt = runs_stmt.where(
            or_(
                Datasets.name.ilike(f"%{search}%"),  # type: ignore[attr-defined]
                Runs.model.ilike(f"%{search}%"),  # type: ignore[attr-defined]
                cast(Runs.id, String).ilike(f"%{search}%"),
            )
        )
    runs_stmt = runs_stmt.order_by(desc(Runs.created_at))  # type: ignore[arg-type]
    runs = session.exec(runs_stmt).all()

    response = []
    for run, dataset_name in runs:
        results_stmt = (
            select(Results)
            .where(Results.run_id == run.id, Results.deleted_at == None)
            .order_by(Results.idx)  # type: ignore[arg-type]
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
            Results.deleted_at == None,
        )
        .order_by(Results.idx)  # type: ignore[arg-type]
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


@router.get("/{run_id}/cost")
async def get_run_cost(
    run_id: int,
    session: SessionDep,
    user: Users = Depends(get_current_user),
    _: Users = Depends(require_viewer),
):
    """Get token usage and cost for a run."""
    tu = session.exec(select(TokenUsage).where(TokenUsage.run_id == run_id)).first()
    if not tu:
        return {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "cost_usd": None,
            "input_cost_per_1m": None,
            "output_cost_per_1m": None,
            "cached_tokens": 0,
            "reasoning_tokens": 0,
            "total_latency_s": 0.0,
            "total_attempts": 0,
            "usage_estimated": False,
            "pricing": "unknown",
        }
    return {
        "prompt_tokens": tu.prompt_tokens,
        "completion_tokens": tu.completion_tokens,
        "cost_usd": float(tu.cost_usd) if tu.cost_usd is not None else None,
        "input_cost_per_1m": float(tu.input_cost_per_1m) if tu.input_cost_per_1m else None,
        "output_cost_per_1m": float(tu.output_cost_per_1m) if tu.output_cost_per_1m else None,
        "cached_tokens": tu.cached_tokens,
        "reasoning_tokens": tu.reasoning_tokens,
        "total_latency_s": tu.total_latency_s,
        "total_attempts": tu.total_attempts,
        "usage_estimated": tu.usage_estimated,
        "pricing": "estimated" if tu.cost_usd is not None else "unknown",
    }
