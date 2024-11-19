"""Module for handling incoming Telegram messages and user interactions."""

import logging
from collections import defaultdict
from datetime import datetime, timedelta
from typing import List

from telegram import Update
from telegram.ext import ContextTypes

from telegram_bot.agents.agent_manager import agent_manager

logger = logging.getLogger(__name__)

# Store message timestamps for rate limiting
_user_messages: defaultdict = defaultdict(list)
MAX_MESSAGES = 10  # Maximum messages per time window
TIME_WINDOW = timedelta(minutes=1)  # Time window for rate limiting


def split_long_message(text: str) -> List[str]:
    """Split a long message into chunks that fit within Telegram's message length limit.

    Args:
        text: The message text to split

    Returns:
        List of message chunks
    """
    if len(text) <= 4000:
        return [text]

    chunks = []
    current_chunk = ""

    # Split by newlines first to preserve formatting
    lines = text.split("\n")

    for line in lines:
        # If single line is too long, split by spaces
        if len(line) > 4000:
            words = line.split(" ")
            for word in words:
                if len(current_chunk) + len(word) + 1 > 4000:
                    chunks.append(current_chunk.strip())
                    current_chunk = word + " "
                else:
                    current_chunk += word + " "
        # Otherwise try to add the whole line
        elif len(current_chunk) + len(line) + 1 > 4000:
            chunks.append(current_chunk.strip())
            current_chunk = line + "\n"
        else:
            current_chunk += line + "\n"

    if current_chunk:
        chunks.append(current_chunk.strip())

    return chunks


def check_rate_limit(user_id: int) -> bool:
    """Check if user has exceeded rate limit."""
    current_time = datetime.now()
    # Clean old messages
    _user_messages[user_id] = [
        timestamp
        for timestamp in _user_messages[user_id]
        if current_time - timestamp < TIME_WINDOW
    ]

    if len(_user_messages[user_id]) >= MAX_MESSAGES:
        return False

    _user_messages[user_id].append(current_time)
    return True


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Process incoming messages and generate appropriate responses.

    Handles text messages, manages agent interactions, and processes user requests.
    Logs message details and notifies admins of potential issues.

    Args:
        update: The update containing the message
        context: The context for this handler
    """
    if not update.message or not update.effective_user:
        return

    user_id = update.effective_user.id

    # Check rate limit
    if not check_rate_limit(user_id):
        await update.message.reply_text(
            "⚠️ Rate limit exceeded. Please wait before sending more messages."
        )
        return

    message_type: str = update.message.chat.type
    # Add null check for text
    if not update.message.text:
        await update.message.reply_text("Please send a text message.")
        return

    text: str = update.message.text

    logger.info('User (%s) in %s: "%s"', user_id, message_type, text)

    try:
        # Get or create agent for this user
        logger.info("Getting/creating agent for user %s", user_id)
        agent = agent_manager.get_or_create_agent(user_id)

        # Send typing action while processing
        await update.message.chat.send_action("typing")

        logger.info("Running agent loop for user %s with input: %s", user_id, text)
        messages = agent.run_loop(text)

        if not messages:
            logger.warning("No response messages from agent for user %s", user_id)
            await update.message.reply_text(
                "I apologize, but I didn't receive a proper response. Please try again."
            )
            return

        response_sent = False
        for message in messages:
            if message.role == "assistant" and message.content:
                logger.info("Sending assistant message to user %s", user_id)
                # Split long messages
                chunks = split_long_message(message.content)
                for chunk in chunks:
                    await update.message.reply_text(chunk)
                response_sent = True
            elif message.role == "tool":
                # Format and split tool response
                logger.info("Sending tool result to user %s", user_id)
                # Get tool name from message
                tool_name = message.name if hasattr(message, "name") else "Unknown Tool"

                tool_response = "🔧 Tool: %s\n📋 Result: %s" % (
                    tool_name,
                    message.content,
                )
                chunks = split_long_message(tool_response)
                for chunk in chunks:
                    await update.message.reply_text(chunk)
                response_sent = True

        # If no response was sent, send a default message
        if not response_sent:
            logger.warning("No valid response messages to send for user %s", user_id)
            await update.message.reply_text(
                "I apologize, but I couldn't generate a proper response. Please try again."
            )

    except Exception as e:
        logger.error(
            "Error processing message for user %s: %s", user_id, str(e), exc_info=True
        )
        await update.message.reply_text(
            "Sorry, I encountered an unexpected error processing your message. Please try again."
        )
