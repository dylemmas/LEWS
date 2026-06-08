"""Simulator config."""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )
    api_url: str = "http://localhost:8000/v1/ingest/sim"
    hmac_secret: str = "sim-shared-secret-change-me"
    speedup: int = 60
    interval_sec: int = 15
    log_level: str = "INFO"
    seed_nodes: int = 5


def get_settings() -> Settings:
    return Settings()
