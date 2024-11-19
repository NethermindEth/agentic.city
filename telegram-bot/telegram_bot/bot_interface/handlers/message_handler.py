import logging
from typing import Dict, List
from collections import defaultdict
from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import ContextTypes
from telegram.error import TelegramError

from telegram_bot.agents.agent_manager import agent_manager

logger = logging.getLogger(__name__)

# Rate limiting
MESSAGE_RATE_LIMIT = 5  # messages
RATE_LIMIT_PERIOD = 60  # seconds
# Telegram message length limit (slightly under actual limit for safety)
MAX_MESSAGE_LENGTH = 4000
user_message_counts: Dict[int, list] = defaultdict(list)

def split_long_message(text: str) -> List[str]:
    """Split a long message into chunks that fit within Telegram's message length limit.
    
    Args:
        text: The message text to split
        
    Returns:
        List of message chunks
    """
    if len(text) <= MAX_MESSAGE_LENGTH:
        return [text]
        
    chunks = []
    current_chunk = ""
    
    # Split by newlines first to preserve formatting
    lines = text.split('\n')
    
    for line in lines:
        # If single line is too long, split by spaces
        if len(line) > MAX_MESSAGE_LENGTH:
            words = line.split(' ')
            for word in words:
                if len(current_chunk) + len(word) + 1 > MAX_MESSAGE_LENGTH:
                    chunks.append(current_chunk.strip())
                    current_chunk = word + ' '
                else:
                    current_chunk += word + ' '
        # Otherwise try to add the whole line
        elif len(current_chunk) + len(line) + 1 > MAX_MESSAGE_LENGTH:
            chunks.append(current_chunk.strip())
            current_chunk = line + '\n'
        else:
            current_chunk += line + '\n'
    
    if current_chunk:
        chunks.append(current_chunk.strip())
    
    return chunks

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
        # Get or create agent for this user
        logger.info(f"Getting/creating agent for user {user_id}")
        agent = agent_manager.get_or_create_agent(user_id)
        
        # Send typing action while processing
        await update.message.chat.send_action('typing')
        
        logger.info(f"Running agent loop for user {user_id} with input: {text}")
        messages = agent.run_loop(text)
        
        if not messages:
            logger.warning(f"No response messages from agent for user {user_id}")
            await update.message.reply_text(
                "I apologize, but I didn't receive a proper response. Please try again."
            )
            return
            
        response_sent = False
        for message in messages:
            if message.role == "assistant" and message.content:
                logger.info(f"Sending assistant message to user {user_id}")
                # Split long messages
                chunks = split_long_message(message.content)
                for chunk in chunks:
                    await update.message.reply_text(chunk)
                response_sent = True
            elif message.role == "tool":
                # Format and split tool response
                logger.info(f"Sending tool result to user {user_id}")
                # Get tool name from message
                tool_name = message.name if hasattr(message, 'name') else "Unknown Tool"
                
                tool_response = f"🔧 Tool: {tool_name}\n📋 Result: {message.content}"
                chunks = split_long_message(tool_response)
                for chunk in chunks:
                    await update.message.reply_text(chunk)
                response_sent = True
        
        # If no response was sent, send a default message
        if not response_sent:
            logger.warning(f"No valid response messages to send for user {user_id}")
            await update.message.reply_text(
                "I apologize, but I couldn't generate a proper response. Please try again."
            )
                
    except TelegramError as e:
        logger.error(f"Telegram error for user {user_id}: {e}")
        await update.message.reply_text("Sorry, I encountered an error sending messages.")
    except Exception as e:
        logger.error(f"Error processing message for user {user_id}: {str(e)}", exc_info=True)
        await update.message.reply_text(
            "Sorry, I encountered an unexpected error processing your message. Please try again."
        )