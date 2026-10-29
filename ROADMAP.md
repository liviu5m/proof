# Proof — Production Roadmap & Upgrade Plan

This roadmap outlines the exact engineering steps required to transform **Proof** from a prototype into an enterprise-grade, resume-worthy LLM evaluation framework (Target: 85+/100).

---

## Phase 1: Test Suite & Quality Assurance
*Goal: 80%+ test coverage, reliable offline execution.*

- [ ] **Backend Test Setup**
  - Install `pytest`, `pytest-asyncio`, `httpx`.
  - Create `backend/tests/` directory.
- [ ] **Unit Tests for Core Logic**
  - Test all functions in `scorers.py` (json, regex, word count, keywords).
  - Test `runner.py` and `judge.py` using `pytest-mock` or `respx` to mock Gemini API responses.
- [ ] **API Integration Tests**
  - Test FastAPI endpoints (`/runs`, `/datasets`, `/auth`) using TestClient / AsyncClient.
- [ ] **Frontend Tests**
  - Add Vitest + React Testing Library for Next.js components.

---

## Phase 2: Backend Hardening & Error Handling
*Goal: Bulletproof resilience against bad data and API failures.*

- [ ] **Robust Error Boundaries**
  - Wrap all Gemini API interactions in `try/except` with exponential backoff for rate limits (`429`) and timeouts.
  - Return clear, structured JSON error responses from FastAPI.
- [ ] **Strict CSV & Input Validation**
  - Replace loose string parsing with Pydantic models for CSV row validation.
  - Reject malformed datasets on upload with explicit line numbers and error messages.
- [ ] **Dependency Injection & Config**
  - Remove global client instantiation. Use FastAPI dependency injection for DB sessions and LLM clients.
  - Manage environment variables using `pydantic-settings`.

---

## Phase 3: Production Authentication & Security
*Goal: Real security model.*

- [ ] **Real Authentication**
  - Replace mocked auth with Supabase Auth or standard JWT token authentication.
  - Protect FastAPI routes with `Depends(get_current_user)`.
- [ ] **Security Hardening**
  - Enforce CORS policies and secure HTTP headers.
  - Sanitize all user inputs before passing to prompts or database queries.

---

## Phase 4: Enterprise Features (Resume-Worthy Polish)
*Goal: Stand out to elite engineering teams.*

- [ ] **CI/CD Pipeline**
  - Add a GitHub Actions workflow (`.github/workflows/ci.yml`) to run backend and frontend tests automatically on PR.
- [ ] **Advanced Scorers**
  - Implement a semantic similarity scorer using embedding models alongside exact match and LLM-as-a-Judge.
- [ ] **Observability & Cost Tracking**
  - Track token consumption (input/output tokens) and estimate dollar cost per run.
  - Store token metrics in the database and display them on the Next.js dashboard.
- [ ] **Prompt Versioning**
  - Link prompt strings to immutable version IDs so regression comparisons are crystal clear across deployments.
