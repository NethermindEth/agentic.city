import os
import importlib.util
import sys
from typing import Optional, List
from uuid import uuid4
import ast
from pathlib import Path

from swarmer.tools.utils import tool
from swarmer.types import AgentIdentity, Context, Tool
from swarmer.globals.agent_registry import agent_registry

class ToolCreationContext(Context):
    """Context for creating and managing dynamic tools."""
    
    tools: List[Tool] = []

    def __init__(self) -> None:
        self.tools.extend([
            self.create_tool,
            self.list_tools,
            self.remove_tool
        ])
        self.id = str(uuid4())
        self.base_tools_dir = Path(os.getenv("AGENT_TOOLS_DIRECTORY", "agent_tools"))
        self.base_tools_dir.mkdir(parents=True, exist_ok=True)

    def get_context_instructions(self, agent: AgentIdentity) -> Optional[str]:
        return """
        You can create new tools dynamically using Python code.
        You should do so anytime the user asks you to do something concrete or something
        out of your abilities as a language model. This can be fetching data, effecting some
        task in the realworld. etc. Proactively make these.
        
        
        When creating tools:
        
        1. Each tool must use the @tool decorator
        2. Tools must include proper type hints
        3. Tools must have descriptive docstrings
        4. Tools must return string results
        5. Tools must take agent_identity as their first parameter
        
        Example tool creation:
        ```python
        @tool
        def my_tool(agent_identity: AgentIdentity, param1: str) -> str:
            '''Tool description here'''
            return f"Result: {param1}"
        ```
        """

    def get_context(self, agent: AgentIdentity) -> Optional[str]:
        tools = self.list_available_tools(agent.id)
        if not tools:
            return None
        return f"Available custom tools: {', '.join(tools)}"

    def get_agent_tools_dir(self, agent_id: str) -> Path:
        """Get the tools directory for a specific agent."""
        agent_dir = self.base_tools_dir / agent_id
        agent_dir.mkdir(parents=True, exist_ok=True)
        return agent_dir

    def list_available_tools(self, agent_id: str) -> List[str]:
        """List all available custom tools for an agent."""
        tools = []
        agent_dir = self.get_agent_tools_dir(agent_id)
        for file in agent_dir.glob("*.py"):
            module_name = file.stem
            if module_name != "__init__":
                tools.append(module_name)
        return tools

    def validate_tool_code(self, code: str) -> bool:
        """Validate tool code for safety and correctness."""
        try:
            tree = ast.parse(code)
            
            # Check for tool decorator
            has_tool_decorator = False
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    for decorator in node.decorator_list:
                        if isinstance(decorator, ast.Name) and decorator.id == "tool":
                            has_tool_decorator = True
                            break
            
            if not has_tool_decorator:
                return False
                
            # Check for unsafe operations
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    if isinstance(node.func, ast.Name):
                        if node.func.id in ["eval", "exec", "compile"]:
                            return False
                        
            return True
            
        except SyntaxError:
            return False

    @tool
    def create_tool(
        self,
        agent_identity: AgentIdentity,
        name: str,
        code: str
    ) -> str:
        """Create a new tool from Python code.
        
        Args:
            agent_identity: The agent creating the tool
            name: Name for the tool file (without .py)
            code: Python code defining the tool
            
        Returns:
            Status message
        """
        if not self.validate_tool_code(code):
            return "Invalid tool code. Must use @tool decorator and avoid unsafe operations."
            
        agent_dir = self.get_agent_tools_dir(agent_identity.id)
        file_path = agent_dir / f"{name}.py"
        
        # Add necessary imports
        final_code = (
            "from swarmer.tools.utils import tool\n"
            "from swarmer.types import AgentIdentity\n\n"
        ) + code
        
        # Save tool file
        with open(file_path, "w") as f:
            f.write(final_code)
            
        # Load the tool
        try:
            self.load_tool(name, agent_identity)
            return f"Tool '{name}' created and loaded successfully"
        except Exception as e:
            file_path.unlink()  # Remove file if loading fails
            return f"Failed to load tool: {str(e)}"

    def load_tool(self, name: str, agent_identity: AgentIdentity) -> None:
        """Load a tool module and register it with the agent."""
        agent_dir = self.get_agent_tools_dir(agent_identity.id)
        file_path = agent_dir / f"{name}.py"
        
        # Import the module
        spec = importlib.util.spec_from_file_location(
            f"{agent_identity.id}.{name}", 
            file_path
        )
        if spec is None or spec.loader is None:
            raise ImportError(f"Could not load module spec for {name}")
            
        module = importlib.util.module_from_spec(spec)
        sys.modules[f"{agent_identity.id}.{name}"] = module
        spec.loader.exec_module(module)
        
        # Find and register tool functions
        agent = agent_registry.get_agent(agent_identity)
        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            if hasattr(attr, "__tool_schema__"):
                agent.register_tool(attr)

    @tool
    def list_tools(
        self,
        agent_identity: AgentIdentity
    ) -> str:
        """List all available custom tools.
        
        Args:
            agent_identity: The agent requesting the list
            
        Returns:
            List of available tools
        """
        tools = self.list_available_tools(agent_identity.id)
        if not tools:
            return "No custom tools available"
        return f"Available tools: {', '.join(tools)}"

    @tool
    def remove_tool(
        self,
        agent_identity: AgentIdentity,
        name: str
    ) -> str:
        """Remove a custom tool.
        
        Args:
            agent_identity: The agent removing the tool
            name: Name of the tool to remove
            
        Returns:
            Status message
        """
        agent_dir = self.get_agent_tools_dir(agent_identity.id)
        file_path = agent_dir / f"{name}.py"
        if not file_path.exists():
            return f"Tool '{name}' not found"
            
        file_path.unlink()
        
        # Remove from sys.modules if loaded
        module_name = f"{agent_identity.id}.{name}"
        if module_name in sys.modules:
            del sys.modules[module_name]
            
        return f"Tool '{name}' removed successfully"

    def serialize(self) -> dict:
        """Serialize context state"""
        return {
            "id": self.id
        }

    def deserialize(self, state: dict, agent_identity: AgentIdentity) -> None:
        """Load state into this context instance"""
        self.id = state["id"]
        
        # Reload all tools
        for tool_name in self.list_available_tools(agent_identity.id):
            try:
                self.load_tool(tool_name, agent_identity)
            except Exception:
                pass  # Skip failed tools 