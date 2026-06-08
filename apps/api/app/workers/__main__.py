"""arq worker entrypoint."""

import asyncio
import logging

from arq.connections import RedisSettings
from arq.worker import create_worker

from app.config import get_settings
from app.workers.settings import WorkerSettings


async def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
    s = get_settings()
    WorkerSettings.redis_settings = RedisSettings.from_dsn(s.redis_url)
    worker = create_worker(WorkerSettings)
    await worker.async_run()


if __name__ == "__main__":
    asyncio.run(main())
