"""Tests for the base context."""

from typing import Any, Dict, List

from swarmer.swarmer_types import AgentIdentity, Context, Tool


class TestContext(Context):
    """Test context for testing."""

    def __init__(self, context_id: str = "test_context") -> None:
        """Initialize test context."""
        self.id = context_id
        self.tools: List[Tool] = []
        self.instructions = "Test context instructions"

    def get_context(self, agent: AgentIdentity) -> Dict[str, Any]:
        """Get context."""
        return {
            "message": "Test context",
            "tools": [tool.__name__ for tool in self.tools],
        }

    def get_context_instructions(self, agent: AgentIdentity) -> str:
        """Get context instructions."""
        return self.instructions

    def serialize(self) -> dict:
        """Serialize context."""
        return {"id": self.id}

    def deserialize(self, state: dict, agent_identity: AgentIdentity) -> None:
        """Deserialize context."""
        self.id = state["id"]


class Context1(Context):
    """First test context."""

    def __init__(self, context_id: str) -> None:
        """Initialize test context."""
        self.id = context_id
        self.tools: List[Tool] = []
        self.instructions = "Context1 instructions"

    def get_context(self, agent: AgentIdentity) -> Dict[str, Any]:
        """Get context."""
        return {"message": "Context1", "tools": [tool.__name__ for tool in self.tools]}

    def get_context_instructions(self, agent: AgentIdentity) -> str:
        """Get context instructions."""
        return self.instructions

    def serialize(self) -> dict:
        """Serialize context."""
        return {"id": self.id}

    def deserialize(self, state: dict, agent_identity: AgentIdentity) -> None:
        """Deserialize context."""
        self.id = state["id"]


class Context2(Context):
    """Second test context."""

    def __init__(self, context_id: str) -> None:
        """Initialize test context."""
        self.id = context_id
        self.tools: List[Tool] = []
        self.instructions = "Context2 instructions"

    def get_context(self, agent: AgentIdentity) -> Dict[str, Any]:
        """Get context."""
        return {"message": "Context2", "tools": [tool.__name__ for tool in self.tools]}

    def get_context_instructions(self, agent: AgentIdentity) -> str:
        """Get context instructions."""
        return self.instructions

    def serialize(self) -> dict:
        """Serialize context."""
        return {"id": self.id}

    def deserialize(self, state: dict, agent_identity: AgentIdentity) -> None:
        """Deserialize context."""
        self.id = state["id"]


def test_context_creation() -> None:
    """Test context creation."""
    context = TestContext()
    assert context.id == "test_context"
    assert context.tools == []


def test_context_processing() -> None:
    """Test context processing."""
    context = TestContext()
    agent_id = AgentIdentity("test_agent", "test_user")
    assert context.get_context(agent_id) == {"message": "Test context", "tools": []}
    instr = context.get_context_instructions(agent_id)
    assert instr == "Test context instructions"


def test_context_with_agent() -> None:
    """Test context with agent."""
    context = TestContext()
    agent_id = AgentIdentity("test_agent", "test_user")
    assert context.serialize() == {"id": context.id}
    context.deserialize({"id": "new-id"}, agent_id)
    assert context.id == "new-id"


def test_multiple_contexts() -> None:
    """Test multiple contexts."""
    c1 = Context1("context1")
    c2 = Context2("context2")
    agent_id = AgentIdentity("test_agent", "test_user")

    assert c1.id != c2.id
    assert c1.get_context(agent_id) == {"message": "Context1", "tools": []}
    assert c2.get_context(agent_id) == {"message": "Context2", "tools": []}
    assert c1.get_context_instructions(agent_id) == "Context1 instructions"
    assert c2.get_context_instructions(agent_id) == "Context2 instructions"


def test_simple_context() -> None:
    """Test simple context functionality."""
    context = TestContext()
    agent = AgentIdentity("test_agent", "test_user")

    assert context.get_context_instructions(agent) == "Test context instructions"
    assert context.get_context(agent) == {"message": "Test context", "tools": []}
    assert len(context.tools) == 0


def test_tool_context() -> None:
    """Test context with a single tool."""
    context = TestContext()
    agent = AgentIdentity("test_agent", "test_user")

    assert context.get_context_instructions(agent) == "Test context instructions"
    assert context.get_context(agent) == {"message": "Test context", "tools": []}
    assert len(context.tools) == 0


def test_multi_tool_context() -> None:
    """Test context with multiple tools."""
    context = TestContext()
    agent = AgentIdentity("test_agent", "test_user")

    assert context.get_context_instructions(agent) == "Test context instructions"
    assert context.get_context(agent) == {"message": "Test context", "tools": []}
    assert len(context.tools) == 0
