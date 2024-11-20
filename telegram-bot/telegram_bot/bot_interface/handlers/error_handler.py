"""Module for handling errors and exceptions in the Telegram bot."""

import logging
import traceback
from typing import Optional

from telegram import Update
from telegram.error import BadRequest, Forbidden, NetworkError, TelegramError
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)


async def error_handler(
    update: Optional[Update], context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Handle errors occurring in the dispatcher.

    Args:
        update: The update that caused the error
        context: The context for this handler
    """
    logger.error("Exception while handling an update:", exc_info=context.error)

    try:
        if isinstance(context.error, (BadRequest, Forbidden, NetworkError)):
            # Handle known Telegram API errors
            await handle_telegram_error(update, context, context.error)
        else:
            # Format traceback for unknown errors
            error = context.error
            if error is not None and isinstance(error, Exception):
                tb_list = traceback.format_exception(None, error, error.__traceback__)
                tb_string = "".join(tb_list)

                # Send error message to admin
                if update and update.effective_message:
                    await update.effective_message.reply_text(
                        "Sorry, I encountered an error. The administrator has been notified."
                    )

                logger.error(f"Update {update} caused error:\n{tb_string}")

    except Exception as e:
        logger.error(f"Error in error handler: {e}", exc_info=True)


async def handle_telegram_error(
    update: Optional[Update], context: ContextTypes.DEFAULT_TYPE, error: TelegramError
) -> None:
    """Handle specific Telegram API errors.

    Args:
        update: The update that caused the error
        context: The context for this handler
        error: The specific Telegram error that occurred
    """
