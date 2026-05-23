from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file="../../.env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str = "postgresql+asyncpg://user:pass@localhost:5432/contractiq"
    redis_url: str = "redis://localhost:6379"
    clerk_webhook_secret: str = ""
    ai_service_url: str = "http://localhost:8001"
    environment: str = "development"


settings = Settings()
