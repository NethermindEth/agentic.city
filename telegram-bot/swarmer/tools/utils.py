import hashlib
import inspect
import json
from typing import Any, Callable

from swarmer.instructions.instruction import Instruction
from swarmer.types import AgentIdentity, Tool
from swarmer.globals.agent_registry import agent_registry

def _function_to_schema(func, name) -> dict:
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
    for param in list(signature.parameters.values())[1:]:
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

def function_to_schema(func, name) -> str:
    return json.dumps(_function_to_schema(func, name), indent=2)

def tool(func: Callable[[AgentIdentity, *tuple[Any, ...]], str]) -> Tool:
    """Decorator that adds a schema property to a function based on its type hints.
    
    The schema property contains the OpenAI function calling schema for the decorated function.
    
    Args:
        func: The function to decorate
        
    Returns:
        The decorated function with an added schema property
    """
    # Create a wrapper that maintains the original function attributes
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
        
    # Copy over function metadata
    wrapper.__doc__ = func.__doc__
    wrapper.__annotations__ = func.__annotations__
    wrapper.id = hashlib.sha256(inspect.getsource(func).encode()).hexdigest()

    # Append the id to the name to make it unique
    wrapper.__name__ = func.__name__ + wrapper.id[:16]
    wrapper.schema = _function_to_schema(func, wrapper.__name__)

    return wrapper
