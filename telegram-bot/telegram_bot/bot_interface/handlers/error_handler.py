import logging
import traceback
from typing import Optional, cast
from telegram import Update
from telegram.ext import ContextTypes
from telegram.error import (
    TelegramError,
    Forbidden,  # Replaces Unauthorized
    BadRequest,
    NetworkError,
    RetryAfter,  # For rate limiting
)
from ..utils.admin_notify import notify_admin

logger = logging.getLogger(__name__)

async def error_handler(update: Optional[Update], context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle errors during bot execution"""
    
    # Extract error information
    error = context.error
    if error is None:
        logger.error("No error found in context")
        return
        
    trace = ''.join(traceback.format_tb(error.__traceback__))
    
    # Prepare error message
    error_msg = f"⚠️ An error occurred while handling an update:\n"
    if update:
        error_msg += f"Update ID: {update.update_id}\n"
        if update.effective_chat:
            error_msg += f"Chat ID: {update.effective_chat.id}\n"
        if update.effective_user:
            error_msg += f"User: {update.effective_user.first_name} (ID: {update.effective_user.id})\n"
        if update.effective_message and update.effective_message.text:
            msg_text = update.effective_message.text
            error_msg += f"Message: {msg_text[:100]}...\n" if len(msg_text) > 100 else f"Message: {msg_text}\n"
    
    # Log different types of errors appropriately
    if isinstance(error, Forbidden):
        error_msg += "❌ Forbidden - Bot was blocked or kicked from the chat"
        logger.warning(error_msg)
    
    elif isinstance(error, BadRequest):
        error_msg += f"🚫 Bad Request: {error}"
        logger.error(error_msg)
    
    elif isinstance(error, RetryAfter):
        error_msg += f"⏱️ Rate limited. Retry after {error.retry_after} seconds"
        logger.warning(error_msg)
    
    elif isinstance(error, NetworkError):
        error_msg += f"🌐 Network Error: {error}"
        logger.error(error_msg)
    
    elif isinstance(error, TelegramError):
        error_msg += f"📱 Telegram Error: {error}"
        logger.error(error_msg)
    
    else:
        error_msg += f"💥 Unexpected Error: {error}\n\nTraceback:\n{trace}"
        logger.error(error_msg)
    
    # Notify admin of the error
    await notify_admin_of_error(error_msg, error, update)
    
    # Try to notify the user if possible
    if update and update.effective_chat:
        try:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="Sorry, an error occurred while processing your request. The bot administrator has been notified."
            )
        except TelegramError:
            logger.error("Could not send error message to user", exc_info=True)

async def notify_admin_of_error(error_msg: str, error: Optional[Exception], update: Optional[Update] = None) -> None:
    """Notify admin of errors with detailed information"""
    if error is None:
        await notify_admin(error_msg)
        return
        
    # Add error details
    error_details = f"{error_msg}\n\nError details:\n{str(error)}"
    if hasattr(error, '__traceback__'):
        trace = ''.join(traceback.format_tb(error.__traceback__))
        error_details += f"\n\nTraceback:\n{trace}"
        
    await notify_admin(error_details)