import logging
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
)

from .config import config
from .commands.start import start_command
from .commands.help import help_command
from .commands.status import status_command
from .commands.info import info_command
from .commands.usage import usage_command
from .commands.dump import dump_command
from .commands.remove_agent import remove_agent_command
from .commands.tools import tools_command
from .handlers.message_handler import handle_message
from .handlers.error_handler import error_handler

logger = logging.getLogger(__name__)

def create_bot() -> Application:
    """Create and configure the bot application"""
    # Configure logging
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=getattr(logging, config.LOG_LEVEL)
    )
    
    # Validate configuration
    config.validate()
    
    # Create application
    app = Application.builder().token(config.TELEGRAM_BOT_TOKEN).build()
    
    # Store admin ID in bot data
    app.bot_data['admin_id'] = config.ADMIN_ID
    
    # Add command handlers
    app.add_handler(CommandHandler('start', start_command))
    app.add_handler(CommandHandler('help', help_command))
    app.add_handler(CommandHandler('status', status_command))
    app.add_handler(CommandHandler('info', info_command))
    app.add_handler(CommandHandler('usage', usage_command))
    app.add_handler(CommandHandler('dump', dump_command))
    app.add_handler(CommandHandler('remove_agent', remove_agent_command))
    app.add_handler(CommandHandler('tools', tools_command))
    
    # Add message handler
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Add error handler
    app.add_error_handler(error_handler)
    
    return app

def run_bot() -> None:
    """Start the bot"""
    app = create_bot()
    logger.info("Starting bot...")
    app.run_polling(poll_interval=config.POLLING_INTERVAL)
