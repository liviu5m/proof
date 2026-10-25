import csv
from sqlmodel import Session
import typer
from .utils import get_file_hash
from .db import engine
from sqlmodel import select

from .db import SessionDep
from .models import Datasets, Results, Runs
from .runner import run_tests
from .judge import judge_questions

app = typer.Typer()

dataset_app = typer.Typer(name="dataset", help="Manage datasets")
app.add_typer(dataset_app, name="dataset")


def load_dataset(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


@app.command()
def run(
    questions: str = typer.Option(..., "--questions", "-q", help="Path to CSV"),
    prompt: str = typer.Option("You are a helpful assistant.", "--prompt", "-p"),
    model: str = typer.Option("gemini-3.5-flash-lite", "--model", "-m"),
    judge_modal: str = typer.Option("gemini-3.1-flash-lite", "--judge-model", "-jm"),
):
    with Session(engine) as session:
        hash = get_file_hash(questions) 

        datasetsStmt = select(Datasets).where(Datasets.hash == hash)
        datasets = session.exec(datasetsStmt).all()
        if not datasets:
            dataset = Datasets(name=questions, source_path=questions, hash=hash)
            session.add(dataset)
            session.commit()
        else:
            dataset = datasets[0]
        rows = load_dataset(questions)
        dataset.item_count = len(rows)
        session.commit()
        data = run_tests(rows, prompt, model)
        scores = judge_questions(data, judge_modal)
        avg = 0
        if scores:
            avg = sum(scores) / len(scores)
            typer.echo(f"\nScore: {avg:.1f}/5")

        assert dataset.id is not None
        run = Runs(dataset_id=dataset.id, model=model, system_prompt=prompt, judge_model=judge_modal, avg_score=avg, total=len(data))
        session.add(run)
        session.commit()
        session.refresh(run)
        print(run)
        print(rows)
        for idx, (row, result, score) in enumerate(zip(rows, data, scores)):
            res = Results(
                run_id=run.id,
                idx=idx,
                question=row["input"],
                expected=row.get("expected"),
                response=result["response"],
                score=score["score"],
                reason=None,
            )
            session.add(res)
        session.commit()

@app.command()
def compare(
    run_a: int = typer.Argument(..., help="First run ID (baseline)"),
    run_b: int = typer.Argument(..., help="Second run ID (candidate)"),
    show: int = typer.Option(None, "--show", "-s", help="Show full diff for specific question index"),
    only_regressed: bool = typer.Option(False, "--only-regressed", help="Show only regressed questions"),
    only_improved: bool = typer.Option(False, "--only-improved", help="Show only improved questions"),
):
    """Compare two runs side by side."""
    with Session(engine) as session:
        run_a_obj = session.get(Runs, run_a)
        run_b_obj = session.get(Runs, run_b)

        if not run_a_obj or not run_b_obj:
            typer.echo("Error: One or both run IDs not found", err=True)
            raise typer.Exit(1)

        if run_a_obj.dataset_id != run_b_obj.dataset_id:
            typer.echo("Warning: Runs are from different datasets", err=True)

        results_a = session.exec(
            select(Results).where(Results.run_id == run_a).order_by(Results.idx)
        ).all()
        results_b = session.exec(
            select(Results).where(Results.run_id == run_b).order_by(Results.idx)
        ).all()

        results_a_by_idx = {r.idx: r for r in results_a}
        results_b_by_idx = {r.idx: r for r in results_b}

        all_indices = sorted(set(results_a_by_idx.keys()) | set(results_b_by_idx.keys()))

        total_a = len([r for r in results_a if r.score is not None])
        total_b = len([r for r in results_b if r.score is not None])
        avg_a = sum(r.score for r in results_a if r.score is not None) / total_a if total_a else 0
        avg_b = sum(r.score for r in results_b if r.score is not None) / total_b if total_b else 0
        pass_a = len([r for r in results_a if r.score and r.score >= 4])
        pass_b = len([r for r in results_b if r.score and r.score >= 4])
        fail_a = len([r for r in results_a if r.score and r.score <= 2])
        fail_b = len([r for r in results_b if r.score and r.score <= 2])

        typer.echo("")
        typer.echo("╭" + "─" * 76 + "╮")
        typer.echo(f"│  COMPARE: Run #{run_a} (baseline)  →  Run #{run_b} (candidate)")
        typer.echo(f"│  Dataset ID: {run_a_obj.dataset_id}  |  Model: {run_a_obj.model}  |  Judge: {run_a_obj.judge_model}")
        typer.echo("╰" + "─" * 76 + "╯")
        typer.echo("")

        typer.echo("  OVERALL SCORE")
        typer.echo("  ┌─────────────┬──────────┬──────────┬──────────┐")
        typer.echo("  │ Metric      │ Run #{}  │ Run #{}  │ Delta    │".format(run_a, run_b))
        typer.echo("  ├─────────────┼──────────┼──────────┼──────────┤")
        delta_avg = avg_b - avg_a
        delta_pass = (pass_b / total_b * 100 if total_b else 0) - (pass_a / total_a * 100 if total_a else 0)
        delta_fail = fail_b - fail_a
        typer.echo("  │ Avg Score   │ {:>6.2f} │ {:>6.2f} │ {:>+6.2f} │".format(avg_a, avg_b, delta_avg))
        typer.echo("  │ Pass Rate   │ {:>6.1f}% │ {:>6.1f}% │ {:>+6.1f}% │".format(
            pass_a / total_a * 100 if total_a else 0,
            pass_b / total_b * 100 if total_b else 0,
            delta_pass
        ))
        typer.echo("  │ Failures    │ {:>6}   │ {:>6}   │ {:>+6}   │".format(fail_a, fail_b, delta_fail))
        typer.echo("  └─────────────┴──────────┴──────────┴──────────┘")
        typer.echo("")

        typer.echo("  PER-QUESTION BREAKDOWN")
        typer.echo("  ┌────┬──────────────────────────────────────┬───────┬───────┬────────┬────────────┐")
        typer.echo("  │ #  │ Question                             │ R#{}  │ R#{}  │ Change │ Verdict    │".format(run_a, run_b))
        typer.echo("  ├────┼──────────────────────────────────────┼───────┼───────┼────────┼────────────┤")

        regressed_count = 0
        improved_count = 0

        for idx in all_indices:
            ra = results_a_by_idx.get(idx)
            rb = results_b_by_idx.get(idx)

            score_a = ra.score if ra and ra.score is not None else None
            score_b = rb.score if rb and rb.score is not None else None

            if score_a is None and score_b is None:
                continue

            change = ""
            verdict = ""

            if score_a is not None and score_b is not None:
                diff = score_b - score_a
                change = f"{diff:+d}"
                if diff > 0:
                    verdict = "✅ IMPROVED"
                    improved_count += 1
                elif diff < 0:
                    verdict = "❌ REGRESSED"
                    regressed_count += 1
                else:
                    verdict = "➖ SAME"
            elif score_a is None:
                change = "NEW"
                verdict = "🆕 NEW PASS" if score_b and score_b >= 4 else "💀 NEW FAIL"
            elif score_b is None:
                change = "DEL"
                verdict = "💀 REMOVED"

            if only_regressed and "REGRESSED" not in verdict:
                continue
            if only_improved and "IMPROVED" not in verdict:
                continue

            question_text = ""
            if ra:
                question_text = ra.question[:36]
            elif rb:
                question_text = rb.question[:36]

            score_a_str = str(score_a) if score_a is not None else "—"
            score_b_str = str(score_b) if score_b is not None else "—"

            typer.echo("  │ {:>2} │ {:<36} │ {:>5} │ {:>5} │ {:>6} │ {:<10} │".format(
                idx + 1, question_text, score_a_str, score_b_str, change, verdict
            ))

        typer.echo("  └────┴──────────────────────────────────────┴───────┴───────┴────────┴────────────┘")
        typer.echo("")
        typer.echo("  LEGEND:  ✅ Improved   ❌ Regressed   🆕 New Pass   💀 New Fail   ➖ Unchanged")
        typer.echo("")

        if show is not None:
            idx = show
            ra = results_a_by_idx.get(idx)
            rb = results_b_by_idx.get(idx)

            if not ra and not rb:
                typer.echo(f"Question index {idx} not found in either run", err=True)
                raise typer.Exit(1)

            typer.echo("╭─ Question #{} ────────────────────────────────────────────────────────────╮".format(idx + 1))
            question_text = ra.question if ra else rb.question
            typer.echo(f"│ {question_text}")
            typer.echo("╰" + "─" * 76 + "╯")
            typer.echo("")

            if ra:
                typer.echo(f"  RUN #{run_a} (Score: {ra.score})")
                resp = ra.response[:200] + "..." if ra.response and len(ra.response) > 200 else ra.response
                typer.echo(f"  {resp}")
                if ra.flaw:
                    typer.echo(f"  ❌ Flaw: {ra.flaw}")
                typer.echo("")

            typer.echo("  " + "─" * 76)
            typer.echo("")

            if rb:
                typer.echo(f"  RUN #{run_b} (Score: {rb.score})")
                resp = rb.response[:200] + "..." if rb.response and len(rb.response) > 200 else rb.response
                typer.echo(f"  {resp}")
                if rb.flaw:
                    typer.echo(f"  ❌ Flaw: {rb.flaw}")
                typer.echo("")

        if regressed_count > 0:
            raise typer.Exit(1)

@dataset_app.command("create")
def dataset_create(
    csv: str = typer.Option(..., "--csv", "-c", help="Path to CSV file"),
    name: str = typer.Option(None, "--name", "-n", help="Dataset name (default: filename)"),
):
    """Register a CSV as a dataset (deduplicated by content hash)."""
    from pathlib import Path

    csv_path = Path(csv)
    if not csv_path.exists():
        typer.echo(f"Error: File not found: {csv}", err=True)
        raise typer.Exit(1)

    rows = load_dataset(str(csv_path))
    item_count = len(rows)
    file_hash = get_file_hash(str(csv_path))

    if name is None:
        name = csv_path.stem

    with Session(engine) as session:
        existing = session.exec(
            select(Datasets).where(Datasets.hash == file_hash)
        ).first()

        if existing:
            typer.echo(f"Dataset already exists (same content):")
            typer.echo(f"  ID: {existing.id}")
            typer.echo(f"  Name: {existing.name}")
            typer.echo(f"  Items: {existing.item_count}")
            typer.echo(f"  Hash: {existing.hash[:16]}...")
            typer.echo(f"  Created: {existing.createdAt}")
            return

        dataset = Datasets(
            name=name,
            source_path=str(csv_path),
            item_count=item_count,
            hash=file_hash
        )
        session.add(dataset)
        session.commit()
        session.refresh(dataset)

        typer.echo(f"Dataset created:")
        typer.echo(f"  ID: {dataset.id}")
        typer.echo(f"  Name: {dataset.name}")
        typer.echo(f"  Items: {dataset.item_count}")
        typer.echo(f"  Hash: {dataset.hash[:16]}...")
        typer.echo(f"  Created: {dataset.createdAt}")


@dataset_app.command("list")
def dataset_list():
    """List all registered datasets."""
    with Session(engine) as session:
        datasets = session.exec(
            select(Datasets).order_by(Datasets.createdAt.desc())
        ).all()

        if not datasets:
            typer.echo("No datasets found. Create one with: proof dataset create --csv file.csv")
            return

        typer.echo("")
        typer.echo("  DATASETS")
        typer.echo("  ┌────┬────────────────────────┬───────────┬────────────┬────────────────────────┐")
        typer.echo("  │ ID │ Name                   │ Items     │ Hash (8)   │ Created                │")
        typer.echo("  ├────┼────────────────────────┼───────────┼────────────┼────────────────────────┤")

        for d in datasets:
            hash_short = d.hash[:8] if d.hash else "—"
            created = d.createdAt.strftime("%Y-%m-%d %H:%M:%S") if d.createdAt else "—"
            typer.echo("  │ {:>2} │ {:<22} │ {:>9} │ {:<10} │ {:<22} │".format(
                d.id, d.name[:22], d.item_count, hash_short, created
            ))

        typer.echo("  └────┴────────────────────────┴───────────┴────────────┴────────────────────────┘")
        typer.echo("")


@dataset_app.command("show")
def dataset_show(
    dataset_id: int = typer.Argument(..., help="Dataset ID"),
    limit: int = typer.Option(10, "--limit", "-l", help="Number of questions to show"),
):
    """Show questions from a dataset."""
    with Session(engine) as session:
        dataset = session.get(Datasets, dataset_id)
        if not dataset:
            typer.echo(f"Error: Dataset #{dataset_id} not found", err=True)
            raise typer.Exit(1)

        rows = load_dataset(dataset.source_path)
        rows = rows[:limit]

        typer.echo("")
        typer.echo(f"  Dataset #{dataset.id}: {dataset.name} ({dataset.item_count} items)")
        typer.echo("  ┌────┬──────────────────────────────────────────────────────────────┐")
        typer.echo("  │ #  │ Question                                                     │")
        typer.echo("  ├────┼──────────────────────────────────────────────────────────────┤")

        for i, row in enumerate(rows):
            question = row.get("input", "")[:60]
            typer.echo("  │ {:>2} │ {:<60} │".format(i + 1, question))

        typer.echo("  └────┴──────────────────────────────────────────────────────────────┘")
        typer.echo("")

@app.command("list")
def run_list(
    dataset_id: int = typer.Option(None, "--dataset", "-d"),
    limit: int = typer.Option(20, "--limit", "-l"),
):
    with Session(engine) as session:
        query = select(Runs).order_by(Runs.created_at.desc())
        if dataset_id:
            query = query.where(Runs.dataset_id == dataset_id)
        runs = session.exec(query.limit(limit)).all()

        for r in runs:
            avg = f"{r.avg_score:.2f}" if r.avg_score else "—"
            typer.echo(f"  #{r.id}  dataset={r.dataset_id}  model={r.model}  avg={avg}  total={r.total}  {r.created_at}")


@app.command("show")
def run_show(run_id: int = typer.Argument(...), limit: int = typer.Option(10, "--limit", "-l")):
    with Session(engine) as session:
        run = session.get(Runs, run_id)
        if not run:
            typer.echo(f"Run #{run_id} not found", err=True)
            raise typer.Exit(1)

        results = session.exec(
            select(Results).where(Results.run_id == run_id).order_by(Results.idx).limit(limit)
        ).all()

        typer.echo(f"Run #{run.id}  avg={run.avg_score:.2f}/5  total={run.total}  model={run.model}")
        for res in results:
            score = str(res.score) if res.score else "—"
            typer.echo(f"  [{res.idx+1}] score={score}  q={res.question[:60]}")
@app.command()
def version():
    """Show the version."""
    typer.echo("proof 0.1.0")


if __name__ == "__main__":
    app()
