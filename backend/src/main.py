import uuid
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from contextlib import asynccontextmanager
from src.db import init_db, check_db_connection
from src.models import Datasets
from src.routes.auth import router as authRouter
from src.routes.user import router as userRouter
from src.routes.datasets import router as datasetsRouter
from src.routes.runs import router as runsRouter
import os
from src.config import settings

load_dotenv()
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def validate_config():
    """Fail fast if required config is missing."""
    if not settings.GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY is required")
    if not settings.DATABASE_URL:
        raise RuntimeError("DATABASE_URL is required")
    if not settings.SECRET_KEY:
        raise RuntimeError("SECRET_KEY is required")
    if not check_db_connection():
        raise RuntimeError("Cannot connect to database. Check DATABASE_URL.")

@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "connect-src 'self' " + FRONTEND_URL + "; "
        "script-src 'self'; "
        "style-src 'self'; "
        "img-src 'self' data:;"
    )
    return response

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    detail = exc.detail
    if isinstance(detail, dict):
        error = detail.get("error", str(detail))
        code = detail.get("code", "http_error")
    else:
        error = str(detail)
        code = "http_error"
    request_id = getattr(request.state, "request_id", "unknown")
    return JSONResponse(
        {"error": error, "code": code, "status": exc.status_code, "request_id": request_id},
        status_code=exc.status_code,
        headers=getattr(exc, "headers", None)
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):

    request_id = getattr(request.state, "request_id", "unknown")
    return JSONResponse(
        {"error": "Validation error", "code": "validation_error", "detail": exc.errors(), "request_id": request_id},
        status_code=422,
    )

@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):

    request_id = getattr(request.state, "request_id", "unknown")
    return JSONResponse(
        {"error": "Internal server error", "code": "internal_error", "detail": str(exc), "request_id": request_id},
        status_code=500,
    )

app.include_router(authRouter)
app.include_router(userRouter)
app.include_router(datasetsRouter)
app.include_router(runsRouter)

@app.get("/")
def root():
    return "Hello World"

@app.get("/healthz")
def healthz():
    return {
        "status": "ok",
        "version": "0.1.0",
        "services": {
            "db": bool(settings.DATABASE_URL),
            "llm": bool(settings.GEMINI_API_KEY),
            "storage": bool(settings.SUPABASE_URL and settings.SUPABASE_SERVICE_ROLE_KEY),
        },
    }

@app.get("/readyz")
def readyz():
    return {
        "status": "ready",
        "version": "0.1.0",
        "services": {
            "db": bool(settings.DATABASE_URL),
            "llm": bool(settings.GEMINI_API_KEY),
            "storage": bool(settings.SUPABASE_URL and settings.SUPABASE_SERVICE_ROLE_KEY),
        },
    }
