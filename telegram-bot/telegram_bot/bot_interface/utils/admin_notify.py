import logging
import asyncio
from typing import Optional, Any, List
from datetime import datetime, timedelta
from telegram.error import TelegramError, RetryAfter
from telegram import Bot
from telegram_bot.bot_interface.config import config

logger = logging.getLogger(__name__)

class RateLimiter:
    def __init__(self, rate_limit: int = 1, per_seconds: int = 3):
        self.rate_limit = rate_limit
        self.per_seconds = per_seconds
        self.calls: List[datetime] = []
        self._lock = asyncio.Lock()
    
    async def acquire(self) -> None:
        """Acquire rate limit slot"""
        async with self._lock:
            now = datetime.now()
            # Remove old calls
            self.calls = [t for t in self.calls 
                         if now - t < timedelta(seconds=self.per_seconds)]
            
            if len(self.calls) >= self.rate_limit:
                # Calculate wait time
                oldest_call = self.calls[0]
                wait_time = (oldest_call + timedelta(seconds=self.per_seconds) - now).total_seconds()
                if wait_time > 0:
                    await asyncio.sleep(wait_time)
                self.calls = self.calls[1:]
            
            self.calls.append(now)

_rate_limiter = RateLimiter()
_bot: Optional[Bot] = None

async def get_bot() -> Bot:
    """Get or create bot instance"""
    global _bot
    if _bot is None:
        from telegram_bot.bot_interface.main import _app
        if _app is None:
            raise RuntimeError("Application not initialized")
        _bot = _app.bot
    return _bot

async def notify_admin(message: str, error: Any = None, retry_count: int = 3) -> None:
    """Send notification to admin with rate limiting and retries"""
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
            
            bot = await get_bot()
            await bot.send_message(
                chat_id=config.ADMIN_ID,
                text=formatted_msg
            )
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
