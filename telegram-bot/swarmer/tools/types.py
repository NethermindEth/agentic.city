"""Type definitions for the tool system."""

from typing import Any, Callable, Optional, Protocol, Union, runtime_checkable

@runtime_checkable
class Tool(Protocol):
    """Represents a function that an agent can use to affect its environment."""
    __name__: str
    __tool_doc__: str
    __tool_schema__: dict

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        ...

class ToolResponse:
    """Response from a tool execution."""
    def __init__(self, summary: str, content: Any, error: Optional[str] = None):
        self.summary = summary  # Short summary for immediate display
        self.content = content  # Full content for LLM consumption
        self.error = error     # Error message if any

    def to_dict(self) -> dict:
        """Convert to dictionary representation."""
        return {
            "summary": self.summary,
            "content": self.content,
            "error": self.error
        }

    def __str__(self) -> str:
        if self.error:
            return f"Error: {self.error}"
        return self.summary

# Update ToolableType to accept both str and ToolResponse return types
ToolableType = Callable[..., Union[str, ToolResponse]]
