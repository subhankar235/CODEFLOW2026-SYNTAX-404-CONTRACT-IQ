from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional
import os


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=os.path.join(
            os.path.dirname(
                os.path.dirname(
                    os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
                )
            ),
            ".env",
        ),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Frontend
    next_public_api_url: str = "http://localhost:8000"
    next_public_clerk_publishable_key: Optional[str] = None
    clerk_secret_key: Optional[str] = None
    uploadthing_secret: Optional[str] = None
    uploadthing_app_id: Optional[str] = None

    # Backend API
    database_url: str = "postgresql+asyncpg://user:password@host/dbname"
    redis_url: str = "rediss://host:6379"
    clerk_webhook_secret: Optional[str] = None
    clerk_jwks_url: Optional[str] = None

    # AI Service
    openrouter_api_key: Optional[str] = None
    primary_model: str = "meta-llama/llama-3.3-70b-instruct:free"
    fast_model: str = "google/gemini-2.0-flash-exp:free"
    deepl_api_key: Optional[str] = None
    embedding_model: str = "all-MiniLM-L6-v2"

    # Shared
    ai_service_url: str = "http://localhost:8001"
    environment: str = "development"
    cors_origins: list = ["http://localhost:3000"]
    favorable_clauses_path: Optional[str] = "services/ai/app/data/favorable_clauses"
    precedents_path: Optional[str] = "services/ai/app/data/precedents"


settings = Settings()
