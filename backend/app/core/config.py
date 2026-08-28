"""Application Configuration"""
from pydantic_settings import BaseSettings
from pydantic import field_validator
from functools import lru_cache
from typing import List


class Settings(BaseSettings):
    APP_NAME: str = "Inspection Portal"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # No defaults on purpose: a missing secret must fail startup loudly
    # rather than silently running with a well-known, guessable value.
    SECRET_KEY: str
    MASTER_ENCRYPTION_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    TOTP_ISSUER: str = "Syria-MOI-Inspection"

    DATABASE_URL: str = "postgresql+asyncpg://inspection_app:pass@db:5432/inspection_portal"
    REDIS_URL: str = "redis://:pass@redis:6379/0"

    MEDIAGATE_API_URL: str = "https://mediagate.gov.sy/api"
    MEDIAGATE_API_KEY: str = ""

    UPLOAD_DIR: str = "/var/inspection/uploads"
    MAX_FILE_SIZE_MB: int = 50
    AUDIT_LOG_RETENTION_YEARS: int = 7

    ALLOWED_ORIGINS: str = "https://localhost"
    ALLOWED_HOSTS: str = "localhost"

    @field_validator("SECRET_KEY", "MASTER_ENCRYPTION_KEY")
    @classmethod
    def _reject_weak_secrets(cls, value: str, info) -> str:
        if not value or len(value) < 16 or value in {"dev-secret-key", "dev-encryption-key", "change-me"}:
            raise ValueError(
                f"{info.field_name} is missing or looks like a placeholder. "
                f"Generate a real value (see .env.example) before starting the app."
            )
        return value

    @property
    def allowed_origins_list(self) -> List[str]:
        return [o.strip() for o in self.ALLOWED_ORIGINS.split(",") if o.strip()]

    @property
    def allowed_hosts_list(self) -> List[str]:
        return [h.strip() for h in self.ALLOWED_HOSTS.split(",") if h.strip()]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
