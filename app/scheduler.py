from __future__ import annotations

import asyncio
import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from app.config import Settings
from app.pipeline.run_pipeline import run_once

logger = logging.getLogger(__name__)


async def serve(settings: Settings) -> None:
    scheduler = AsyncIOScheduler(timezone=settings.timezone)
    scheduler.add_job(
        run_once,
        CronTrigger(hour=settings.schedule_hour, minute=settings.schedule_minute),
        kwargs={"settings": settings},
        id="daily_graphics_research_run",
        replace_existing=True,
    )
    scheduler.start()
    logger.info(
        "Scheduler started hour=%s minute=%s timezone=%s",
        settings.schedule_hour,
        settings.schedule_minute,
        settings.timezone,
    )
    try:
        await asyncio.Event().wait()
    finally:
        scheduler.shutdown(wait=False)
