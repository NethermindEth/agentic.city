"""Module for managing bot configuration and settings."""

import os
from dataclasses import dataclass, field
from typing import Final, List

from dotenv import load_dotenv

# Load .env file from project root
load_dotenv()


@dataclass
class Config:
    """Manages bot configuration settings.

    Handles loading and accessing bot configuration data from environment variables.
    Provides defaults for missing values.
    """

    TELEGRAM_BOT_TOKEN: Final[str] = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    POLLING_INTERVAL: Final[float] = float(os.environ.get("POLLING_INTERVAL", "3.0"))
    LOG_LEVEL: Final[str] = os.environ.get("LOG_LEVEL", "INFO")
    ADMIN_ID: int = 0  # Primary admin ID
    admin_ids: List[str] = field(default_factory=list)  # List of all admin IDs

    def validate(self) -> None:
        """Validate and process configuration values.

        Raises:
            ValueError: If required environment variables are not set.
        """
        if not self.TELEGRAM_BOT_TOKEN:
            raise ValueError("TELEGRAM_BOT_TOKEN environment variable is not set!")

        # Process ADMIN_ID
        admin_id = os.environ.get("ADMIN_ID", "")
        if not admin_id:
            raise ValueError("ADMIN_ID environment variable is not set!")

        # Handle usernames
        if admin_id.startswith("@"):
            raise ValueError(
                "ADMIN_ID should be a numeric Telegram user ID, not a username."
            )

        try:
            self.ADMIN_ID = int(admin_id)
        except ValueError:
            raise ValueError("ADMIN_ID must be a valid integer.")

        # Process additional admin IDs
        admin_ids = os.environ.get("ADMIN_IDS", str(self.ADMIN_ID))
        self.admin_ids = [id.strip() for id in admin_ids.split(",")]

        # Validate additional admin IDs
        for id in self.admin_ids:
            if id.startswith("@"):
                raise ValueError(
                    "ADMIN_IDS should be a comma-separated list of numeric Telegram user IDs, not usernames."
                )

            try:
                int(id)
            except ValueError:
                raise ValueError(
                    "ADMIN_IDS must be a comma-separated list of valid integers."
                )


config = Config()
