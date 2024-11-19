import importlib
import subprocess
import sys
from functools import wraps
from typing import cast, List, Optional, Union, Dict, Any, Callable, TypeVar, Protocol
from typing_extensions import runtime_checkable

T_co = TypeVar('T_co', covariant=True)

@runtime_checkable
class ToolFunction(Protocol[T_co]):
    __tool_dependencies__: List[tuple[str, Optional[str]]]
    def __call__(self, *args: Any, **kwargs: Any) -> T_co: ...

def requires(*packages: Union[str, Dict[str, str]]) -> Callable[[Callable[..., T_co]], ToolFunction[T_co]]:
    """Decorator to specify package dependencies for a tool.
    
    Args:
        *packages: Package names as strings (for latest version) or dicts with name and version
                  e.g. @requires('requests', {'numpy': '>=1.20.0'})
    """
    def decorator(func: Callable[..., T_co]) -> ToolFunction[T_co]:
        # Create a new list to store dependencies
        dependencies: List[tuple[str, Optional[str]]] = []
        
        # Process package requirements
        for package in packages:
            if isinstance(package, str):
                dependencies.append((package, None))
            elif isinstance(package, dict):
                for name, version in package.items():
                    dependencies.append((name, version))
        
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T_co:
            # Ensure dependencies are installed before running
            ensure_dependencies(dependencies)
            return func(*args, **kwargs)
        
        # Add dependencies to wrapper function
        wrapper_with_deps = cast(ToolFunction[T_co], wrapper)
        wrapper_with_deps.__tool_dependencies__ = dependencies
        return wrapper_with_deps
        
    return decorator

def ensure_dependencies(dependencies: List[tuple[str, Optional[str]]]) -> None:
    """Ensure all required packages are installed.
    
    Args:
        dependencies: List of (package_name, version_spec) tuples
    """
    missing = []
    for package, version in dependencies:
        spec = f"{package}{version if version else ''}"
        try:
            importlib.import_module(package.replace('-', '_'))
        except ImportError:
            missing.append(spec)
    
    if missing:
        try:
            subprocess.check_call([
                sys.executable, "-m", "pip", "install", "--quiet", *missing
            ])
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Failed to install dependencies: {e}")
