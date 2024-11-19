"""Utility functions and classes for Swarmer tools.

This module provides common utilities used across different tools, including
response handling, schema generation, and tool decorators.
"""

import inspect
from functools import update_wrapper
from typing import (
    Any,
    Callable,
    List,
    Optional,
    Protocol,
    TypeVar,
    Union,
    cast,
    runtime_checkable,
)

from swarmer.tools.dependencies import ensure_dependencies
from swarmer.tools.types import Tool, ToolableType, ToolResponse

T_co = TypeVar("T_co", covariant=True)


@runtime_checkable
class WrappedTool(Tool, Protocol[T_co]):
    """Protocol for a tool that has been wrapped by the tool decorator.

    This protocol defines the attributes that a tool must have after being
    wrapped by the tool decorator.

    Attributes:
        __original_func__: The original function that was wrapped.
        __tool_dependencies__: A list of dependencies required by the tool.
    """

    __original_func__: ToolableType
    __tool_dependencies__: List[tuple[str, Optional[str]]]


def function_to_schema(func: ToolableType, name: str) -> dict:
    """Convert a function's signature to a JSON schema.

    Args:
        func: The function to convert.
        name: The name of the function.

    Returns:
        A dictionary representing the function's JSON schema.
    """
    type_map = {
        str: "string",
        int: "integer",
        float: "number",
        bool: "boolean",
        list: "array",
        dict: "object",
        type(None): "null",
    }

    try:
        signature = inspect.signature(func)
    except ValueError as e:
        raise ValueError(
            f"Failed to get signature for function {func.__name__}: {str(e)}"
        )

    parameters = {}
    # We always skip the first param because it's either the self param or the agent_identity param
    # We skip the second param if the first param is self because self is always the first param for methods
    # This is hacky but for some reason inspect.ismethod is false at the time of the tool decorator
    skip_params = 2 if list(signature.parameters.values())[0].name == "self" else 1
    for param in list(signature.parameters.values())[skip_params:]:
        try:
            param_type = type_map.get(param.annotation, "string")
        except KeyError as e:
            raise KeyError(
                f"Unknown type annotation {param.annotation} for parameter {param.name}: {str(e)}"
            )
        parameters[param.name] = {"type": param_type}

    required = [
        param.name
        for param in list(signature.parameters.values())[1:]
        if param.default == inspect._empty
    ]

    return {
        "type": "function",
        "function": {
            "name": name,
            "description": (func.__doc__ or "").strip(),
            "parameters": {
                "type": "object",
                "properties": parameters,
                "required": required,
            },
        },
    }


def tool(func: Callable[..., Union[str, ToolResponse]]) -> Tool:
    """Convert a function into a Swarmer tool.

    This decorator processes the function's signature and docstring to create
    a proper Tool instance that can be used by agents.

    Args:
        func: The function to convert into a tool.

    Returns:
        A Tool instance wrapping the original function.
    """

    def wrapper(*args: Any, **kwargs: Any) -> ToolResponse:
        # Ensure dependencies are installed
        if hasattr(func, "__tool_dependencies__"):
            ensure_dependencies(func.__tool_dependencies__)

        # Execute the tool function
        result = func(*args, **kwargs)

        # Return if already a ToolResponse
        if isinstance(result, ToolResponse):
            return result

        # Convert to string and create summary
        result_str = str(result)
        summary = result_str[:100] + "..." if len(result_str) > 100 else result_str

        return ToolResponse(summary=summary, content=result)

    # Generate the schema for the function
    schema = function_to_schema(func, func.__name__)

    # Copy over function attributes
    update_wrapper(wrapper, func)

    # Add tool-specific attributes
    wrapper.__tool_doc__ = func.__doc__ or ""  # type: ignore
    wrapper.__tool_schema__ = schema  # type: ignore
    if hasattr(func, "__tool_dependencies__"):
        wrapper.__tool_dependencies__ = func.__tool_dependencies__  # type: ignore

    return cast(Tool, wrapper)
