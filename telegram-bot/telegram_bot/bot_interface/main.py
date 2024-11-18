import logging
import sys
from typing import Optional
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
)
from telegram.error import TelegramError
import asyncio
import signal

from .config import config
from .commands.start import start_command
from .commands.help import help_command
from .commands.status import status_command
from .commands.info import info_command
from .commands.usage import usage_command
from .commands.dump import dump_command
from .commands.remove_agent import remove_agent_command
from .commands.tools import tools_command
from .commands.health import health_command
from .handlers.message_handler import handle_message
from .handlers.error_handler import error_handler
from telegram_bot.agents.agent_manager import agent_manager

logger = logging.getLogger(__name__)

# Global application instance
_app: Optional[Application] = None

async def create_application() -> Application:
    """Create and configure the bot application"""
    logger.info("Creating bot application...")
    
    # Create the application with custom settings
    application = (
        Application.builder()
        .token(config.TELEGRAM_BOT_TOKEN)
        .connection_pool_size(8)  # Increase connection pool
        .get_updates_connection_pool_size(4)  # Separate pool for updates
        .read_timeout(12.0)  # Timeout for long polling
        .write_timeout(10.0)  # Timeout for sending messages
        .connect_timeout(10.0)  # Timeout for establishing connections
        .pool_timeout(3.0)  # Timeout for getting connection from pool
        .build()
    )
    
    # Store admin ID in bot data
    application.bot_data['admin_id'] = config.ADMIN_ID
    
    # Register handlers
    logger.info("Registering command handlers...")
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler('status', status_command))
    application.add_handler(CommandHandler('info', info_command))
    application.add_handler(CommandHandler('usage', usage_command))
    application.add_handler(CommandHandler('dump', dump_command))
    application.add_handler(CommandHandler('remove_agent', remove_agent_command))
    application.add_handler(CommandHandler('tools', tools_command))
    application.add_handler(CommandHandler('health', health_command))
    
    # Add message handler
    logger.info("Registering message handler...")
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Add error handler
    application.add_error_handler(error_handler)
    
    # Test connection
    logger.info("Testing bot connection...")
    try:
        bot_info = await application.bot.get_me()
        logger.info(f"Successfully connected to bot: @{bot_info.username}")
    except Exception as e:
        logger.error(f"Failed to connect to bot: {e}")
        raise
    
    return application

async def shutdown(app: Application) -> None:
    """Gracefully shutdown the bot"""
    logger.info("Received shutdown signal, initiating graceful shutdown...")
    
    try:
        # Stop the updater first
        if app.updater:
            logger.info("Stopping updater...")
            try:
                # Don't wait for final get_updates during shutdown
                app.updater._last_update_id = None  # Skip final update check
                await asyncio.wait_for(app.updater.stop(), timeout=2.0)
            except asyncio.TimeoutError:
                logger.warning("Updater stop timed out")
            except Exception as e:
                logger.error(f"Error stopping updater: {e}", exc_info=True)
        
        # Stop the application
        logger.info("Stopping application...")
        try:
            await asyncio.wait_for(app.stop(), timeout=2.0)
            logger.info("Application.stop() complete")
        except asyncio.TimeoutError:
            logger.warning("Application stop timed out")
        except Exception as e:
            logger.error(f"Error stopping application: {e}", exc_info=True)
        
        # Close the bot if it exists
        if app.bot:
            logger.info("Closing bot...")
            try:
                # Skip close webhook call if we hit flood control
                if hasattr(app.bot, '_close_pool'):
                    await asyncio.wait_for(app.bot._close_pool(), timeout=2.0)
            except Exception as e:
                logger.error(f"Error closing bot connection pool: {e}", exc_info=True)
        
        # Cleanup the application
        logger.info("Cleaning up application...")
        try:
            await asyncio.wait_for(app.shutdown(), timeout=2.0)
        except asyncio.TimeoutError:
            logger.warning("Application shutdown timed out")
        except Exception as e:
            logger.error(f"Error during application shutdown: {e}", exc_info=True)
        
        # Cleanup the agent manager
        logger.info("Cleaning up agent manager...")
        try:
            agent_manager.shutdown()
        except Exception as e:
            logger.error(f"Error during agent manager shutdown: {e}", exc_info=True)
        
    except Exception as e:
        logger.error(f"Error during shutdown: {e}", exc_info=True)
    finally:
        logger.info("Bot shutdown complete")

async def run_bot() -> None:
    """Start the bot with proper error handling"""
    global _app
    
    try:
        logger.info("Starting bot...")
        app = await create_application()
        _app = app
        
        # Log startup info
        logger.info("Bot configuration:")
        logger.info(f"- Admin ID: {config.ADMIN_ID}")
        logger.info(f"- Polling Interval: {config.POLLING_INTERVAL}")
        logger.info(f"- Log Level: {config.LOG_LEVEL}")
        
        # Start polling
        logger.info("Starting message polling...")
        await app.initialize()
        await app.start()
        await app.updater.start_polling(poll_interval=config.POLLING_INTERVAL)
        
        # Keep the application running
        stop_signal = asyncio.Event()
        
        def signal_handler():
            logger.info("Received stop signal")
            asyncio.create_task(shutdown(app))
            stop_signal.set()
        
        loop = asyncio.get_event_loop()
        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(sig, signal_handler)
            
        try:
            await stop_signal.wait()
        finally:
            # Remove signal handlers
            for sig in (signal.SIGINT, signal.SIGTERM):
                loop.remove_signal_handler(sig)
        
    except Exception as e:
        logger.critical(f"Bot crashed: {str(e)}", exc_info=True)
        if _app:
            try:
                await shutdown(_app)
            except Exception as shutdown_error:
                logger.error(f"Error during shutdown: {shutdown_error}", exc_info=True)
        raise
