"""Run the arq worker."""

import asyncio
import logging

from arq import run_worker
from arq.connections import RedisSettings

from app.config import get_settings
from app.workers.alert_worker import process_reading


async def main():
    s = get_settings()
    logging.basicConfig(level=s.log_level, format="%(asctime)s %(levelname)-5s %(name)s :: %(message)s")
    logging.getLogger(__name__).info("Starting arq worker…")
    redis = RedisSettings.from_dsn(s.redis_url)
    await run_worker(
        functions=[process_reading],
        redis_settings=redis,
        max_jobs=s.arq_max_jobs,
        job_timeout=s.arq_job_timeout_sec,
        keep_result=60,
        health_check_interval=30,
    )


if __name__ == "__main__":
    asyncio.run(main())
