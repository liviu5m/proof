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
        idx = 0
        Results(run_id=run.id, idx=idx, question=q["input"], expected=q["expected"], response=response, score=score, flaw=flaw, reason=reason)
        idx += 1




@app.command()
def version():
    """Show the version."""
    typer.echo("proof 0.1.0")


if __name__ == "__main__":
    app()
