"""Type definitions for the tool system."""

from typing import Any, Callable, Optional, Protocol, Union, runtime_checkable


@runtime_checkable
class Tool(Protocol):
    """Represents a function that an agent can use to affect its environment."""

    __name__: str
    __tool_doc__: str
    __tool_schema__: dict

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        """Execute the tool with the given arguments.

        Args:
            *args: Positional arguments for the tool.
            **kwargs: Keyword arguments for the tool.

        Returns:
            The result of executing the tool.
        """
        ...


class ToolResponse:
    """Response from a tool execution."""

    def __init__(self, summary: str, content: Any, error: Optional[str] = None):
        """Initialize a tool response.

        Args:
            summary: Short summary for immediate display.
            content: Full content for LLM consumption.
            error: Error message if any.
        """
        self.summary = summary  # Short summary for immediate display
        self.content = content  # Full content for LLM consumption
        self.error = error  # Error message if any

    def to_dict(self) -> dict:
        """Convert to dictionary representation."""
        return {"summary": self.summary, "content": self.content, "error": self.error}

    def __str__(self) -> str:
        """Return a string representation of the tool response.

        Returns:
            A string containing either the error message or the summary.
        """
        if self.error:
            return f"Error: {self.error}"
        return self.summary


# Update ToolableType to accept both str and ToolResponse return types
ToolableType = Callable[..., Union[str, ToolResponse]]
