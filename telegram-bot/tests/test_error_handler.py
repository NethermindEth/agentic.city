"""Tests for the error handler functionality."""

from unittest.mock import MagicMock

import pytest

from telegram_bot.bot_interface.handlers.error_handler import error_handler


@pytest.mark.asyncio
async def test_error_handler_generic_error(
    mock_update: MagicMock,
    mock_context: MagicMock,
) -> None:
    """Test the error handler's response to a generic exception."""
    # Arrange
    update = mock_update()
    mock_context.error = Exception("Test error")

    # Act
    await error_handler(update, mock_context)

    # Assert
    mock_context.bot.send_message.assert_not_called()  # Because we use reply_text instead
    assert update.effective_message.reply_text.called
    args = update.effective_message.reply_text.call_args
    assert "Sorry, I encountered an error" in args[0][0]


@pytest.mark.asyncio
async def test_error_handler_network_error(
    mock_update: MagicMock,
    mock_context: MagicMock,
) -> None:
    """Test the error handler's response to a network error."""
    # Arrange
    update = mock_update()
    mock_context.error = ConnectionError("Network error")

    # Act
    await error_handler(update, mock_context)

    # Assert
    mock_context.bot.send_message.assert_not_called()  # Because we use reply_text instead
    assert update.effective_message.reply_text.called
    args = update.effective_message.reply_text.call_args
    assert "Sorry, I encountered an error" in args[0][0]
