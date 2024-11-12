import logging
from telegram import Update
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Error handler"""
    logger.error(f"Update {update} caused error {context.error}\n\n{context}")
    try:
        if isinstance(update, Update) and update.effective_message:
            await update.effective_message.reply_text(
                "Sorry, I encountered an error processing your request. "
                "Please try again later."
            )
    except Exception as e:
        logger.error(f"Error in error handler: {e}") 