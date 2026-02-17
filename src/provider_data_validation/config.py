from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # Frontend
    FRONTEND_URL: str = "http://localhost:5173"

    # Ollama
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3.1:latest"
    ENABLE_LLM: bool = True

    # Demo / Twilio
    DEMO_MODE: bool = True
    TWILIO_AUTH_TOKEN: Optional[str] = None

    # Redis for persistence (optional)
    REDIS_URL: Optional[str] = None
    # Database (Postgres) fallback
    DATABASE_URL: Optional[str] = None

    # Celery
    CELERY_ENABLED: bool = False

    # CORS
    CORS_ORIGINS: Optional[str] = None  # comma-separated list

    class Config:
        env_file = ".env"


settings = Settings()
