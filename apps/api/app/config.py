"""Application configuration loaded from environment."""

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # App
    app_env: Literal["dev", "staging", "prod"] = "dev"
    log_level: str = "INFO"
    api_url: str = "http://localhost:8000"
    web_url: str = "http://localhost:3000"
    public_web_url: str = "http://localhost:3000"
    cors_origins: list[str] = Field(
        default_factory=lambda: ["http://localhost:3000", "http://127.0.0.1:3000"]
    )

    # Postgres / TimescaleDB
    postgres_user: str = "lews"
    postgres_password: str = "lews_dev"
    postgres_db: str = "lews"
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    database_url_async: str = (
        "postgresql+asyncpg://lews:lews_dev@localhost:5432/lews"
    )

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # JWT
    jwt_secret: str = "change-me-in-prod-please-this-is-not-secure"
    jwt_alg: str = "HS256"
    access_ttl_min: int = 15
    refresh_ttl_days: int = 30

    # Ingest HMAC
    ingest_hmac_secret: str = "sim-shared-secret-change-me"
    ingest_max_skew_sec: int = 300

    # Twilio
    twilio_account_sid: str | None = None
    twilio_auth_token: str | None = None
    twilio_from: str | None = None

    # SendGrid
    sendgrid_api_key: str | None = None
    sendgrid_from: str = "alerts@lews.local"

    # SMTP (dev fallback)
    smtp_host: str = "mailhog"
    smtp_port: int = 1025
    smtp_user: str | None = None
    smtp_password: str | None = None
    smtp_use_tls: bool = False

    # ML
    ml_model_path: Path = Path("app/ml/model_v1.joblib")
    ml_threshold_watch: float = 0.30
    ml_threshold_warning: float = 0.55
    ml_threshold_critical: float = 0.70

    # Simulator
    sim_speedup: int = 60
    sim_interval_sec: int = 15
    sim_ingest_url: str = "http://localhost:8000/v1/ingest/sim"
    sim_hmac_secret: str = "sim-shared-secret-change-me"

    # Worker
    arq_max_jobs: int = 8
    arq_job_timeout_sec: int = 30

    # Seed
    seed_admin_email: str = "admin@acme.test"
    seed_admin_password: str = "admin123"
    seed_tenant_slug: str = "acme"
    seed_tenant_name: str = "Acme Landslide Monitoring"


@lru_cache
def get_settings() -> Settings:
    return Settings()
