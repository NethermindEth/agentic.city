"""Test fixtures."""

from typing import Any, Dict

import pytest

from swarmer.agent import Agent
from swarmer.swarmer_types import AgentIdentity, Context


class MockContext(Context):
    """Mock context for testing."""

    def __init__(self) -> None:
        """Initialize mock context."""
        self.tools = []
        self.id = "mock-context-id"

    def process_message(self, message: str) -> str:
        """Process a message."""
        return f"Processed: {message}"

    def get_context(self, agent: AgentIdentity) -> Dict[str, Any]:
        """Get test context.

        Args:
            agent: The agent requesting context.

        Returns:
            Test context state.
        """
        return {
            "message": "Test context",
            "tools": [tool.__name__ for tool in self.tools],
        }

    def get_context_instructions(self, agent: AgentIdentity) -> str:
        """Get context instructions."""
        return "Mock context instructions"

    def serialize(self) -> Dict[str, Any]:
        """Serialize context."""
        return {"id": self.id}

    def deserialize(self, state: Dict[str, Any], agent_identity: AgentIdentity) -> None:
        """Deserialize context."""
        self.id = state["id"]


@pytest.fixture
def mock_context() -> MockContext:
    """Create a mock context."""
    return MockContext()


@pytest.fixture
def mock_agent() -> Agent:
    """Create a mock agent."""
    return Agent(name="test_agent", token_budget=1000, model="gpt-3.5-turbo")
