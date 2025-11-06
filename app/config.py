"""Application configuration powered by Pydantic settings."""

from __future__ import annotations

from datetime import timedelta
from json import loads
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseSettings, Field, validator


class Settings(BaseSettings):
    """Runtime configuration pulled from environment variables and .env."""

    flask_env: str = Field(default="production", env="FLASK_ENV")
    secret_key: str = Field(default="change-this", env="SECRET_KEY")
    jwt_secret_key: str = Field(default="change-this-jwt", env="JWT_SECRET_KEY")
    database_uri: str = Field(
        default="sqlite:///lab.db",
        env="DATABASE_URI",
        description="SQLAlchemy connection string.",
    )

    rate_redis_url: Optional[str] = Field(default=None, env="RATE_REDIS_URL")
    api_keys_json: Dict[str, List[str]] = Field(
        default_factory=dict, env="API_KEYS_JSON"
    )

    jwt_access_token_expires_hours: int = Field(default=12, ge=1, le=72)
    jwt_refresh_token_expires_days: int = Field(default=30, ge=1, le=365)

    oo_base_url: str = Field(default="http://onlyoffice-d:80", env="OO_BASE_URL")
    oo_jwt_secret: Optional[str] = Field(default=None, env="OO_JWT_SECRET")
    base_file_dir: Path = Field(default=Path("/mnt/docs"), env="BASE_FILE_DIR")

    cors_allowed_origins: List[str] = Field(
        default_factory=list, env="CORS_ALLOWED_ORIGINS"
    )
    enable_swagger: bool = Field(default=True, env="ENABLE_SWAGGER")

    sentry_dsn: Optional[str] = Field(default=None, env="SENTRY_DSN")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

        @classmethod
        def parse_env_var(cls, field_name: str, raw_value: Any):
            if field_name == "cors_allowed_origins" and raw_value in ("", None):
                return []
            return BaseSettings.Config.parse_env_var(field_name, raw_value)

    @validator("api_keys_json", pre=True)
    def _parse_api_keys(cls, value: Any) -> Dict[str, List[str]]:
        if not value:
            return {}
        if isinstance(value, dict):
            return value
        try:
            parsed: Dict[str, List[str]] = loads(value)
        except Exception as exc:  # pragma: no cover - defensive branch
            raise ValueError("API_KEYS_JSON must be valid JSON") from exc
        return parsed

    @validator("cors_allowed_origins", pre=True)
    def _split_origins(cls, value: Union[str, List[str], None]) -> List[str]:
        if value is None or value == "":
            return []
        if isinstance(value, list):
            return value
        return [origin.strip() for origin in str(value).split(",") if origin.strip()]

    @property
    def jwt_access_delta(self) -> timedelta:
        """Timedelta used by Flask-JWT-Extended for access tokens."""
        return timedelta(hours=self.jwt_access_token_expires_hours)

    @property
    def jwt_refresh_delta(self) -> timedelta:
        """Timedelta used by Flask-JWT-Extended for refresh tokens."""
        return timedelta(days=self.jwt_refresh_token_expires_days)

    @property
    def swagger_ui_enabled(self) -> bool:
        """Return True when Swagger UI should be exposed."""
        return self.enable_swagger


settings = Settings()
