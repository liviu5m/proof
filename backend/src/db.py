import os
from sqlmodel import create_engine, SQLModel, Session, text
from dotenv import load_dotenv
from typing import Annotated, Optional
from fastapi import Depends
from supabase import create_client, Client
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from sqlalchemy.exc import OperationalError

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "") 

_engine = None
_supabase: Optional[Client] = None

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    retry=retry_if_exception_type(OperationalError),
    reraise=True,
)
def _get_engine():
    global _engine
    if _engine is None:
        if not DATABASE_URL:
            raise ValueError("DATABASE_URL not set")
        
        engine_kwargs = {
            "echo": True,
            "pool_pre_ping": True
        }
        
        if DATABASE_URL.startswith("sqlite"):
            engine_kwargs["connect_args"] = {}
        else:
            engine_kwargs["connect_args"] = {
                "connect_timeout": 5,
                "options": "-c search_path=proof",
            }
            engine_kwargs["pool_size"] = 5
            engine_kwargs["max_overflow"] = 10
        
        _engine = create_engine(DATABASE_URL, **engine_kwargs)
    return _engine

def _get_supabase() -> Client:
    global _supabase
    if _supabase is None:
        _supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
    return _supabase


class _Lazy:
    def __init__(self, getter):
        self._getter = getter
    def __getattr__(self, name):
        return getattr(self._getter(), name)


engine = _Lazy(_get_engine)
supabase = _Lazy(_get_supabase)

def init_db():
    eng = _get_engine()
    SQLModel.metadata.create_all(eng)
    print("✅ Database tables created successfully!")

def check_db_connection() -> bool:
    try:
        with Session(_get_engine()) as session:
            session.exec(text("SELECT 1"))
        return True
    except Exception:
        return False

def get_session():
    with Session(_get_engine()) as session:
        yield session


SessionDep = Annotated[Session, Depends(get_session)]
