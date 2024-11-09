from telegram import Update
from telegram.ext import ContextTypes

async def info_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for /info command"""
    user = update.effective_user
    chat = update.effective_chat
    
    info_text = (
        f'👤 User Info:\n'
        f'ID: {user.id}\n'
        f'Name: {user.full_name}\n'
        f'Username: @{user.username if user.username else "None"}\n'
        f'Language: {user.language_code}\n\n'
        f'💭 Chat Info:\n'
        f'Chat ID: {chat.id}\n'
        f'Chat Type: {chat.type}'
    )
    await update.message.reply_text(info_text) 