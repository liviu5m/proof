import os
from sqlmodel import create_engine, SQLModel, Session, text
from dotenv import load_dotenv
from typing import Annotated
from fastapi import Depends, FastAPI
from supabase import create_client, Client

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "") 

supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
if not DATABASE_URL:
    raise ValueError("DATABASE_URL not set")

engine = create_engine(
    DATABASE_URL,
    echo=True,
    connect_args={
        "connect_timeout": 5,  
        "options": "-c search_path=proof",
    },
    pool_size=5,
    max_overflow=10,
)


def init_db():
    SQLModel.metadata.create_all(engine)
    print("✅ Database tables created successfully!")
    from sqlalchemy import inspect
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    print(f"📊 Tables created: {tables}")


def get_session():
    with Session(engine) as session:
        yield session


SessionDep = Annotated[Session, Depends(get_session)]
