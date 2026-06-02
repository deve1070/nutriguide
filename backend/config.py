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
    database_url: str = "postgresql://postgres:postgres@localhost:5432/nutriguide"

    # ── JWT ──────────────────────────────────────────
    jwt_secret_key: str = "change-me-too"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 30  # access token — short lived
    jwt_refresh_expire_days: int = 30  # refresh token — long lived

    # ── OAuth — Google ────────────────────────────────
    google_client_id: str = ""
    google_client_secret: str = ""
    google_redirect_uri: str = "http://localhost:8002/auth/google/callback"

    # ── OAuth — Facebook ─────────────────────────────
    facebook_client_id: str = ""
    facebook_client_secret: str = ""
    facebook_redirect_uri: str = "http://localhost:8002/auth/facebook/callback"

    # ── Frontend URL ─────────────────────────────────
    frontend_url: str = "http://localhost:5173"

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
