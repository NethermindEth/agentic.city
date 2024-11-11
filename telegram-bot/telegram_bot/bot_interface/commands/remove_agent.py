from telegram import Update
from telegram.ext import ContextTypes
from telegram_bot.agents.agent_manager import agent_manager
from typing import Optional

async def find_user_id(username: str, context: ContextTypes.DEFAULT_TYPE) -> Optional[int]:
    """Try to get user ID from username"""
    if username.startswith('@'):
        username = username[1:]  # Remove @ if present
    
    # Try to get chat member info from the current chat
    try:
        chat_member = await context.bot.get_chat_member(
            chat_id=context.chat_data.get('chat_id'),
            user_id='@' + username
        )
        return chat_member.user.id
    except:
        return None

async def remove_agent_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handler for /remove_agent command"""
    if not update.message or not update.effective_user:
        return

    # Only allow admin to use this command
    admin_id = context.bot_data.get('admin_id', '')
    is_admin = (update.effective_user.username and 
                update.effective_user.username.lower() == admin_id.lower())
    
    if not is_admin:
        await update.message.reply_text("⚠️ This command is only available to the bot administrator.")
        return

    if not context.args:
        await update.message.reply_text(
            "Please provide a user ID or username.\n"
            "Usage: /remove_agent <user_id or @username>"
        )
        return

    user_identifier = context.args[0]
    
    try:
        # Try parsing as numeric ID first
        if user_identifier.isdigit():
            user_id = int(user_identifier)
        else:
            # Try resolving username
            user_id = await find_user_id(user_identifier, context)
            if user_id is None:
                await update.message.reply_text(
                    f"Could not find user with identifier: {user_identifier}"
                )
                return
        
        if agent_manager.remove_agent(user_id):
            await update.message.reply_text(
                f"Successfully removed agent for user {user_identifier} (ID: {user_id})"
            )
        else:
            await update.message.reply_text(
                f"No agent found for user {user_identifier} (ID: {user_id})"
            )
    except ValueError:
        await update.message.reply_text(
            "Invalid user identifier. Please provide either a numeric ID or a username starting with @"
        ) 