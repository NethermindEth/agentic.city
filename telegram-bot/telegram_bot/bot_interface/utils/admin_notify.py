"""Module for sending notifications to bot administrators.

This module provides functionality to send important messages, errors,
and system notifications to designated bot administrators through Telegram.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, List, Optional

from telegram import Bot, Update
from telegram.error import RetryAfter, TelegramError
from telegram.ext import ContextTypes

from telegram_bot.bot_interface.config import config

logger = logging.getLogger(__name__)


class RateLimiter:
    """Rate limiter for controlling the frequency of operations.

    This class implements a token bucket rate limiter to prevent operations
    from exceeding a specified rate limit within a time window.
    """

    def __init__(self, rate_limit: int = 1, per_seconds: int = 3):
        """Initialize the rate limiter.

        Args:
            rate_limit: Maximum number of operations allowed per time window.
            per_seconds: Time window in seconds.
        """
        self.rate_limit = rate_limit
        self.per_seconds = per_seconds
        self.calls: List[datetime] = []
        self._lock = asyncio.Lock()

    async def acquire(self) -> None:
        """Wait for and acquire a rate limit slot.

        This method blocks until a rate limit slot becomes available. It ensures
        that operations do not exceed the configured rate limit by implementing
        a sliding window rate limiting algorithm.
        """
        async with self._lock:
            now = datetime.now()
            # Remove old calls
            self.calls = [
                t for t in self.calls if now - t < timedelta(seconds=self.per_seconds)
            ]

            if len(self.calls) >= self.rate_limit:
                # Calculate wait time
                oldest_call = self.calls[0]
                wait_time = (
                    oldest_call + timedelta(seconds=self.per_seconds) - now
                ).total_seconds()
                if wait_time > 0:
                    await asyncio.sleep(wait_time)
                self.calls = self.calls[1:]

            self.calls.append(now)


_rate_limiter = RateLimiter()
_bot: Optional[Bot] = None


async def get_bot() -> Bot:
    """Get or create bot instance."""
    global _bot
    if _bot is None:
        from telegram_bot.bot_interface.main import _app

        if _app is None:
            raise RuntimeError("Application not initialized.")
        _bot = _app.bot
    return _bot


def admin_only(func):
    """Ensure a command can only be used by admin users.

    Args:
        func: The function to wrap

    Returns:
        The wrapped function that checks for admin status
    """

    async def wrapper(
        update: "Update", context: "ContextTypes.DEFAULT_TYPE", *args, **kwargs
    ):
        if (
            not update.effective_user
            or str(update.effective_user.id) not in config.admin_ids
        ):
            await update.message.reply_text(
                "This command is only available to administrators."
            )
            return
        return await func(update, context, *args, **kwargs)

    return wrapper


async def notify_admin(
    message: str, error: Any = None, retry_count: int = 3, bot: Optional[Bot] = None
) -> None:
    """Send a notification message to the bot administrator.

    Args:
        message: The message to send to the administrator
        error: Optional error message to include in the notification
        retry_count: Number of times to retry sending the message if it fails
        bot: Optional Bot instance to use for sending the message.
            If not provided, will attempt to use a cached bot instance.

    Raises:
        TelegramError: If there's an error sending the message
    """
    if not config.ADMIN_ID:
        logger.warning("No ADMIN_ID configured, skipping admin notification")
        return

    formatted_msg = f"{message}"
    if error:
        formatted_msg += f"\nError: {str(error)}"

    for attempt in range(retry_count):
        try:
            # Acquire rate limit slot
            await _rate_limiter.acquire()

            bot = bot or await get_bot()
            await bot.send_message(chat_id=config.ADMIN_ID, text=formatted_msg)
            return

        except RetryAfter as e:
            if attempt < retry_count - 1:
                await asyncio.sleep(e.retry_after)
            else:
                logger.error(f"Rate limit exceeded after {retry_count} attempts")
                raise

        except TelegramError as e:
            if attempt < retry_count - 1:
                await asyncio.sleep(1)
            else:
                logger.error(f"Failed to send admin notification: {e}")
                raise

        except Exception as e:
            logger.error(f"Unexpected error in admin notification: {e}")
            raise
