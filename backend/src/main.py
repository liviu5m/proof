from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from contextlib import asynccontextmanager
from src.db import init_db
from src.models import Datasets
from src.routes.auth import router as authRouter
from src.routes.user import router as userRouter
from src.routes.datasets import router as datasetsRouter
from src.routes.runs import router as runsRouter

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global exception handlers - structured JSON errors
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    detail = exc.detail
    if isinstance(detail, dict):
        error = detail.get("error", str(detail))
        code = detail.get("code", "http_error")
    else:
        error = str(detail)
        code = "http_error"
    return JSONResponse(
        {"error": error, "code": code, "status": exc.status_code},
        status_code=exc.status_code,
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        {"error": "Validation error", "code": "validation_error", "detail": exc.errors()},
        status_code=422,
    )

@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        {"error": "Internal server error", "code": "internal_error", "detail": str(exc)},
        status_code=500,
    )

app.include_router(authRouter)
app.include_router(userRouter)
app.include_router(datasetsRouter)
app.include_router(runsRouter)

@app.get("/")
def root():
    return "Hello World"
