"""Pytest fixtures for Telegram bot testing."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from telegram import Chat, Message, Update, User


@pytest.fixture
def mock_bot():
    """Create a mock bot instance with async send_message capability."""
    bot = MagicMock()
    bot.send_message = AsyncMock()
    return bot


@pytest.fixture
def mock_message(mock_bot):
    """Create a mock message factory function.

    Args:
        mock_bot: The mock bot fixture.

    Returns:
        A function that creates mock messages with customizable text and user ID.
    """

    def _make_message(message_text: str = "", user_id: int = 123456789):
        user = User(id=user_id, is_bot=False, first_name="Test", last_name="User")
        chat = Chat(id=user_id, type="private")
        message = MagicMock(spec=Message)
        message.message_id = 1
        message.date = None
        message.chat = chat
        message.from_user = user
        message.text = message_text
        message.reply_text = AsyncMock()
        return message

    return _make_message


@pytest.fixture
def mock_update(mock_message):
    """Create a mock update factory function.

    Args:
        mock_message: The mock message fixture.

    Returns:
        A function that creates mock updates with customizable message text and user ID.
    """

    def _make_update(message_text: str = "", user_id: int = 123456789):
        message = mock_message(message_text, user_id)
        update = MagicMock(spec=Update)
        update.update_id = 1
        update.message = message
        update.effective_message = message
        update.effective_user = message.from_user
        update.effective_chat = message.chat
        return update

    return _make_update


@pytest.fixture
def mock_context(mock_bot):
    """Create a mock context with the mock bot instance.

    Args:
        mock_bot: The mock bot fixture.

    Returns:
        A mock context object with the bot attribute set.
    """
    context = MagicMock()
    context.bot = mock_bot
    return context
