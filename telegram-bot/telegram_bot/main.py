import os
import asyncio
import logging
import sys
from telegram_bot.bot_interface.main import run_bot
from telegram_bot.agents.agent_manager import agent_manager
from telegram_bot.bot_interface.config import config

# Create logs directory if it doesn't exist
log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, 'telegram_bot.log')

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=getattr(logging, config.LOG_LEVEL),
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(log_file, mode='a')
    ]
)

# Set logging levels for specific modules
logging.getLogger('telegram').setLevel(logging.INFO)
logging.getLogger('httpx').setLevel(logging.WARNING)
logging.getLogger('swarmer').setLevel(logging.DEBUG)
logging.getLogger('telegram_bot').setLevel(logging.DEBUG)

logger = logging.getLogger(__name__)

async def main() -> None:
    """Main entry point for the bot"""
    try:
        # Validate configuration
        config.validate()
        
        logger.info("Starting Telegram Bot...")
        await run_bot()
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt. Shutting down...")
        agent_manager.shutdown()
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        agent_manager.shutdown()
        sys.exit(1)

def run() -> None:
    """Run the bot with proper asyncio handling"""
    loop = None
    try:
        # Set better default for Windows
        if sys.platform == "win32":
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        
        # Get or create event loop
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        except Exception as e:
            logger.error(f"Error setting up event loop: {e}", exc_info=True)
            return
        
        # Run the main function
        loop.run_until_complete(main())
        
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
    finally:
        # Clean up
        if loop and not loop.is_closed():
            try:
                # Cancel all tasks except current
                current_task = None
                try:
                    current_task = asyncio.current_task(loop)
                except RuntimeError:
                    pass
                
                tasks = [t for t in asyncio.all_tasks(loop) 
                        if t is not current_task and not t.done()]
                
                if tasks:
                    # Cancel all tasks
                    for task in tasks:
                        task.cancel()
                    
                    # Wait for tasks to complete with timeout
                    try:
                        loop.run_until_complete(
                            asyncio.wait(tasks, timeout=2.0)
                        )
                    except asyncio.CancelledError:
                        pass
                
                # Final cleanup
                try:
                    loop.run_until_complete(loop.shutdown_asyncgens())
                except asyncio.CancelledError:
                    pass
                
            except Exception as e:
                logger.error(f"Error during task cleanup: {e}", exc_info=True)
            finally:
                try:
                    loop.close()
                except Exception as e:
                    logger.error(f"Error closing event loop: {e}", exc_info=True)
        
        sys.exit(0)

if __name__ == "__main__":
    run()