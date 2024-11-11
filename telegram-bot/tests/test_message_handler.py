import pytest
from datetime import datetime, timedelta
from telegram import error as telegram_error
from telegram_bot.bot_interface.handlers.message_handler import handle_message, check_rate_limit, user_message_counts
from unittest.mock import AsyncMock

@pytest.mark.asyncio
async def test_handle_empty_message(mock_update, mock_context):
    # Arrange
    update = mock_update("")
    user_message_counts.clear()
    
    # Act
    await handle_message(update, mock_context)
    
    # Assert
    update.message.reply_text.assert_called_once_with("Please send a text message.")

@pytest.mark.asyncio
async def test_handle_rate_limit_exceeded(mock_update, mock_context):
    # Arrange
    update = mock_update("Test message")
    user_id = update.effective_user.id
    user_message_counts.clear()
    
    # Fill up rate limit
    current_time = datetime.now()
    user_message_counts[user_id] = [
        current_time - timedelta(seconds=1) 
        for _ in range(5)
    ]
    
    # Act
    await handle_message(update, mock_context)
    
    # Assert
    update.message.reply_text.assert_called_once_with(
        "⚠️ Rate limit exceeded. Please wait before sending more messages."
    )

def test_check_rate_limit():
    # Arrange
    user_id = 12345
    user_message_counts.clear()
    
    # Act & Assert
    # Should allow 5 messages
    for _ in range(5):
        assert check_rate_limit(user_id) is True
    
    # Should reject 6th message
    assert check_rate_limit(user_id) is False
    
    # Clean up
    user_message_counts.clear()