import hashlib
import inspect
import json
from typing import Any, cast

from swarmer.types import Tool, ToolableType

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

def tool(
    func: ToolableType
) -> Tool:
    """Decorator that adds a schema property to a function based on its type hints.
    
    The schema property contains the OpenAI function calling schema for the decorated function.
    
    Args:
        func: The function to decorate
        
    Returns:
        The decorated function with an added schema property
    """

    def _wrapper(*args: Any, **kwargs: Any) -> str:
        return func(*args, **kwargs)

    wrapper = cast(Tool, _wrapper)
    __tool_id__ = hashlib.sha256(inspect.getsource(wrapper).encode()).hexdigest()
    # Copy over function metadata
    wrapper.__doc__ = func.__doc__
    wrapper.__name__ = func.__name__ + __tool_id__[:16]
    wrapper.__tool_schema__ = function_to_schema(func, wrapper.__name__)

    return wrapper
