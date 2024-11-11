import hashlib
import inspect
import json
from typing import Any, Callable, Union, get_type_hints, get_args, get_origin

from swarmer.instructions.instruction import Instruction
from swarmer.types import AgentIdentity, Tool
from swarmer.globals.agent_registry import agent_registry

def _get_type_schema(type_hint: Any) -> dict:
    """Convert Python type hints to JSON schema types."""
    # Handle None/NoneType
    if type_hint is type(None):
        return {"type": "null"}
    
    # Handle basic types
    basic_types = {
        str: {"type": "string"},
        int: {"type": "integer"},
        float: {"type": "number"},
        bool: {"type": "boolean"},
    }
    if type_hint in basic_types:
        return basic_types[type_hint]
    
    # Handle typing.Union and Optional (which is Union[T, None])
    origin = get_origin(type_hint)
    if origin is not None:
        args = get_args(type_hint)
        
        if origin == list:
            item_type = _get_type_schema(args[0]) if args else {"type": "string"}
            return {
                "type": "array",
                "items": item_type
            }
        elif origin == dict:
            return {
                "type": "object",
                "additionalProperties": True
            }
        # Handle Union types
        elif origin == Union:
            types = [_get_type_schema(arg)["type"] for arg in args if arg != type(None)]
            if len(types) == 1:
                return {"type": types[0]}
            return {"type": types}
    
    # Default to string for unknown types
    return {"type": "string"}

def function_to_schema(func, name) -> dict:
    """Convert a function to an OpenAI function schema."""
    try:
        signature = inspect.signature(func)
        type_hints = get_type_hints(func)
        
        # Skip the first parameter (usually self or agent_identity)
        parameters = {}
        for param in list(signature.parameters.values())[1:]:
            param_type = type_hints.get(param.name, str)
            param_schema = _get_type_schema(param_type)
            
            # Add description from docstring if available
            parameters[param.name] = param_schema
            
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
    except Exception as e:
        print(f"ERROR generating schema for {name}: {str(e)}")
        raise

def tool(func: Callable[[AgentIdentity, *tuple[Any, ...]], str]) -> Tool:
    """Decorator that adds a schema property to a function based on its type hints."""
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
        
    # Copy over function metadata
    wrapper.__doc__ = func.__doc__
    wrapper.__annotations__ = func.__annotations__
    wrapper.id = hashlib.sha256(inspect.getsource(func).encode()).hexdigest()
    
    # Create unique name
    wrapper.__name__ = func.__name__ + wrapper.id[:16]
    
    # Generate schema
    try:
        wrapper.schema = function_to_schema(func, wrapper.__name__)
    except Exception as e:
        print(f"ERROR creating tool schema for {func.__name__}: {str(e)}")
        raise

    return wrapper
