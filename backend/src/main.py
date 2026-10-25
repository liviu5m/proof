from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI
from contextlib import asynccontextmanager
from db import init_db
from models import Datasets
from routes.auth import router as authRouter
from routes.user import router as userRouter 
from routes.datasets import router as datasetsRouter
from routes.runs import router as runsRouter

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

app.include_router(authRouter)
app.include_router(userRouter)
app.include_router(datasetsRouter)
app.include_router(runsRouter)

@app.get("/")
def root():
    return "Hello World"
