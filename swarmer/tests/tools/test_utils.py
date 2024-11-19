"""Tests for the tools utilities."""

from swarmer.tools.types import ToolResponse
from swarmer.tools.utils import tool


def test_tool_decorator() -> None:
    """Test that the tool decorator adds the expected attributes."""

    @tool
    def sample_tool(agent_identity: str, input_text: str) -> str:
        """Run a sample tool for testing."""
        return f"Tool processed: {input_text}"

    assert hasattr(sample_tool, "__tool_schema__")
    assert hasattr(sample_tool, "__tool_doc__")

    result = sample_tool("test_agent", "hello")
    assert isinstance(result, ToolResponse)
    assert result.content == "Tool processed: hello"


def test_tool_validation() -> None:
    """Verify that the tool decorator validates input correctly."""

    @tool
    def invalid_tool(agent_identity: str) -> str:
        """Define an invalid tool with no additional parameters."""
        return "This should fail"

    schema = invalid_tool.__tool_schema__
    assert isinstance(schema, dict)
    assert "type" in schema
    assert "function" in schema
    assert "name" in schema["function"]
    assert "description" in schema["function"]
    assert "parameters" in schema["function"]


def test_tool_return_type() -> None:
    """Verify that the tool decorator validates return types correctly."""

    @tool
    def valid_tool(agent_identity: str) -> str:
        """Define a valid tool with string return type."""
        return "Valid return type"

    result = valid_tool("test_agent")
    assert isinstance(result, ToolResponse)
    assert isinstance(result.content, str)


def test_tool_documentation() -> None:
    """Verify that the tool decorator preserves documentation correctly."""

    @tool
    def documented_tool(agent_identity: str) -> str:
        """Define a documented tool."""
        return "Documentation preserved"

    assert documented_tool.__tool_doc__ == "Define a documented tool."
