import logging
import traceback
from typing import Optional
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
    trace = ''.join(traceback.format_tb(error.__traceback__))
    
    # Prepare error message
    error_msg = f"⚠️ An error occurred while handling an update:\n"
    if update:
        error_msg += f"Update ID: {update.update_id}\n"
        if update.effective_chat:
            error_msg += f"Chat ID: {update.effective_chat.id}\n"
        if update.effective_user:
            error_msg += f"User: {update.effective_user.first_name} (ID: {update.effective_user.id})\n"
        if update.effective_message:
            error_msg += f"Message: {update.effective_message.text[:100]}...\n" if len(update.effective_message.text) > 100 else f"Message: {update.effective_message.text}\n"
    
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

async def notify_admin_of_error(error_msg: str, error: Exception, update: Optional[Update] = None) -> None:
    """Notify admin of errors with detailed information"""
    try:
        # Add debug information
        debug_info = "\n\nDebug Information:"
        if update:
            debug_info += f"\nUpdate Type: {update.update_id}"
            if update.effective_message:
                debug_info += f"\nMessage Type: {update.effective_message.type}"
        
        # Add error details
        debug_info += f"\nError Type: {type(error).__name__}"
        if hasattr(error, 'message'):
            debug_info += f"\nError Message: {error.message}"
        
        # Add traceback
        debug_info += f"\n\nTraceback:\n{traceback.format_exc()}"
        
        # Send notification
        await notify_admin(error_msg + debug_info)
    except Exception as e:
        logger.error(f"Failed to notify admin of error: {str(e)}", exc_info=True)