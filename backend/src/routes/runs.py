import csv
import io
import json
from datetime import UTC, datetime, timedelta
from difflib import unified_diff
from typing import Any, Literal, cast

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel
from sqlalchemy import case, desc, func
from sqlmodel import Session, select

from src.config import settings
from src.db import SessionDep, supabase
from src.deps import get_llm_provider
from src.judge import judge_questions
from src.models import (
    Datasets,
    PromptRegistry,
    PromptVersion,
    ProofUserRole,
    Results,
    Runs,
    TokenUsage,
    Users,
)
from src.rate_limit import check_concurrent_run, rate_limit_runs, release_concurrent_run
from src.runner import run_tests
from src.utils import (
    get_current_user,
    require_member,
    require_viewer,
    sanitize_prompt,
    sanitize_text,
    validate_scorer_weights,
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
    prompt_version_id: int | None = None


def _prompt_version_summaries(session: Session, runs: list[Runs]) -> dict[int, dict]:
    """vN + hash for the prompt version each run used, in one query per request."""
    ids: set[int] = {
        run.prompt_version_id for run in runs if run.prompt_version_id is not None
    }
    if not ids:
        return {}
    versions = session.exec(
        select(PromptVersion).where(PromptVersion.id.in_(ids))  # type: ignore[union-attr]
    ).all()
    summaries: dict[int, dict] = {}
    for v in versions:
        if v.id is None:
            continue
        summaries[v.id] = {
            "id": v.id,
            "registry_id": v.registry_id,
            "version_number": v.sequence,
            "content_hash": v.content_hash,
            "deleted": v.deleted_at is not None,
        }
    return summaries


def _summary_for(summaries: dict[int, dict], run: Runs) -> dict | None:
    if run.prompt_version_id is None:
        return None
    return summaries.get(run.prompt_version_id)


def resolve_system_prompt(
    session: Session, user: Users, payload: RunCreateRequest
) -> str:
    """Use the selected immutable prompt version when given, else the raw prompt."""
    if payload.prompt_version_id is None:
        return sanitize_prompt(payload.system_prompt)

    version = session.get(PromptVersion, payload.prompt_version_id)
    if not version or version.deleted_at is not None:
        raise HTTPException(
            status_code=404,
            detail={"error": "Prompt version not found", "code": "not_found"},
        )

    registry = session.get(PromptRegistry, version.registry_id)
    if not registry or registry.deleted_at is not None:
        raise HTTPException(
            status_code=404,
            detail={"error": "Prompt registry not found", "code": "not_found"},
        )
    if user.role != ProofUserRole.ADMIN and registry.user_id != user.id:
        raise HTTPException(
            status_code=403,
            detail={"error": "Not your prompt registry", "code": "forbidden"},
        )

    return sanitize_prompt(version.content)


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

    clean_system_prompt = resolve_system_prompt(session, user, payload)
    clean_judge_model = sanitize_text(payload.judge_model, max_length=100)
    # Per-request weights override the dataset default; null means system defaults.
    scorer_weights = validate_scorer_weights(
        payload.scorer_weights
    ) or validate_scorer_weights(dataset.scorer_weights)
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
        scores = await judge_questions(
            data, clean_judge_model, provider_judge, scorer_weights
        )
    finally:
        await release_concurrent_run(user.id)
    avg_score = sum(s["score"] for s in scores) / len(scores) if scores else 0.0
    run = Runs(
        dataset_id=payload.dataset_id,
        model=payload.model,
        provider=payload.provider,
        provider_judge=payload.judge_provider,
        system_prompt=clean_system_prompt,
        scorer_weights=scorer_weights,
        prompt_version_id=payload.prompt_version_id,
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
    first_with_price: dict = next(
        (r for r in all_responses if r.get("input_cost_per_1m") is not None), {}
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
        if first_with_price.get("input_cost_per_1m")
        else None,
        output_cost_per_1m=Decimal(str(first_with_price.get("output_cost_per_1m")))
        if first_with_price.get("output_cost_per_1m")
        else None,
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

    summaries = _prompt_version_summaries(session, [run for run, _ in runs])
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
                "prompt_version": _summary_for(summaries, run),
                "datasetName": dataset_name,
                "results": [r.model_dump() for r in results],
            }
        )
    return response


@router.get("/usage")
async def get_usage(
    session: SessionDep,
    user: Users = Depends(get_current_user),
    _: Users = Depends(require_viewer),
    days: int = 30,
):
    """Totals, per-dataset breakdown and daily trend in one grouped query."""
    days = max(1, min(days, 365))
    since = datetime.now(UTC) - timedelta(days=days)

    day = func.date(TokenUsage.created_at).label("day")
    unpriced = func.count(
        func.distinct(case((cast(Any, TokenUsage.cost_usd == None), TokenUsage.run_id)))
    ).label("unpriced")
    estimated = func.count(
        func.distinct(case((cast(Any, TokenUsage.usage_estimated), TokenUsage.run_id)))
    ).label("estimated")

    stmt = (
        select(  # type: ignore[call-overload]
            day,
            Datasets.id,
            Datasets.name,
            func.count(func.distinct(TokenUsage.run_id)),
            func.coalesce(func.sum(TokenUsage.prompt_tokens), 0),
            func.coalesce(func.sum(TokenUsage.completion_tokens), 0),
            func.coalesce(func.sum(TokenUsage.cost_usd), 0),
            unpriced,
            estimated,
        )
        .join(Runs, Runs.id == TokenUsage.run_id)
        .join(Datasets, Datasets.id == Runs.dataset_id)
        .where(
            Datasets.user_id == user.id,
            Datasets.deleted_at == None,
            Runs.deleted_at == None,
            TokenUsage.created_at >= since,
        )
        .group_by(day, Datasets.id, Datasets.name)
        .order_by(day)
    )
    rows = session.exec(stmt).all()

    totals = {
        "runs": 0,
        "prompt_tokens": 0,
        "completion_tokens": 0,
        "cost_usd": 0.0,
        "unpriced_runs": 0,
        "estimated": False,
    }
    by_dataset: dict[int, dict] = {}
    by_day: dict[str, dict] = {}

    for (
        day_value,
        dataset_id,
        dataset_name,
        run_count,
        prompt_tokens,
        completion_tokens,
        cost,
        unpriced_count,
        estimated_count,
    ) in rows:
        cost_value = float(cost or 0)
        key = str(day_value)

        totals["runs"] += run_count
        totals["prompt_tokens"] += prompt_tokens
        totals["completion_tokens"] += completion_tokens
        totals["cost_usd"] += cost_value
        totals["unpriced_runs"] += unpriced_count
        totals["estimated"] = totals["estimated"] or bool(estimated_count)

        dataset_entry = by_dataset.setdefault(
            dataset_id,
            {
                "dataset_id": dataset_id,
                "dataset_name": dataset_name,
                "runs": 0,
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "cost_usd": 0.0,
                "unpriced_runs": 0,
            },
        )
        dataset_entry["runs"] += run_count
        dataset_entry["prompt_tokens"] += prompt_tokens
        dataset_entry["completion_tokens"] += completion_tokens
        dataset_entry["cost_usd"] += cost_value
        dataset_entry["unpriced_runs"] += unpriced_count

        day_entry = by_day.setdefault(
            key,
            {"date": key, "runs": 0, "tokens": 0, "cost_usd": 0.0},
        )
        day_entry["runs"] += run_count
        day_entry["tokens"] += prompt_tokens + completion_tokens
        day_entry["cost_usd"] += cost_value

    totals["cost_usd"] = round(totals["cost_usd"], 6)
    daily = sorted(by_day.values(), key=lambda d: d["date"])

    return {
        "days": days,
        "totals": totals,
        "datasets": sorted(
            by_dataset.values(), key=lambda d: d["cost_usd"], reverse=True
        ),
        "daily": daily,
    }


def _owned_run(session: Session, run_id: int, user: Users) -> tuple[Runs, Datasets]:
    run = session.get(Runs, run_id)
    if not run or run.deleted_at is not None:
        raise HTTPException(
            status_code=404, detail={"error": "Run not found", "code": "not_found"}
        )
    dataset = session.get(Datasets, run.dataset_id)
    if not dataset or dataset.deleted_at is not None:
        raise HTTPException(
            status_code=404,
            detail={"error": "Dataset not found", "code": "not_found"},
        )
    if user.role != ProofUserRole.ADMIN and dataset.user_id != user.id:
        raise HTTPException(
            status_code=403, detail={"error": "Not your run", "code": "forbidden"}
        )
    return run, dataset


def _run_cost(session: Session, run_id: int) -> tuple[float | None, bool]:
    rows = session.exec(select(TokenUsage).where(TokenUsage.run_id == run_id)).all()
    if not rows:
        return None, False
    total = sum(float(row.cost_usd) for row in rows if row.cost_usd is not None)
    return total, any(row.cost_usd is None for row in rows)


@router.get("/compare")
async def compare_runs(
    run_a: int,
    run_b: int,
    session: SessionDep,
    user: Users = Depends(get_current_user),
    _: Users = Depends(require_viewer),
):
    """Diff matrix for two runs: scores, responses and cost."""
    run_a_obj, dataset_a = _owned_run(session, run_a, user)
    run_b_obj, dataset_b = _owned_run(session, run_b, user)

    results_a = {
        r.idx: r
        for r in session.exec(
            select(Results).where(Results.run_id == run_a, Results.deleted_at == None)
        ).all()
    }
    results_b = {
        r.idx: r
        for r in session.exec(
            select(Results).where(Results.run_id == run_b, Results.deleted_at == None)
        ).all()
    }

    rows = []
    for idx in sorted(set(results_a) | set(results_b)):
        result_a = results_a.get(idx)
        result_b = results_b.get(idx)
        score_a = result_a.score if result_a else None
        score_b = result_b.score if result_b else None
        response_a = result_a.response if result_a else None
        response_b = result_b.response if result_b else None

        if score_a is not None and score_b is not None:
            delta = score_b - score_a
            status = (
                "improved" if delta > 0 else "regressed" if delta < 0 else "unchanged"
            )
        elif score_b is not None:
            delta = None
            status = "only_b"
        elif score_a is not None:
            delta = None
            status = "only_a"
        else:
            delta = None
            status = "no_score"

        response_diff = "".join(
            unified_diff(
                (response_a or "").splitlines(keepends=True),
                (response_b or "").splitlines(keepends=True),
                fromfile=f"run #{run_a}",
                tofile=f"run #{run_b}",
            )
        )

        rows.append(
            {
                "idx": idx,
                "question": result_a.question
                if result_a
                else result_b.question
                if result_b
                else "",
                "expected": result_a.expected
                if result_a
                else result_b.expected
                if result_b
                else None,
                "response_a": response_a,
                "response_b": response_b,
                "reason_a": result_a.reason if result_a else None,
                "reason_b": result_b.reason if result_b else None,
                "score_a": score_a,
                "score_b": score_b,
                "score_delta": delta,
                "status": status,
                "response_diff": response_diff,
            }
        )

    def _pass_rate(results: dict[int, Results]) -> tuple[float, int, int]:
        scores = [r.score for r in results.values() if r.score is not None]
        passed = len([score for score in scores if score >= 4])
        failed = len([score for score in scores if score <= 2])
        rate = round(passed / len(scores) * 100, 1) if scores else 0.0
        return rate, len(scores), failed

    pass_a, total_a, fail_a = _pass_rate(results_a)
    pass_b, total_b, fail_b = _pass_rate(results_b)
    avg_a = float(run_a_obj.avg_score) if run_a_obj.avg_score is not None else None
    avg_b = float(run_b_obj.avg_score) if run_b_obj.avg_score is not None else None
    score_delta = avg_b - avg_a if avg_a is not None and avg_b is not None else None
    cost_a, unpriced_a = _run_cost(session, run_a)
    cost_b, unpriced_b = _run_cost(session, run_b)
    cost_delta = (
        round(cost_b - cost_a, 6) if cost_a is not None and cost_b is not None else None
    )

    summaries = _prompt_version_summaries(session, [run_a_obj, run_b_obj])

    return {
        "run_a": {
            "id": run_a_obj.id,
            "dataset_id": run_a_obj.dataset_id,
            "dataset_name": dataset_a.name,
            "model": run_a_obj.model,
            "provider": run_a_obj.provider,
            "judge_model": run_a_obj.judge_model,
            "avg_score": avg_a,
            "total": run_a_obj.total,
            "cost_usd": cost_a,
            "unpriced": unpriced_a,
            "prompt_version": _summary_for(summaries, run_a_obj),
            "scorer_weights": run_a_obj.scorer_weights,
        },
        "run_b": {
            "id": run_b_obj.id,
            "dataset_id": run_b_obj.dataset_id,
            "dataset_name": dataset_b.name,
            "model": run_b_obj.model,
            "provider": run_b_obj.provider,
            "judge_model": run_b_obj.judge_model,
            "avg_score": avg_b,
            "total": run_b_obj.total,
            "cost_usd": cost_b,
            "unpriced": unpriced_b,
            "prompt_version": _summary_for(summaries, run_b_obj),
            "scorer_weights": run_b_obj.scorer_weights,
        },
        "same_dataset": run_a_obj.dataset_id == run_b_obj.dataset_id,
        "metrics": {
            "pass_rate_a": pass_a,
            "pass_rate_b": pass_b,
            "pass_rate_delta": round(pass_b - pass_a, 1),
            "scored_a": total_a,
            "scored_b": total_b,
            "failures_a": fail_a,
            "failures_b": fail_b,
            "score_delta": score_delta,
            "cost_delta": cost_delta,
        },
        "regression": {
            "regressed": score_delta is not None
            and score_delta < -settings.REGRESSION_THRESHOLD,
            "delta": score_delta,
            "threshold": settings.REGRESSION_THRESHOLD,
        },
        "rows": rows,
    }


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
        "prompt_version": _summary_for(_prompt_version_summaries(session, [run]), run),
        "datasetName": dataset.name,
        "results": [r.model_dump() for r in results],
    }


def _csv_cell(value: object) -> str:
    if value is None:
        return ""
    text = str(value)
    # Stop spreadsheet formula injection from model or dataset output.
    if text.startswith(("=", "+", "-", "@")):
        return "'" + text
    return text


@router.get("/{run_id}/export")
async def export_run(
    run_id: int,
    session: SessionDep,
    user: Users = Depends(get_current_user),
    _: Users = Depends(require_viewer),
    format: Literal["csv", "json"] = "csv",
):
    """Download a run's results as CSV or JSON."""
    run, dataset = _owned_run(session, run_id, user)
    results = session.exec(
        select(Results)
        .where(Results.run_id == run_id, Results.deleted_at == None)
        .order_by(Results.idx)  # type: ignore[arg-type]
    ).all()

    headers = {
        "Content-Disposition": f'attachment; filename="run-{run_id}-results.{format}"'
    }

    if format == "csv":
        buffer = io.StringIO()
        writer = csv.writer(buffer)
        writer.writerow(["idx", "question", "expected", "response", "score", "reason"])
        for result in results:
            writer.writerow(
                [
                    result.idx,
                    _csv_cell(result.question),
                    _csv_cell(result.expected),
                    _csv_cell(result.response),
                    "" if result.score is None else result.score,
                    _csv_cell(result.reason),
                ]
            )
        return Response(
            content=buffer.getvalue(),
            media_type="text/csv; charset=utf-8",
            headers=headers,
        )

    cost, unpriced = _run_cost(session, run_id)
    payload = {
        "run": {
            "id": run.id,
            "dataset_id": run.dataset_id,
            "dataset_name": dataset.name,
            "model": run.model,
            "provider": run.provider,
            "judge_model": run.judge_model,
            "avg_score": run.avg_score,
            "total": run.total,
            "status": run.status,
            "created_at": run.created_at,
            "prompt_version": _summary_for(
                _prompt_version_summaries(session, [run]), run
            ),
            "scorer_weights": run.scorer_weights,
            "cost_usd": cost,
            "unpriced": unpriced,
        },
        "results": [
            {
                "idx": result.idx,
                "question": result.question,
                "expected": result.expected,
                "response": result.response,
                "score": result.score,
                "reason": result.reason,
            }
            for result in results
        ],
    }
    return Response(
        content=json.dumps(payload, default=str),
        media_type="application/json",
        headers=headers,
    )


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
        "input_cost_per_1m": float(tu.input_cost_per_1m)
        if tu.input_cost_per_1m
        else None,
        "output_cost_per_1m": float(tu.output_cost_per_1m)
        if tu.output_cost_per_1m
        else None,
        "cached_tokens": tu.cached_tokens,
        "reasoning_tokens": tu.reasoning_tokens,
        "total_latency_s": tu.total_latency_s,
        "total_attempts": tu.total_attempts,
        "usage_estimated": tu.usage_estimated,
        "pricing": "estimated" if tu.cost_usd is not None else "unknown",
    }
