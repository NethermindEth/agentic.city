import hashlib
import inspect
import json
from typing import Any, cast, List, Optional, Tuple, Protocol, TypeVar, runtime_checkable, Union, Dict, Callable
from functools import wraps, update_wrapper

from swarmer.tools.types import Tool, ToolResponse, ToolableType
from swarmer.tools.dependencies import ensure_dependencies, ToolFunction

T_co = TypeVar('T_co', covariant=True)

@runtime_checkable
class WrappedTool(Tool, Protocol[T_co]):
    __original_func__: ToolableType
    __tool_dependencies__: List[tuple[str, Optional[str]]]

def function_to_schema(func: ToolableType, name: str) -> dict:
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
    """Decorator that adds a schema property to a function based on its type hints.
    
    The schema property contains the OpenAI function calling schema for the decorated function.
    The decorator also handles any dependencies specified by the @requires decorator and
    wraps the response in a ToolResponse object if needed.
    
    Args:
        func: The function to decorate
        
    Returns:
        The decorated function with an added schema property
    """
    def wrapper(*args: Any, **kwargs: Any) -> ToolResponse:
        # Ensure dependencies are installed
        if hasattr(func, '__tool_dependencies__'):
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
    if hasattr(func, '__tool_dependencies__'):
        wrapper.__tool_dependencies__ = func.__tool_dependencies__  # type: ignore
    
    return cast(Tool, wrapper)
