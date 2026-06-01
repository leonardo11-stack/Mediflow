from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    GEMINI_API_KEY: str
    DATABASE_URL: str

    GEMINI_MODEL: str = "gemini-2.5-flash-lite"
    CORS_ORIGINS: list[str] = ["*"]

    N8N_WEBHOOK_URL: str = (
        "http://localhost:5678/webhook/baba29d5-4eb6-434a-9109-fd210973555d"
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
# (Apenas informativo: a URL da variável N8N_WEBHOOK_URL já está igual à solicitada.)