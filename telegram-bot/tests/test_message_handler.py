"""Tests for the message handler functionality."""

from datetime import datetime, timedelta
from unittest.mock import MagicMock

import pytest
from telegram.ext import ContextTypes

from telegram_bot.bot_interface.handlers.message_handler import (
    _user_messages as user_message_counts,
)
from telegram_bot.bot_interface.handlers.message_handler import (
    check_rate_limit,
    handle_message,
)


@pytest.mark.asyncio
async def test_handle_empty_message(
    mock_update: MagicMock,
    mock_context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Test handling of empty messages."""
    # Arrange
    update = mock_update("")
    user_message_counts.clear()

    # Act
    await handle_message(update, mock_context)

    # Assert
    update.message.reply_text.assert_called_once_with("Please send a text message.")


@pytest.mark.asyncio
async def test_handle_rate_limit_exceeded(
    mock_update: MagicMock,
    mock_context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Test behavior when user exceeds message rate limit."""
    # Arrange
    update = mock_update("Test message")
    user_id = update.effective_user.id
    user_message_counts.clear()

    # Fill up rate limit
    current_time = datetime.now()
    user_message_counts[user_id] = [
        current_time - timedelta(seconds=1) for _ in range(5)
    ]

    # Act
    await handle_message(update, mock_context)

    # Assert
    update.message.reply_text.assert_called_once_with(
        "⚠️ Rate limit exceeded. Please wait before sending more messages."
    )


def test_check_rate_limit() -> None:
    """Test the rate limiting functionality."""
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
