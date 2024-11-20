"""Tests for the status command functionality."""

from unittest.mock import MagicMock

import pytest

from telegram_bot.bot_interface.commands.status import (
    MESSAGE_RATE_LIMIT,
    RATE_LIMIT_PERIOD,
    status_command,
)


@pytest.mark.asyncio
async def test_status_command(
    mock_update: MagicMock,
    mock_context: MagicMock,
) -> None:
    """Test the basic functionality of the status command."""
    # Arrange
    update = mock_update("/status")

    # Act
    await status_command(update, mock_context)

    # Assert
    update.message.reply_text.assert_called_once()
    args = update.message.reply_text.call_args
    message_text = args[0][0]

    # Check all required components are in the status message
    assert "Bot Status" in message_text
    assert "✅ Bot is running" in message_text
    assert f"Current rate limit: {MESSAGE_RATE_LIMIT}" in message_text
    assert f"{RATE_LIMIT_PERIOD} seconds" in message_text


@pytest.mark.asyncio
async def test_status_command_rate_limit_values(
    mock_update: MagicMock,
    mock_context: MagicMock,
) -> None:
    """Test that status command correctly displays rate limit values."""
    # Arrange
    update = mock_update("/status")

    # Act
    await status_command(update, mock_context)

    # Assert
    args = update.message.reply_text.call_args
    message_text = args[0][0]
    assert str(MESSAGE_RATE_LIMIT) in message_text
    assert str(RATE_LIMIT_PERIOD) in message_text
