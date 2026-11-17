from pathlib import Path
from typing import Literal
from urllib.parse import urlsplit
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT = Path(__file__).resolve().parents[2]

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=ROOT / ".env", extra="ignore")
    app_env: Literal["development", "production", "test"] = "development"
    host: str = "127.0.0.1"
    port: int = Field(default=8000, ge=1, le=65535)
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    model_path: Path = ROOT / "models/neuralink.keras"
    model_metadata_path: Path = ROOT / "models/metadata.json"
    max_upload_mb: int = Field(default=5, ge=1, le=20)
    max_image_pixels: int = Field(default=12000000, ge=784, le=50000000)
    log_level: str = "INFO"
    rate_limit_enabled: bool = True
    rate_limit_per_minute: int = Field(default=30, ge=1, le=10000)
    uncertainty_threshold: float = Field(default=0.7, ge=0, le=1)

    @field_validator("model_path", "model_metadata_path")
    @classmethod
    def resolve_path(cls, value: Path) -> Path:
        return value if value.is_absolute() else ROOT / value

    @property
    def origins(self) -> list[str]:
        values = [v.strip().rstrip("/") for v in self.cors_origins.split(",") if v.strip()]
        for value in values:
            parts = urlsplit(value)
            if parts.scheme not in {"http", "https"} or not parts.hostname or parts.username or parts.password or parts.path or parts.query or parts.fragment:
                raise ValueError("CORS requires explicit HTTP(S) origins without paths or credentials")
        if "*" in values:
            raise ValueError("CORS requires explicit origins")
        if self.app_env == "production" and (not values or any(not v.startswith("https://") for v in values)):
            raise ValueError("Production CORS origins must use HTTPS")
        return values

    @property
    def upload_bytes(self) -> int:
        return self.max_upload_mb * 1024 * 1024
