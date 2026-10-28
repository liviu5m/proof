# Proof — Self-Hosted LLM Evaluation & Regression Testing

> *Jest for LLMs. Catch AI regressions before they reach production.*

Proof is a self-hosted, automated evaluation framework for LLM applications. It allows engineering teams to define datasets of test cases, run them against LLM models, grade results using rules and LLM-as-a-Judge, track run history, and compare prompt regressions.

---

## 🏗️ Architecture & Tech Stack

- **Backend / CLI:** Python 3.11+, FastAPI, SQLModel, Typer, Google GenAI (`gemini-3.5-flash-lite`, `gemini-3.1-flash-lite`)
- **Database:** PostgreSQL (Supabase) via SQLModel
- **Frontend:** Next.js (App Router), Tailwind CSS, Shadcn UI components

---

## 📁 Project Structure

```text
proof/
├── backend/
│   ├── pyproject.toml
│   └── src/
│       ├── cli.py         # Typer CLI commands (dataset, run, compare)
│       ├── main.py        # FastAPI application & startup
│       ├── models.py      # SQLModel database schemas (Datasets, Runs, Results)
│       ├── runner.py      # LLM test execution engine
│       ├── judge.py       # LLM-as-a-Judge evaluation logic
│       ├── scorers.py     # Rule-based and automated scorers
│       ├── db.py          # Database engine connection
│       └── routes/        # FastAPI REST endpoints (runs, datasets, auth, user)
└── frontend/
    ├── package.json
    └── src/
        ├── app/           # Next.js app router (dashboard, evaluate, compare, auth)
        ├── components/    # Shadcn UI components & layout elements
        └── api/           # API client integrations
```

---

## 🚀 Getting Started

### 1. Environment Setup

Create `.env` files in both `backend/` and `frontend/` containing your database connection string and API keys (e.g., `GEMINI_API_KEY`, `DATABASE_URL`).

### 2. Backend & CLI Installation

Navigate to `backend` and install dependencies:

```bash
cd backend
pip install -e .
```

This registers the `proof` CLI command.

### 3. Running the CLI

#### Create a Dataset
```bash
proof dataset create --csv src/test.csv --name "Core Benchmark"
```

#### List Datasets
```bash
proof dataset list
```

#### Run Evaluations
```bash
proof run --questions src/test.csv --prompt "You are a precise assistant."
```

#### Compare Runs
```bash
proof compare <run_id_1> <run_id_2>
```

---

## 📊 Dataset CSV Format

To evaluate your model with expected outputs and validation rules, structure your dataset CSV with the following columns:

```csv
input,expected,regex,min_words,max_words,required_keywords,forbidden_keywords,requires_json
"What is the capital of France?","Paris","Paris",1,10,"Paris","London",false
"How many seconds are in 3.5 hours?","12600","\\d+",1,5,"12600","error",false
```

### Column Descriptions
- `input`: Prompt or question sent to the LLM.
- `expected`: Target expected answer.
- `regex`: (Optional) Regular expression pattern response must match.
- `min_words`: (Optional) Minimum word count required.
- `max_words`: (Optional) Maximum word count allowed.
- `required_keywords`: (Optional) Comma-separated required words.
- `forbidden_keywords`: (Optional) Comma-separated forbidden words.
- `requires_json`: (Optional) Boolean indicating valid JSON requirement.

---

## 🌐 Web Dashboard

Start the FastAPI backend:
```bash
uvicorn src.main:app --reload
```

Start the Next.js frontend:
```bash
cd frontend
npm install
npm run dev
```
