"""Test fixtures."""

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

    def get_context(self, agent: AgentIdentity) -> str:
        """Get context."""
        return "Mock context state"

    def get_context_instructions(self, agent: AgentIdentity) -> str:
        """Get context instructions."""
        return "Mock context instructions"

    def serialize(self) -> dict:
        """Serialize context."""
        return {"id": self.id}

    def deserialize(self, state: dict, agent_identity: AgentIdentity) -> None:
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
