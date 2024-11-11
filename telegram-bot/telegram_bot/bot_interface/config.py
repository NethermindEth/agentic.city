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
    ADMIN_ID: str = os.environ.get('ADMIN_ID', '')

    def validate(self) -> None:
        if not self.TELEGRAM_BOT_TOKEN:
            raise ValueError("TELEGRAM_BOT_TOKEN environment variable is not set!")
        if not self.ADMIN_ID:
            raise ValueError("ADMIN_ID environment variable is not set!")
        if self.ADMIN_ID.startswith('@'):
            self.ADMIN_ID = self.ADMIN_ID[1:]

config = Config() 