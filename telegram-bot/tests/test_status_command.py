"""Tests for the status command functionality."""

import pytest

from telegram_bot.bot_interface.commands.status import (
    MESSAGE_RATE_LIMIT,
    RATE_LIMIT_PERIOD,
    status_command,
)


@pytest.mark.asyncio
async def test_status_command(mock_update, mock_context):
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
async def test_status_command_rate_limit_values(mock_update, mock_context):
    """Test that status command correctly displays rate limit values."""
    # Arrange
    update = mock_update("/status")

    # Act
    await status_command(update, mock_context)

    # Assert
    args = update.message.reply_text.call_args
    message_text = args[0][0]

    # Verify the exact rate limit values are displayed
    expected_text = f"🕒 Current rate limit: {MESSAGE_RATE_LIMIT} messages per {RATE_LIMIT_PERIOD} seconds"
    assert expected_text in message_text
