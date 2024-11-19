"""Tests for the base context."""

from swarmer.swarmer_types import AgentIdentity, Context


class TestContext(Context):
    """Test context for testing."""

    def __init__(self, context_id: str = "test_context") -> None:
        """Initialize test context."""
        self.id = context_id
        self.tools = []
        self.instructions = "Test context instructions"

    def get_context(self, agent: AgentIdentity) -> str:
        """Get context."""
        return "Test context"

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
        self.tools = []
        self.instructions = "Context1 instructions"

    def get_context(self, agent: AgentIdentity) -> str:
        """Get context."""
        return "Context1"

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
        self.tools = []
        self.instructions = "Context2 instructions"

    def get_context(self, agent: AgentIdentity) -> str:
        """Get context."""
        return "Context2"

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
    agent_id = AgentIdentity(name="test", id="test-id")
    assert context.get_context(agent_id) == "Test context"
    instr = context.get_context_instructions(agent_id)
    assert instr == "Test context instructions"


def test_context_with_agent() -> None:
    """Test context with agent."""
    context = TestContext()
    agent_id = AgentIdentity(name="test", id="test-id")
    assert context.serialize() == {"id": context.id}
    context.deserialize({"id": "new-id"}, agent_id)
    assert context.id == "new-id"


def test_multiple_contexts() -> None:
    """Test multiple contexts."""
    c1 = Context1("context1")
    c2 = Context2("context2")
    agent_id = AgentIdentity(name="test", id="test-id")

    assert c1.id != c2.id
    assert c1.get_context(agent_id) == "Context1"
    assert c2.get_context(agent_id) == "Context2"
    assert c1.get_context_instructions(agent_id) == "Context1 instructions"
    assert c2.get_context_instructions(agent_id) == "Context2 instructions"
