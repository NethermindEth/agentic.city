import logging
from typing import Dict
from collections import defaultdict
from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import ContextTypes
from telegram.error import TelegramError

from telegram_bot.agents.basic import agent

logger = logging.getLogger(__name__)

# Rate limiting
MESSAGE_RATE_LIMIT = 5  # messages
RATE_LIMIT_PERIOD = 60  # seconds
user_message_counts: Dict[int, list] = defaultdict(list)

def check_rate_limit(user_id: int) -> bool:
    """Check if user has exceeded rate limit"""
    current_time = datetime.now()
    # Clean old messages
    user_message_counts[user_id] = [
        timestamp for timestamp in user_message_counts[user_id]
        if current_time - timestamp < timedelta(seconds=RATE_LIMIT_PERIOD)
    ]
    
    if len(user_message_counts[user_id]) >= MESSAGE_RATE_LIMIT:
        return False
    
    user_message_counts[user_id].append(current_time)
    return True

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handler for text messages"""
    if not update.message or not update.effective_user:
        return

    user_id = update.effective_user.id
    
    # Check rate limit
    if not check_rate_limit(user_id):
        await update.message.reply_text(
            f"⚠️ Rate limit exceeded. Please wait before sending more messages."
        )
        return

    message_type: str = update.message.chat.type
    # Add null check for text
    if not update.message.text:
        await update.message.reply_text("Please send a text message.")
        return
        
    text: str = update.message.text
    
    logger.info(f'User ({user_id}) in {message_type}: "{text}"')
    
    try:
        messages = agent.run_loop(text)
        
        for message in messages:
            print("++++++++++++++", message)
            if message.role == "assistant" and message.content:
                await update.message.reply_text(message.content)
            elif message.role == "tool":
                # Format tool response nicely
                tool_response = f"🔧 Tool Result:\n{message.content}"
                await update.message.reply_text(tool_response)
                
    except TelegramError as e:
        logger.error(f"Error sending message: {e}")
        await update.message.reply_text("Sorry, I encountered an error processing your message.") 