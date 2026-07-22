"""APScheduler wrapper — all recurring agent jobs register here."""
import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.executors.asyncio import AsyncIOExecutor

log = logging.getLogger("jarvis.scheduler")

_scheduler = AsyncIOScheduler(
    executors={"default": AsyncIOExecutor()},
    job_defaults={"coalesce": True, "max_instances": 1, "misfire_grace_time": 30},
)


def get_scheduler() -> AsyncIOScheduler:
    return _scheduler


def start():
    if not _scheduler.running:
        _scheduler.start()
        log.info("Scheduler started")


def shutdown():
    if _scheduler.running:
        _scheduler.shutdown(wait=False)
