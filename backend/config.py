from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(Path(__file__).resolve().parent / ".env"),
        extra="ignore",
        # Allow fields like `model_dir` without conflicting with Pydantic's protected namespaces.
        protected_namespaces=("settings_",),
    )

    # CORS / API
    back_end_cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000,http://localhost:3001,http://127.0.0.1:3001,http://localhost:3002,http://127.0.0.1:3002"
    api_port: int = 8000
    jwt_secret_key: str = "change-me-in-env"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 60 * 24

    # AI providers
    ai_provider: str = "openai"
    openai_api_key: str = ""
    gemini_api_key: str = ""
    gemini_api_base_url: str = "https://generativelanguage.googleapis.com/v1beta/openai/"
    gemini_model: str = "gemini-2.5-flash"
    xai_api_base_url: str = "https://api.x.ai/v1"
    xai_model: str = "grok-4.3"
    openai_model: str = "gpt-4o-mini"

    # Database
    postgres_url: str = ""
    db_echo: bool = False

    # ML artifacts (resolved relative to the backend folder)
    backend_dir: Path = Path(__file__).resolve().parent
    model_dir: str = str(backend_dir / "model")
    diabetes_model_path: str = str(backend_dir / "model" / "diabetes_model.joblib")
    heart_disease_model_path: str = str(backend_dir / "model" / "heart_disease_model.joblib")
    hypertension_model_path: str = str(backend_dir / "model" / "hypertension_model.joblib")
    health_preprocessor_path: str = str(backend_dir / "model" / "health_preprocessor.joblib")
    diabetes_preprocessor_path: str = str(backend_dir / "model" / "health_preprocessor.joblib")


settings = Settings()
