from typing import Optional

from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    GEMINI_API_KEY: str
    DATABASE_URL: str
    SECRET_KEY: str
    SUPABASE_URL: Optional[str] = None
    SUPABASE_SERVICE_ROLE_KEY: Optional[str] = None
    GOOGLE_CLIENT_ID: Optional[str] = None
    GOOGLE_CLIENT_SECRET: Optional[str] = None
    FRONTEND_URL: Optional[str] = None
    REDIRECT_URI: Optional[str] = None
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"
    MAX_CONCURRENT_RUNS: int = 5

    class Config:
        env_file = ".env"
        extra = "allow"

settings = Settings()
