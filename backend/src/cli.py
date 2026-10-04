import csv
import typer

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
    rows = load_dataset(questions)
    typer.echo(f"Loaded {len(rows)} test cases from {questions}")
    data = run_tests(rows , prompt, model)
    scores = judge_questions(data, judge_modal)

    if scores:
        avg = sum(scores) / len(scores)
        typer.echo(f"\nScore: {avg:.1f}/5")


@app.command()
def version():
    """Show the version."""
    typer.echo("proof 0.1.0")


if __name__ == "__main__":
    app()
