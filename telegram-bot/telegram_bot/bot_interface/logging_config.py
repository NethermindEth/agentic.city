"""Module for configuring logging settings and handlers for the Telegram bot.

This module sets up logging configuration for both file and console output,
with different formatting for each handler type. It supports different log levels
and includes rotation of log files to manage disk space.
"""

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path


def setup_logging() -> None:
    """Configure logging with both file and console handlers."""
    # Create logs directory if it doesn't exist
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    # Format for logs
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # Main log file handler (rotating, max 10MB, keep 5 backup files)
    main_handler = RotatingFileHandler(
        "logs/bot.log", maxBytes=10 * 1024 * 1024, backupCount=5  # 10MB
    )
    main_handler.setFormatter(formatter)
    root_logger.addHandler(main_handler)

    # Error log file handler
    error_handler = RotatingFileHandler(
        "logs/error.log", maxBytes=10 * 1024 * 1024, backupCount=5  # 10MB
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)
    root_logger.addHandler(error_handler)

    # Set third-party loggers to WARNING to reduce noise
    logging.getLogger("telegram").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
