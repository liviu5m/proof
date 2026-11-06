# Proof — Production Roadmap & Upgrade Plan

**Target rating: 85+/100**  
**Current harsh rating (Phase 4 NOT yet built): ~44/100**  
**Gap to close: ~41 points via the phases below.**

This roadmap is the exact, ordered engineering plan to transform Proof from a prototype into an enterprise-grade, resume-worthy LLM evaluation framework. Every phase below has a **Definition of Done** and **Acceptance Criteria**. Do not start the next phase until the previous phase's Definition of Done is met.

> Rating model (100 pts): Core correctness 30 · Code quality & correctness 20 · Testing & reliability 15 · Security & ops 15 · Enterprise polish 10 · Multi-provider flexibility 5 · Documentation & DX 5.

---

## Phase 0: Foundation & Critical Bug Fixes
*Goal: Stop the bleeding. Make the codebase runnable, import-safe, and dependency-injection correct before adding features. Without this, later phases build on broken foundations.*

- [ ] **Fix `deps.get_llm_client` wiring**
  - `get_llm_client(settings)` requires an argument but is registered as `Depends(get_llm_client)` in `routes/runs.py` and `cli.py`. FastAPI cannot resolve it.
  - Refactor to `get_llm_client()` with no required args, reading `settings` from module-level or via `lru_cache`/dependency override.
  - Acceptance: `uvicorn src.main:app --reload` starts and `/api/runs/` dependency resolves without 500.

- [ ] **Fix `db.py` import-time failure**
  - `db.py` raises `ValueError("DATABASE_URL not set")` at import time and constructs the Supabase client with empty strings when env vars are absent. This breaks test collection and local dev without a live DB.
  - Make engine/Supabase client lazy (initialize on first use, not import). Validate config at app startup in `lifespan`, not at module import.
  - Acceptance: `import src.db` succeeds with no env vars; app fails fast with a clear message only when a DB-dependent endpoint is called without `DATABASE_URL`.

- [ ] **Unify password hashing**
  - `utils.py` uses `sha256_crypt`; `auth.py` uses `bcrypt`. Inconsistent and `sha256_crypt` is weak/deprecated.
  - Standardize on `bcrypt` (via `passlib`) everywhere. Add password complexity validation on register.
  - Acceptance: `hashPassword`/`verifyPassword` single source of truth; register+login round-trip works with bcrypt.

- [ ] **Remove dead / misleading code**
  - `_is_rate_limit()` in `runner.py` is defined but never used; the `tenacity` retry fires on *all* exceptions including hard failures (400, 401).
  - Split retry policy: retry only on 429/timeout/transient; fail fast on auth/validation errors.
  - Acceptance: `grep -rn "_is_rate_limit"` shows usage; retries do not mask 401/400 errors.

- [ ] **Fix error propagation between `run_tests` and `judge_questions`**
  - `run_tests` returns error dicts (`{"error": ...}`) that lack `"response"`/`"input"` keys; `judge_single` then `KeyError`s on `q["response"]` (masked by `return_exceptions=True`, but sloppy and loses debugging info).
  - Normalize shapes: every runner result carries `input`, `response` (or `null`), `error`; judge handles missing response gracefully (score 0, reason "no response").
  - Acceptance: A failed Gemini call produces a visible error result, not a swallowed exception.

- [ ] **Centralize configuration validation**
  - `config.py` uses `pydantic-settings` but required fields (`GEMINI_API_KEY`, `DATABASE_URL`, `SECRET_KEY`, etc.) crash at import if missing.
  - Add a `/healthz` and `/readyz` endpoint that reports which env vars/services are configured.
  - Acceptance: `GET /healthz` returns `{status, version, services: {db, llm, storage}}` without crashing.

**Definition of Done:** App imports and starts with minimal env; `/healthz` responds; login/register/bcrypt consistent; no unused or dead code; DI resolves correctly.

**Rating impact: +8 points** (brings baseline from ~44 to ~52).

## Phase 1: Test Suite & Quality Assurance (80%+ Coverage, Enforced)
*Goal: The roadmap's own goal is "80%+ test coverage." Reality is far below. Fix this with enforced gates.*

- [ ] **Backend test infrastructure**
  - Pin `pytest`, `pytest-asyncio`, `httpx`, `pytest-mock`, `respx`, `pytest-cov`.
  - Create `backend/tests/conftest.py` with FastAPI `TestClient` / `AsyncClient` fixtures and an in-memory SQLite override for `get_session`.
  - Add `pyproject.toml`/`pytest.ini` with `addopts = --cov=src --cov-report=term-missing --cov-fail-under=80`.

- [ ] **Unit tests for core logic**
  - `scorers.py`: `check_json`, `check_regex`, `check_word_count`, `check_keywords` — edge cases (empty string, unicode, invalid regex, boundary word counts).
  - `utils.py`: `sanitize_text`, `sanitize_prompt`, `createAccessToken`/`decodeToken`, `hashPassword`/`verifyPassword`, HTML-escaping, null-byte removal.
  - `validators.py`: `DatasetRow` validators (min/max words, regex compile, `requires_json` parsing), `validate_csv_headers`, `validate_csv_rows` with line numbers.

- [ ] **Unit tests for runner & judge**
  - `runner.py`: mock `client.aio.interactions.create`; test retry on 429, fail-fast on 400, timeout handling, word-count/keyword injection into prompt.
  - `judge.py`: mock judge LLM; test score parsing, JSON gate, word-count gate, regex gate, keyword gate, API error fallback (score 1.0).

- [ ] **API integration tests**
  - FastAPI `TestClient` for all routers: `/api/auth/*`, `/api/dataset/*`, `/api/runs/*`, `/api/user/*`.
  - Test unauthorized access (401), not-found (404), validation errors (422), success paths (200/201).
  - Override `get_current_user` and `get_llm_client` dependencies in tests.

- [ ] **CLI tests**
  - Typer `CliRunner` for `proof dataset create/list/show`, `proof run`, `proof compare`, `proof version`.
  - Test CSV not found, empty dataset, default user creation.

- [ ] **Frontend tests**
  - Vitest + React Testing Library for all dashboard pages and UI components.
  - Test `evaluate.page.tsx` run flow (mock API), `datasets`, `runs`, `compare`, `login`, `signup`.
  - Target: 80%+ frontend coverage enforced in CI.

- [ ] **Coverage gate in CI**
  - Fail the build if backend or frontend coverage drops below 80%.

**Definition of Done:** `pytest --cov` and `vitest --coverage` both report ≥80%; CI fails below threshold; every new PR must maintain or increase coverage.

**Rating impact: +12 points.**

## Phase 2: Backend Hardening & Error Handling
*Goal: Bulletproof resilience against bad data and API failures.*

- [ ] **Robust LLM error boundaries**
  - Wrap all Gemini (and future provider) calls in `try/except` with exponential backoff for 429/rate limits and timeouts only.
  - Return clear, structured JSON error responses from FastAPI: `{"error": ..., "code": ..., "status": ..., "request_id": ...}`.
  - Add correlation/`request_id` middleware to every request for distributed tracing.

- [ ] **Strict CSV & input validation (defense in depth)**
  - Keep Pydantic `DatasetRow` models; reject malformed datasets on upload with explicit line numbers and error messages.
  - Add file size limits, MIME-type checks, and virus-scan hook placeholder for storage uploads.
  - Validate `system_prompt` length and content (prompt-injection strip list in `sanitize_prompt`).

- [ ] **Dependency injection & config**
  - Remove global client instantiation. Use FastAPI `Depends` for DB sessions (`SessionDep`) and LLM clients (`get_llm_client`).
  - Manage all env vars via `pydantic-settings` (`config.py`); add `ENVIRONMENT` (dev/staging/prod), `LOG_LEVEL`, `MAX_CONCURRENT_RUNS`.
  - Add dependency overrides for testing.

- [ ] **Database reliability**
  - Add Alembic (or SQLModel-autogenerate) migrations; no more `create_all` only in production.
  - Add connection pool tuning, `pool_pre_ping`, and retry on DB connection failure.
  - Add soft-delete (`deleted_at`) on `Datasets`, `Runs`, `Results`.

- [ ] **Rate limiting & abuse protection**
  - Add Redis-backed rate limiter (or in-memory fallback) per user/IP on `/api/runs` and `/api/dataset`.
  - Limit concurrent runs per user (`MAX_CONCURRENT_RUNS`); queue excess with a `status="Queued"`.

**Definition of Done:** All external API calls have bounded retries and structured errors; DI is consistent; migrations exist; rate limiter returns 429 with `Retry-After`.

**Rating impact: +8 points.**

## Phase 3: Production Authentication & Security
*Goal: Real security model with authorization, not just authentication.*

- [ ] **Real authentication**
  - Keep Supabase Auth **or** standard JWT as primary; add refresh-token rotation.
  - Protect all FastAPI routes with `Depends(get_current_user)`; no unauthenticated write endpoints.
  - Add `/api/auth/refresh`, `/api/auth/password-reset`, `/api/auth/email-verification`.

- [ ] **Authorization (RBAC)**
  - Add `role` field to `Users` (`admin`, `member`, `viewer`).
  - Enforce resource ownership: users can only see/edit their own datasets/runs unless `admin`.
  - Add `Depends(require_role("admin"))` for admin routes.

- [ ] **Security hardening**
  - Enforce strict CORS (env-driven `ALLOWED_ORIGINS`, no `*` in prod).
  - Secure HTTP headers: HSTS, `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`, CSP.
  - Sanitize all user inputs before prompts/DB queries (keep `sanitize_text`/`sanitize_prompt`).
  - Add CSRF protection for state-changing cookie-based endpoints.
  - Add audit log table: `actor_user_id`, `action`, `resource_type`, `resource_id`, `timestamp`, `ip`.

- [ ] **Secrets management**
  - Never commit `.env`; use environment injection or a secret manager in prod.
  - Rotate `SECRET_KEY` and signing keys; add key-version support in JWT.

**Definition of Done:** Every mutating endpoint requires auth + ownership check; RBAC enforced; security headers present; audit log writes on all write actions; no secrets in git.

**Rating impact: +10 points.**

## Phase 4: Enterprise Features (Resume-Worthy Polish)
*Goal: Stand out to elite engineering teams. These are differentiators, not table stakes.  
**Note: Not built yet.** This is future work to add on top of Phases 0–3.*

- [ ] **CI/CD Pipeline**
  - Add `.github/workflows/ci.yml`: lint (`ruff`/`black`/`isort`), type-check (`mypy`/`pyright`), backend tests, frontend tests, frontend build (`next build`), security scan (`bandit`/`snyk`).
  - Add `.github/workflows/cd.yml`: build/push Docker images, deploy to staging on `main`, production on release tag.

- [ ] **Advanced scorers**
  - Implement a **semantic similarity scorer** using embedding models (e.g., `text-embedding-004` / local `sentence-transformers`) alongside exact match, regex, and LLM-as-a-Judge.
  - Composite score: weighted blend of rule-based + LLM-judge + semantic similarity.
  - Allow per-dataset scorer configuration (weights toggled in UI).

- [ ] **Observability & cost tracking**
  - Track input/output tokens and estimate dollar cost per run per model.
  - Store token metrics in DB (`token_usage` table: `run_id`, `model`, `prompt_tokens`, `completion_tokens`, `cost_usd`, `created_at`).
  - Display cost and token counts on the Next.js dashboard (per run and per dataset trend).

- [ ] **Prompt versioning**
  - Link prompt strings to immutable version IDs (content-addressed hash).
  - Store `prompt_version_id` on `Runs`; regression comparisons show side-by-side prompt versions.
  - UI: prompt registry with create/edit (creates new version, never mutate), compare two versions, rollback.

- [ ] **Run comparison & regression alerts**
  - `compare` endpoint returns diff matrix across runs (score delta, response diff, cost delta).
  - Optional regression alert: if avg score drops > threshold vs baseline run, flag in UI and webhook.

- [ ] **Export & reporting**
  - Export run results to CSV/JSON/PDF; schedule email/Slack report hook.

**Definition of Done:** Semantic scorer wired; cost displayed per run; prompt versions immutable and comparable; CI/CD green on every PR.

**Rating impact: +10 points.**

## Phase 5: Multi-Provider LLM Abstraction & Model Flexibility
*Goal: Remove single-vendor lock-in. Critical for an "enterprise-grade" framework.*

- [ ] **LLM provider interface**
  - Define abstract base class `LLMProvider` with `generate(prompt, model, config) -> Response` and `count_tokens(text) -> int`.
  - Implement providers: **Google GenAI**, **OpenAI**, **Anthropic**, **Ollama** (local/self-hosted).
  - Provider selected per run (`provider` field on `Runs`), not hardcoded.

- [ ] **Unified config per provider**
  - `LLMProviderConfig`: API key, base URL, timeout, max retries, default models.
  - Provider credentials stored encrypted at rest; referenced by `provider_id`, not inline keys.

- [ ] **Model catalog**
  - Admin-curated model list with capabilities (supports JSON mode, supports system prompt, max tokens, cost per 1k tokens).
  - Frontend model dropdown populated from catalog, not hardcoded.

- [ ] **Fallback & routing**
  - Optional fallback chain: if primary provider fails, route to secondary (configurable).
  - Load-balance across multiple API keys for the same provider.

**Definition of Done:** A run can be executed against OpenAI, Anthropic, or Ollama with zero backend code changes; provider is a request parameter.

**Rating impact: +8 points** (this alone separates a toy from a platform).

## Phase 6: Observability, Cost Tracking & Production Ops
*Goal: Run it in production with confidence.*

- [ ] **Distributed tracing & logging**
  - Add OpenTelemetry tracing (or structlog + request_id) across HTTP handler → runner → judge → DB.
  - Structured JSON logs; correlate logs by `run_id` and `request_id`.
  - Export traces to a backend (Jaeger/OTLP) in staging/prod.

- [ ] **Metrics & alerting**
  - Prometheus metrics: `runs_total`, `runs_failed`, `avg_score`, `tokens_consumed`, `cost_usd`, `llm_latency_seconds`, `http_request_duration`.
  - Alert rules: error rate > 5%, avg score drop > 0.5, cost spike > 20% day-over-day.

- [ ] **Health checks**
  - `/healthz` (liveness), `/readyz` (readiness: DB reachable, storage reachable, LLM provider reachable).
  - Kubernetes probes wired in deployment manifests.

- [ ] **Caching**
  - Cache LLM responses for identical `(prompt, input, model, provider)` tuples (semantic or exact hash) to reduce cost and latency.
  - Cache dataset metadata; invalidate on upload/delete.

- [ ] **Backup & recovery**
  - Daily automated DB backups; point-in-time recovery documentation.
  - Storage bucket versioning for dataset CSVs.

- [ ] **Deployment manifests**
  - Dockerfiles (multi-stage, non-root user), `docker-compose.yml` for local dev, Kubernetes/Helm or Vercel configs for prod.
  - Environment variable reference doc (all required/optional vars).

**Definition of Done:** Traces correlate end-to-end; metrics dashboard exists; health probes pass; backup/restore tested; deployable via `docker-compose up` and a prod manifest.

**Rating impact: +10 points.**

## Phase 7: Frontend Polish & Real API Integration
*Goal: No more mock data; the dashboard hits the real API end-to-end.*

- [ ] **Remove `mock-data.ts`**
  - `mockDatasets`/`mockRuns` must be deleted; all dashboard data comes from `/api/dataset` and `/api/runs`.
  - Add empty/loading/error states everywhere (currently missing in several pages).

- [ ] **Full API client layer**
  - `frontend/src/api/` with typed functions for every backend endpoint (datasets, runs, users, auth, compare, export).
  - Request/response types in `frontend/src/types/` matching backend Pydantic/SQLModel schemas.
  - React Query (`@tanstack/react-query`) with cache invalidation, retry, and optimistic updates.

- [ ] **Real-time run status**
  - Polling or WebSocket/SSE for run status (`Pending` → `Running` → `Completed`/`Failed`).
  - Progress bar: `completed_items / total_items`.

- [ ] **Dashboard views**
  - Datasets: upload CSV, preview rows, search, delete, download.
  - Runs: list with pagination/filter/sort, view detail with per-item scores, reasons, responses.
  - Compare: side-by-side two runs, score delta, response diff.
  - Evaluate: select dataset, model, provider, prompt version; start run; view live progress.
  - Prompt registry: create/edit/compare/rollback prompt versions.
  - Cost/tokens: per-run and trend charts.

- [ ] **Authentication UI**
  - Login/signup with real JWT cookie handling; protected routes redirect to login.
  - Profile/settings: change password, API key management.

- [ ] **Accessibility & responsive**
  - Keyboard navigation, ARIA labels, color contrast, mobile-responsive layout.
  - Dark theme (already themed) polished.

**Definition of Done:** Zero references to `mockDatasets`/`mockRuns`; full CRUD works end-to-end against the real backend; run status updates in real time; mobile-friendly.

**Rating impact: +8 points.**

## Phase 8: CI/CD, Deployment & Developer Experience
*Goal: Ship fast, safely, and consistently.*

- [ ] **Local developer experience**
  - `Makefile` or `justfile`: `make dev`, `make test`, `make lint`, `make typecheck`, `make docker-build`.
  - `.env.example` files for backend and frontend with every required variable documented.
  - `docker-compose.yml` spins up backend, frontend, Postgres, Redis (one command).

- [ ] **CI pipeline (GitHub Actions)**
  - On every PR: lint, type-check, backend tests (coverage gate ≥80%), frontend tests (coverage gate ≥80%), `next build`, `npm run build` (if applicable), secret scan.
  - PR must pass all checks before merge; branch protection on `main`.

- [ ] **CD pipeline**
  - Staging deploy on merge to `main`; production deploy on git tag.
  - Blue/green or rolling deploy with health-check gate; rollback on failure.

- [ ] **API documentation**
  - FastAPI auto OpenAPI at `/docs` and `/redoc`; customize with tags, descriptions, examples.
  - Frontend consumes OpenAPI types or hand-maintained TS types kept in sync.

**Definition of Done:** `make dev` works for a new clone in < 5 minutes; every PR runs full test+lint+build; deploys are automated and rollbackable.

**Rating impact: +5 points.**

## Phase 9: Documentation, Performance & Scale
*Goal: Production-grade docs and the ability to scale beyond a single user.*

- [ ] **Documentation**
  - `docs/`: architecture overview, API reference, quickstart (CLI + web), dataset CSV format guide, auth guide, provider setup guide, contribution guide, security policy.
  - `ARCHITECTURE.md`, `DECISIONS/` (ADRs for major choices: provider abstraction, JWT vs sessions, etc.).
  - README updated with badges (coverage, build status, license).

- [ ] **Performance**
  - Pagination (`limit`/`offset` or cursor) on all list endpoints (`/api/runs`, `/api/dataset`, results).
  - Async throughout (no blocking calls in FastAPI route handlers).
  - DB indexes on `user_id`, `dataset_id`, `run_id`, `created_at`.
  - Load-test: 50 concurrent runs without errors; response p95 < 2s for API (excluding LLM latency).

- [ ] **Scale**
  - Background job queue (Celery/RQ/Arq) for runs so API doesn't block on LLM calls.
  - Worker scales independently from API.
  - Object storage abstraction (Supabase Storage or S3-compatible) for dataset CSVs and exports.

- [ ] **Final hardening**
  - Pen-test checklist: SQL injection (parameterized queries everywhere — verify), XSS (output escaping), IDOR (ownership checks — verify), auth bypass.
  - Final coverage re-check ≥80% both backend and frontend.

**Definition of Done:** Docs complete; paginated endpoints; background workers; p95 < 2s API; final security self-audit passed.

**Rating impact: +7 points** (brings total to ~85+).

---

## Rating Checklist — How to Reach 85+/100

| Area | Target | Phase |
|---|---|---|
| Core correctness | 25–30 / 30 | 0, 2, 7 |
| Code quality & correctness | 18–20 / 20 | 0, 2, 3 |
| Testing & reliability | 13–15 / 15 | 1, 8 |
| Security & ops | 13–15 / 15 | 3, 6, 9 |
| Enterprise polish | 8–10 / 10 | 4 |
| Multi-provider flexibility | 4–5 / 5 | 5 |
| Documentation & DX | 4–5 / 5 | 8, 9 |
| **Total** | **85–100 / 100** | |

**Order of execution:** Phase 0 → 1 → 2 → 3 → 5 → 4 → 6 → 7 → 8 → 9.  
Do not skip Phase 0; the DI and import bugs will break every phase that follows.

**Merge rule:** No feature branch merges to `main` without passing CI, coverage gate, and at least one approval.
