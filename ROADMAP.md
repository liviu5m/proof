# Proof — Project Roadmap

> **The Golden Rule: Make it work → Make it right → Make it fast.**
>
> You're currently at "make it work." Don't worry about speed, scale, or a beautiful UI until the core loop is solid.

---

## 📊 Current Project State Analysis

### ✅ **What's Working (Phase 1 - Core Loop ~80% complete)**

| Component | Status |
|-----------|--------|
| CLI (`proof run`) | ✅ Working - loads CSV, runs through Gemini, judges responses |
| LLM Runner | ✅ Uses Google GenAI (Gemini 3.5 Flash Lite) |
| LLM Judge | ✅ Structured JSON output with rubric scoring (1-5) |
| Database Models | ✅ Defined: `Datasets`, `Runs`, `Results` (SQLModel) |
| Database Connection | ✅ PostgreSQL (Supabase) connected, tables created |
| FastAPI App | ✅ Basic setup with CORS, lifespan for DB init |

### ❌ **What's Missing (Phase 2 - Persistence)**

1. **No data persistence** - CLI runs but doesn't save to database
2. **No `proof compare` command** - Can't compare runs
3. **No dataset management** - No `proof dataset create/list` commands
4. **No run history** - Can't view past runs

### ❌ **What's Missing (Phase 3 - Web Dashboard)**

1. **No API endpoints** - FastAPI only has `/` root endpoint
2. **Frontend is empty** - No Next.js project initialized

### ❌ **What's Missing (Phase 4 - Killer Features)**

- Concurrency (asyncio/arq)
- Rule-based scorers (regex, JSON schema, word count)
- GitHub Action template
- Quality thresholds
---

## 🎯 Recommended Next Steps (Priority Order)

### **Week 1: Complete Phase 2 - Persistence (2-3 days)**

| Task | Description |
|------|-------------|
| **1. Save runs to DB** | Modify `cli.py` `run` command to create `Datasets`, `Runs`, `Results` records |
| **2. Add dataset commands** | `proof dataset create --name --csv`, `proof dataset list` |
| **3. Add run history** | `proof run list`, `proof run show <id>` |
| **4. Add compare command** | `proof compare <run_id_1> <run_id_2>` - side-by-side diff |
| **5. Add hash deduplication** | Use `hash` field in `Datasets` to avoid re-uploading same CSV |

### **Week 2: Phase 3 Backend - API Endpoints (3-4 days)**

| Endpoint | Purpose |
|----------|---------|
| `POST /api/datasets` | Upload CSV, create dataset |
| `GET /api/datasets` | List all datasets |
| `GET /api/datasets/{id}` | Get dataset details |
| `POST /api/runs` | Start new evaluation run |
| `GET /api/runs` | List runs (with filters) |
| `GET /api/runs/{id}` | Get run results with scores |
| `GET /api/compare?run_a=1&run_b=2` | Comparison data for frontend |