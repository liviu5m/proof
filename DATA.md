Here is a complete project blueprint. You can copy and paste this directly into a `README.md` file in your GitHub repository, or into a Notion/Linear document to guide your development.

***

# Proof — Build Plan

> **The Golden Rule: Make it work → Make it right → Make it fast.**
>
> You're currently at "make it work." Don't worry about speed, scale, or a
> beautiful UI until the core loop is solid.

Here is the exact order you should build **Proof**, designed so you have
something **working and visible after Day 1**.

> **The #1 rule: Do not touch the frontend until Phase 4.**

---

## 🎯 Phase 1: The Core Loop (Days 1-3) — BUILD THIS FIRST

**Goal:** A Python script in your terminal that runs 5 questions through an LLM,
judges them, and prints a score. **No UI. No database. No web app.**

### Day 1: The Runner

Create a file called `runner.py`:

```python
# Hardcode 5 test questions
questions = [
    "What is the capital of France?",
    "Explain quantum physics in 3 words",
    # ...
]

# Send each to an LLM (OpenAI, Claude, etc.)
# Save the answers to a list
```

✅ **Day 1 deliverable:** You can run `python runner.py` and see 5 AI answers
printed in your terminal.

### Day 2: The Judge

Create `judge.py`:

- Take each `(question, answer)` pair
- Send it to a "Judge" LLM (GPT-4o-mini is cheap) with a prompt like:
  > *"Rate this answer 1-5 for accuracy. Reply ONLY with a JSON: {\"score\": X, \"reason\": \"...\"}"*
- Parse the JSON response
- Calculate the average score

✅ **Day 2 deliverable:** Running the script now prints: `Score: 4.2/5` with
reasons for each.

### Day 3: Make it a CLI tool

Use Python's `Typer` or `Click` library:

```bash
proof run --questions test.csv --prompt "You are a helpful assistant"
```

✅ **Day 3 deliverable:** A real CLI tool you can run from your terminal.
**This is your MVP.**

---

## 📊 Phase 2: Persistence (Days 4-6)

**Goal:** Save your runs so you can compare them later.

- Set up a simple **SQLite** database (don't use Postgres yet, SQLite is easier)
- Create 3 tables: `Datasets`, `Runs`, `Results`
- Modify your CLI so every run saves to the database
- Add a command: `proof compare run_1 run_2` that prints the difference

✅ **Deliverable:** You can run multiple evals and compare them in the terminal.

---

## 🎨 Phase 3: The Web Dashboard (Days 7-14)

**Only start this AFTER Phase 1 & 2 work perfectly.**

- **Backend:** FastAPI with endpoints like `/runs`, `/datasets`, `/compare`
- **Frontend:** Next.js + Tailwind + Shadcn UI
- **Pages to build (in order):**
  1. Upload CSV page (dataset creation)
  2. Run evaluation page (select dataset + prompt)
  3. Results page (see all answers + scores)
  4. Compare page (side-by-side two runs)

✅ **Deliverable:** A beautiful web app you can show your friends.

---

## 🚀 Phase 4: The "Killer Features" (Weeks 3-4)

This is what makes Proof special:

1. **Concurrency:** Use `asyncio` + `arq` to run 100 evals in parallel instead of
   one by one
2. **Rule-based scorers:** Add regex, JSON schema validation, word count checks
3. **GitHub Action:** Create a `.github/workflows/proof.yml` so teams can run
   evals on every PR
4. **Quality thresholds:** Block deploys if score drops below X%

---

## 🛠️ Tech Stack (Keep it simple!)

| Layer | Choice | Why |
|---|---|---|
| Language | **Python** | Best LLM ecosystem |
| CLI | **Typer** | Dead simple |
| DB (start) | **SQLite** | Zero setup |
| DB (later) | **PostgreSQL** | For production |
| Backend | **FastAPI** | Fast, modern |
| Frontend | **Next.js + Shadcn** | Beautiful by default |
| LLM API | **OpenAI** | Start here, add others later |

---

## ⚠️ The 3 Traps to Avoid

1. **❌ Building the UI first.** You'll spend 2 weeks on buttons and have no
   working product.
2. **❌ Over-engineering the database.** SQLite is fine for months. Don't design
   a perfect schema upfront.
3. **❌ Supporting 10 LLM providers at once.** Start with OpenAI only. Add
   Claude/Anthropic in Week 3.

---

## 📅 Your Action Plan for TODAY

Do this in the next 2 hours:

1. Create a GitHub repo called `proof`
2. Create a virtual environment: `python -m venv venv`
3. Install: `pip install openai typer`
4. Write `runner.py` with 5 hardcoded questions
5. Run it and see 5 AI answers in your terminal

**That's it.** Once you see those 5 answers, you've started. The rest is just
iteration.

---

# 📎 Appendix: Original Product Blueprint

*The strategy document this build plan was derived from. Kept for reference —
see "Phase 1: MVP Milestones" at the bottom for the 4-week schedule.*

---

## 🛡️ Proof: Self-Hosted LLM Evaluation & Regression Testing

**Tagline:** *Jest for LLMs. Catch AI regressions before they reach production.*

## 📖 The Problem
When building AI applications, traditional unit tests (`assert output == expected`) don't work because LLM outputs are non-deterministic natural language. 
When a developer tweaks a prompt to make the AI "more friendly," it might accidentally start hallucinating or breaking JSON formatting. Without a testing framework, these **silent regressions** make it to production, breaking the app for real users.

## 💡 The Solution
**Proof** is a self-hosted, automated evaluation framework for LLM applications. It allows engineering teams to define datasets of test cases, run them against their AI app, automatically grade the results using rules or an "LLM-as-a-Judge", and block CI/CD deployments if the quality score drops.

---

## 🚀 Core Features

### 1. Dataset Management
* Upload test cases via CSV, JSON, or UI.
* Each test case contains: `Input` (the user prompt), `Context` (optional RAG context), and `Expected Behavior` (rules or reference answers).
* Version control for datasets so you can track how your test suite evolves.

### 2. The Evaluation Engine (The Core Loop)
* **The Runner:** Concurrently sends all dataset inputs to the target LLM app. Handles API rate-limiting and retries automatically.
* **The Scorers:** Automatically grades every single output.
  * *Rule-based:* Regex checks, JSON schema validation, word count limits, keyword inclusion.
  * *LLM-as-a-Judge:* Sends the `(Input + Output + Rules)` to a secondary "Judge" LLM (e.g., GPT-4o-mini) to score the output on a scale of 1-5 based on custom rubrics (e.g., "Is it polite?", "Did it hallucinate?").

### 3. The Comparison Dashboard
* Visual, side-by-side comparison of **Run A** (old prompt) vs **Run B** (new prompt).
* Highlights exactly which test cases improved, which degraded, and which stayed the same.
* Displays an overall aggregate quality score (e.g., "Run B improved overall score by 12%").

### 4. CI/CD Integration (The Killer Feature)
* A CLI tool (`proof run`) and GitHub Action.
* Developers can set a "Quality Threshold" (e.g., 90%). If a PR changes a prompt and the eval score drops below 90%, **the GitHub Action fails and blocks the merge.**

---

## 🏗️ How It Works (The User Flow)

1. **Define:** The developer creates a dataset of 100 tricky customer support queries.
2. **Configure:** They set up a Judge prompt: *"Score the AI's response from 1-5. Deduct points if it promises a refund or uses profanity."*
3. **Run:** The developer runs `proof run --dataset support.csv --prompt v2.txt`.
4. **Review:** The dashboard shows the new prompt scored 94/100. It highlights 3 specific cases where the AI accidentally promised a refund.
5. **Fix & Deploy:** The developer tweaks the prompt, runs it again (Score: 99/100), and merges the PR. The CI/CD pipeline passes.

---

## 🎯 Target Audience
* **AI/ML Engineers** building RAG pipelines or chatbots.
* **Startup Founders** who need to ensure their AI product doesn't embarrass them in front of customers.
* **Enterprise Teams** in healthcare, finance, or Europe (GDPR) who **cannot** send their proprietary test data to third-party SaaS eval tools like LangSmith or Braintrust. *(This is your main marketing angle: 100% Self-Hosted & Private).*

---

## 🛠️ Recommended Tech Stack (For a Solo Dev)

* **Backend:** Python (FastAPI). Python is mandatory here because the AI/LLM ecosystem (LangChain, OpenAI SDK, etc.) is native to it.
* **Background Jobs:** Redis + Celery (or Python's `asyncio` + `arq` for a lighter setup). *Crucial for running 1,000 evals concurrently without timing out.*
* **Database:** PostgreSQL. You need relational data to link `Datasets` -> `Test Cases` -> `Runs` -> `Results`.
* **Frontend:** Next.js (React) + Tailwind CSS + Shadcn UI. Keep the dashboard clean, fast, and developer-friendly.
* **CLI:** Python `Typer` or `Click` library to build the command-line interface.

---

## 🏆 Differentiation (Why Proof?)
* **vs LangSmith / Braintrust:** Proof is **self-hosted**. Your data never leaves your VPC. 
* **vs Promptfoo:** Promptfoo is powerful but heavily CLI-based and complex to configure. Proof focuses on a **beautiful, intuitive Web UI** and simpler setup for non-technical product managers to review results.

---

## 📅 Phase 1: MVP Milestones (First 4 Weeks)

- [ ] **Week 1:** Build the Backend API. Create DB schema (Datasets, Runs, Results). Build the basic LLM runner (send prompt, get response).
- [ ] **Week 2:** Build the "LLM-as-a-Judge" scorer. Ensure it reliably outputs JSON scores. Implement basic rule-based scorers (regex, length).
- [ ] **Week 3:** Build the Frontend Dashboard. Upload CSV, view raw results, see the overall score.
- [ ] **Week 4:** Build the CLI tool (`proof run`) and a basic GitHub Action YAML template. Write the `README.md` and launch on Hacker News / Reddit.

***

### 💡 Advice for starting:
Don't get distracted building a massive UI on day one. **Start with the CLI and the Python backend.** If you can run a script in your terminal that outputs `Score: 85/100` and tells you exactly which 15 questions failed, you have a working MVP. The pretty dashboard comes second!
