"""Screener batch job scheduler.

Runs daily post-market-close (after 3:30 PM IST).
Idempotent — re-running for the same date overwrites previous results.
"""

import asyncio
import logging
from datetime import date

from app.database import SessionLocal
from app.services.screener.adapters.base import DataSourceAdapter
from app.services.screener.engine import run_screener
from app.utils.datetime_helpers import market_hours_active, utc_now, to_ist

logger = logging.getLogger(__name__)


async def run_daily_screener(adapter: DataSourceAdapter) -> dict:
    """Execute daily screener batch job.

    Should be triggered post-market-close. Checks that market is closed
    before running to avoid mid-day data inconsistency.
    """
    if market_hours_active():
        logger.warning("Market is still open — screener should run post-close. Proceeding anyway.")

    today = date.today()
    logger.info(f"Starting daily screener run for {today}")

    db = SessionLocal()
    try:
        # Delete existing results for today (idempotent re-run)
        from app.models.screener import ScreenerResult
        deleted = db.query(ScreenerResult).filter(ScreenerResult.run_date == today).delete()
        if deleted:
            logger.info(f"Cleared {deleted} existing results for {today}")
        db.commit()

        summary = await run_screener(adapter, db, run_date=today)
        logger.info(f"Daily screener complete: {summary}")
        return summary
    finally:
        db.close()


def start_scheduler(adapter: DataSourceAdapter):
    """Start the daily screener scheduler.

    In production, use a proper scheduler (APScheduler, Celery Beat, or cron).
    This is a simple loop for development.
    """
    async def _loop():
        while True:
            now_ist = to_ist(utc_now())
            # Run at 4:00 PM IST (30 min after market close)
            if now_ist.hour == 16 and now_ist.minute == 0:
                try:
                    await run_daily_screener(adapter)
                except Exception as e:
                    logger.error(f"Daily screener failed: {e}")
            await asyncio.sleep(60)  # Check every minute

    asyncio.create_task(_loop())
