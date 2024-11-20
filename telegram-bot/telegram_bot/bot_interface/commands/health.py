"""Module for handling the health check command in the Telegram bot."""

import json
import time
from typing import Awaitable, Callable

import psutil
from telegram import Update
from telegram.ext import ContextTypes

from telegram_bot.agents.agent_manager import agent_manager


def admin_only(
    func: Callable[[Update, ContextTypes.DEFAULT_TYPE], Awaitable[None]]
) -> Callable[[Update, ContextTypes.DEFAULT_TYPE], Awaitable[None]]:
    """Restrict command access to admin users only.

    Args:
        func: The function to wrap with admin-only access

    Returns:
        A wrapped function that checks for admin access before executing
    """

    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not update.message or not update.effective_user:
            return

        admin_id = context.bot_data.get("admin_id", "")
        is_admin = (
            update.effective_user.username
            and update.effective_user.username.lower() == admin_id.lower()
        )

        message = update.message
        if not is_admin and message:
            await message.reply_text(
                "⚠️ This command is only available to the bot administrator."
            )
            return

        await func(update, context)

    return wrapper


@admin_only
async def health_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Check the system health status.

    Returns system metrics like CPU usage, memory usage, and disk space.

    Args:
        update: The update containing the command
        context: The context for this handler
    """
    if not update.message:
        return

    try:
        process = psutil.Process()
        memory = process.memory_info()
        uptime = time.time() - process.create_time()

        status = {
            "status": "healthy",
            "uptime": f"{uptime:.2f}s",
            "memory_usage": f"{memory.rss / 1024 / 1024:.2f}MB",
            "cpu_percent": f"{process.cpu_percent()}%",
            "active_agents": len(agent_manager.agents),
            "disk_usage": {
                "total": f"{psutil.disk_usage('/').total / (1024**3):.1f}GB",
                "used": f"{psutil.disk_usage('/').used / (1024**3):.1f}GB",
                "free": f"{psutil.disk_usage('/').free / (1024**3):.1f}GB",
            },
        }

        await update.message.reply_text(
            "🤖 Bot Health Status:\n" f"```json\n{json.dumps(status, indent=2)}\n```",
            parse_mode="Markdown",
        )
    except Exception as e:
        await update.message.reply_text(f"❌ Error getting health status: {str(e)}")
