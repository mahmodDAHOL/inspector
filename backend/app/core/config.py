"""Application Configuration"""
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    APP_NAME: str = "Inspection Portal"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    SECRET_KEY: str = "dev-secret-key"
    MASTER_ENCRYPTION_KEY: str = "dev-encryption-key"
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

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
