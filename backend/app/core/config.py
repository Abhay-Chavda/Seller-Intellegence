from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    database_url: str = "sqlite:///./dev.db"
    jwt_secret_key: str = "dev-secret"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 120
    # Include both localhost and 127.0.0.1 — browsers treat them as different origins for CORS.
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    buybox_model_path: str = "backend/model/best_model.pkl"

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
