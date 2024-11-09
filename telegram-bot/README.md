# Telegram Bot

A production-ready Telegram bot built with python-telegram-bot.

## Features

- Command handling (/start, /help, /status, /info)
- Rate limiting
- Error handling
- Logging
- Configuration management
- Type hints
- Security best practices

## Setup

1. Create a new bot through [BotFather](https://t.me/botfather) on Telegram
2. Copy `.env.example` to `.env`:
   ```bash
   cp telegram_bot/.env.example telegram_bot/.env
   ```
3. Edit `.env` and add your bot token
4. Install dependencies:
   ```bash
   poetry install
   ```

## Running the Bot

Run the bot using Poetry:
```bash
poetry run python -m telegram_bot.main
```
