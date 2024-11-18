import os
from dataclasses import dataclass
from typing import Final
from dotenv import load_dotenv

# Load .env file from project root
load_dotenv()

@dataclass
class Config:
    TELEGRAM_BOT_TOKEN: Final[str] = os.environ.get('TELEGRAM_BOT_TOKEN', '')
    POLLING_INTERVAL: Final[float] = float(os.environ.get('POLLING_INTERVAL', '3.0'))
    LOG_LEVEL: Final[str] = os.environ.get('LOG_LEVEL', 'INFO')
    ADMIN_ID: int = 0  # Will be set during validation

    def validate(self) -> None:
        """Validate and process configuration values"""
        if not self.TELEGRAM_BOT_TOKEN:
            raise ValueError("TELEGRAM_BOT_TOKEN environment variable is not set!")
        
        # Process ADMIN_ID
        admin_id = os.environ.get('ADMIN_ID', '')
        if not admin_id:
            raise ValueError("ADMIN_ID environment variable is not set!")
        
        # Handle usernames
        if admin_id.startswith('@'):
            raise ValueError("ADMIN_ID should be a numeric Telegram user ID, not a username")
        
        try:
            self.ADMIN_ID = int(admin_id)
        except ValueError:
            raise ValueError("ADMIN_ID must be a valid integer")

config = Config()