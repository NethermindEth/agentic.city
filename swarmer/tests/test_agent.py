"""Tests for the agent module."""

from tests.conftest import MockContext

from swarmer.agent import Agent


def test_agent_creation() -> None:
    """Test agent creation."""
    agent = Agent(name="test_agent", token_budget=1000, model="gpt-3.5-turbo")
    assert agent.identity.name == "test_agent"
    assert agent.token_budget == 1000
    assert agent.model == "gpt-3.5-turbo"
    assert len(agent.contexts) == 0


def test_agent_with_context(mock_context: MockContext) -> None:
    """Test agent with context."""
    agent = Agent(name="test_agent", token_budget=1000, model="gpt-3.5-turbo")
    agent.register_context(mock_context)
    assert mock_context.id in agent.contexts


def test_agent_context_management(mock_context: MockContext) -> None:
    """Test agent context management."""
    agent = Agent(name="test_agent", token_budget=1000, model="gpt-3.5-turbo")

    # Test context registration
    agent.register_context(mock_context)
    assert mock_context.id in agent.contexts

    # Test context unregistration
    agent.unregister_context(mock_context.id)
    assert mock_context.id not in agent.contexts
