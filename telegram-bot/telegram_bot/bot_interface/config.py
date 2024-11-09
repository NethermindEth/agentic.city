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

    def validate(self):
        if not self.TELEGRAM_BOT_TOKEN:
            raise ValueError("TELEGRAM_BOT_TOKEN environment variable is not set!")

config = Config() 