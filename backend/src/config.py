from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    GEMINI_API_KEY: str
    DATABASE_URL: str
    SECRET_KEY: str
    SUPABASE_URL: str | None = None
    SUPABASE_SERVICE_ROLE_KEY: str | None = None
    GOOGLE_CLIENT_ID: str | None = None
    GOOGLE_CLIENT_SECRET: str | None = None
    FRONTEND_URL: str | None = None
    REDIRECT_URI: str | None = None
    RESEND_API_KEY: str | None = None
    BREVO_API_KEY: str | None = None
    FROM_EMAIL: str | None = None
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"
    MAX_CONCURRENT_RUNS: int = 5
    REDIS_URL: str = "redis://localhost:6379/0"
    RATE_LIMIT_RUNS_PER_MIN: int = 30
    RATE_LIMIT_DATASETS_PER_MIN: int = 30
    OPENAI_API_KEY: str | None = None
    ANTHROPIC_API_KEY: str | None = None
    OLLAMA_BASE_URL: str | None = "http://localhost:11434"
    ENCRYPTION_KEY: str | None = None

    class Config:
        env_file = ".env"
        extra = "allow"


settings = Settings()
