"""Utility functions for the Swarmer framework."""

from typing import Any, Callable, Dict, Type

from swarmer.swarmer_types import Context


def create_context(context_class: Type[Context], **kwargs: Any) -> Context:
    """Create a new context instance.

    Args:
        context_class: The context class to instantiate.
        **kwargs: Additional arguments to pass to the context constructor.

    Returns:
        A new instance of the specified context class.
    """
    return context_class(**kwargs)


def create_tool(
    func: Callable[..., Any], doc: str, schema: Dict[str, Any]
) -> Callable[..., Any]:
    """Create a new tool from a function.

    Args:
        func: The function to convert into a tool.
        doc: Documentation for the tool.
        schema: JSON schema for the tool.

    Returns:
        A callable tool function.
    """
    func.__tool_doc__ = doc  # type: ignore
    func.__tool_schema__ = schema  # type: ignore
    return func
