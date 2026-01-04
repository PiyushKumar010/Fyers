import asyncio
import logging
from datetime import datetime
from typing import Optional

from app import database
from app.config import settings
from app.services import fyers as fyers_service

logger = logging.getLogger("token_refresher")

_task: Optional[asyncio.Task] = None


async def _refresher_loop():
    """Background loop that refreshes Fyers access token before expiry."""
    while True:
        try:
            tokens_collection = database.tokens_collection
            if tokens_collection is None:
                logger.warning("MongoDB not available; retrying in 60s")
                await asyncio.sleep(60)
                continue

            token_doc = tokens_collection.find_one()
            if not token_doc or "refresh_token" not in token_doc:
                logger.info("No refresh token stored yet; retrying in 60s")
                await asyncio.sleep(60)
                continue

            try:
                expires_in = int(token_doc.get("expires_in", 0))
                obtained_at = float(token_doc.get("obtained_at", 0))
            except Exception:
                expires_in = 0
                obtained_at = 0

            if expires_in <= 0 or obtained_at <= 0:
                # Unknown expiry: wake up periodically to check again
                logger.info("No expiry info; will recheck in %s seconds", settings.REFRESH_CHECK_INTERVAL)
                await asyncio.sleep(settings.REFRESH_CHECK_INTERVAL)
                continue

            expiry_time = obtained_at + expires_in
            refresh_time = expiry_time - settings.REFRESH_BUFFER_SECONDS
            now = datetime.utcnow().timestamp()
            wait_seconds = max(refresh_time - now, 0)

            if wait_seconds > 0:
                logger.info("Next token refresh scheduled in %s seconds", int(wait_seconds))
                await asyncio.sleep(wait_seconds)

            # Time to refresh
            logger.info("Attempting token refresh now")
            try:
                # refresh_access_token is synchronous; run in thread
                await asyncio.to_thread(fyers_service.refresh_access_token)
                logger.info("Token refresh successful")
            except Exception as e:
                logger.exception("Token refresh failed: %s", e)
                # Wait a bit before retrying to avoid tight loop
                await asyncio.sleep(settings.REFRESH_CHECK_INTERVAL)

            # short pause before loop recalculates timings
            await asyncio.sleep(2)

        except asyncio.CancelledError:
            logger.info("Token refresher cancelled")
            break
        except Exception as e:
            logger.exception("Unexpected error in token refresher: %s", e)
            await asyncio.sleep(settings.REFRESH_CHECK_INTERVAL)


def start_refresher():
    global _task
    if _task is None:
        try:
            print("[token_refresher] creating refresher task")
            _task = asyncio.create_task(_refresher_loop())
            logger.info("Token refresher started")
            print("[token_refresher] refresher task created")
        except Exception as e:
            logger.exception("Failed to create refresher task: %s", e)
            print("[token_refresher] Failed to create refresher task:", e)
    else:
        print("[token_refresher] refresher task already exists")
    return _task


async def stop_refresher():
    global _task
    if _task is not None:
        _task.cancel()
        try:
            await _task
        except asyncio.CancelledError:
            pass
        _task = None
        logger.info("Token refresher stopped")
