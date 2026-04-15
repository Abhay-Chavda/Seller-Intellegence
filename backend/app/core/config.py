from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    database_url: str = "postgresql+psycopg://neondb_owner:npg_eE0D2zgBqoIb@ep-fragrant-wind-a8m7evi9-pooler.eastus2.azure.neon.tech/neondb?sslmode=require&channel_binding=require"
    database_schema: str = "seller_intelligence"
    jwt_secret_key: str = "7zJh4J5JsxUlFB9I"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 120
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    buybox_model_path: str = "backend/model/best_model.pkl"
    buybox_api_url: str = "http://willowcore-stage-dashboardapi-lb-582389980.us-east-1.elb.amazonaws.com/predict"
    buybox_api_timeout_seconds: float = 8.0

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
