from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── App ──────────────────────────────────────────
    app_name: str = "NutriGuide"
    app_env: str = "development"
    debug: bool = True
    secret_key: str = "change-me-in-production"

    # ── Database ─────────────────────────────────────
    database_url: str = "postgresql://postgres:nutride123@localhost:5432/nutriguide"

    # ── JWT ──────────────────────────────────────────
    jwt_secret_key: str = "change-me-too"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 10080  # 7 days

    # ── Groq LLM ─────────────────────────────────────
    groq_api_key: str = ""
    groq_model_id: str = "llama-3.1-70b-versatile"

    # ── CORS ─────────────────────────────────────────
    cors_origins: str = "http://localhost:3000,http://localhost:5173"

    # ── ChromaDB ─────────────────────────────────────
    chroma_persist_path: str = "./chroma_db"

    @property
    def allowed_origins(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",")]

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"


@lru_cache
def get_settings() -> Settings:
    """Cached settings instance — call this everywhere instead of Settings()"""
    return Settings()
