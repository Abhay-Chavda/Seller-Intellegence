from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=("backend/.env", ".env"),
        env_file_encoding="utf-8",
    )

    database_url: str = "sqlite:///./dev.db"
    database_schema: str = "public"
    jwt_secret_key: str = "replace-with-a-long-random-secret"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 120
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    buybox_model_path: str = "backend/model/best_model.pkl"
    buybox_api_url: str = ""
    buybox_api_timeout_seconds: float = 8.0
    foundry_project_endpoint: str = ""
    foundry_model_deployment_name: str = ""
    foundry_connection_id: str = ""
    foundry_tools_openapi_url: str = ""
    foundry_agent_name_prefix: str = "seller-intelligence-agent"

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
