"""arq worker settings."""

from __future__ import annotations

from app.config import get_settings
from app.workers.alert_worker import process_reading

settings = get_settings()


class WorkerSettings:
    functions = [process_reading]
    redis_settings = _redis_settings = None  # populated at runtime
    max_jobs = settings.arq_max_jobs
    job_timeout = settings.arq_job_timeout_sec
    keep_result = 60
    health_check_interval = 30


def build_worker_settings():
    from arq.connections import RedisSettings

    s = get_settings()
    return WorkerSettings(
        redis_settings=RedisSettings.from_dsn(s.redis_url),
    )
