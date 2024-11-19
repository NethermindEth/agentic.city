import os
import importlib.util
import sys
from typing import Optional, List
from uuid import uuid4
import ast
from pathlib import Path
import logging

from swarmer.tools.utils import tool, ToolResponse
from swarmer.swarmer_types import AgentIdentity, Context, Tool
from swarmer.globals.agent_registry import agent_registry

class ToolCreationContext(Context):
    """Context for creating and managing dynamic tools."""
    
    tools: List[Tool] = []

    def __init__(self) -> None:
        self.tools.extend([
            self.create_tool,
            self.list_tools,
            self.remove_tool,
            self.update_tool
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

        If a tool fails to execute, attempt to fix it by rewriting the tool or creating a new one.
        
        When creating tools:
        
        1. Each tool must use the @tool decorator
        2. Specify dependencies using the @requires decorator before @tool:
           - For latest version: @requires('package_name')
           - For specific version: @requires({'package_name': '>=1.0.0'})
           - For multiple packages: @requires('pkg1', {'pkg2': '==2.1.0'})
        3. Dependencies will be automatically installed when the tool is used
        4. Import statements should be inside the function to ensure dependencies are installed first
        5. Tools must include proper type hints
        6. Tools must have descriptive docstrings
        7. Tools must return a ToolResponse object or a tuple of (summary, content):
           - ToolResponse(summary="User-friendly message", content="Detailed result for LLM", error=None)
           - Or return (summary, content) which will be automatically wrapped
           - Or return a single value which will be used for both summary and content
        8. Tools must take agent_identity as their first parameter
        9. Make sure tools provide both user-friendly summaries and detailed content for the LLM
        10. Handle errors appropriately - they will be automatically captured and formatted

        Example tool creation:
        ```python
        from swarmer.tools.utils import tool, ToolResponse
        from swarmer.tools.dependencies import requires
        from swarmer.swarmer_types import AgentIdentity
        
        @requires('requests')
        @tool
        def get_weather(agent_identity: AgentIdentity, city: str) -> ToolResponse:
            '''Get the current weather for a city.
            
            Args:
                agent_identity: The identity of the agent making the request
                city: The name of the city to get weather for
                
            Returns:
                ToolResponse with user-friendly summary and detailed weather data
            '''
            import requests
            
            response = requests.get(f'http://api.openweathermap.org/data/2.5/weather?q={city}&appid=YOUR_API_KEY')
            data = response.json()
            
            # Create user-friendly summary
            summary = f"Current weather in {city}: {data['weather'][0]['description']}, {data['main']['temp']}°K"
            
            # Return both summary and full data
            return ToolResponse(
                summary=summary,
                content=data,
                error=None
            )
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
    ) -> ToolResponse:
        """Create a new tool from Python code.
        
        Args:
            agent_identity: The agent creating the tool
            name: Name for the tool file (without .py)
            code: Python code defining the tool
            
        Returns:
            ToolResponse containing status message and detailed information
        """
        logger = logging.getLogger(__name__)
        logger.info(f"Creating tool '{name}' for agent {agent_identity.id}")
        
        if not self.validate_tool_code(code):
            error = "Invalid tool code. Must use @tool decorator and avoid unsafe operations."
            logger.error(f"Invalid tool code for '{name}': {error}")
            return ToolResponse(
                summary=error,
                content={"status": "error", "message": error},
                error=error
            )
            
        agent_dir = self.get_agent_tools_dir(agent_identity.id)
        file_path = agent_dir / f"{name}.py"
        logger.info(f"Writing tool to {file_path}")
        
        # Add necessary imports
        final_code = (
            "from swarmer.tools.utils import tool, ToolResponse\n"
            "from swarmer.tools.dependencies import requires\n"
            "from swarmer.swarmer_types import AgentIdentity\n\n"
        ) + code
        
        try:
            # Save tool file
            with open(file_path, "w") as f:
                f.write(final_code)
            logger.info(f"Successfully wrote tool file {file_path}")
            
            # Load the tool
            try:
                self.load_tool(name, agent_identity)
                logger.info(f"Successfully loaded tool '{name}'")
                success_msg = f"Tool '{name}' created and loaded successfully"
                return ToolResponse(
                    summary=success_msg,
                    content={"status": "success", "message": success_msg, "code": code},
                    error=None
                )
            except Exception as e:
                error_msg = f"Failed to load tool: {str(e)}"
                logger.error(f"Failed to load tool '{name}': {str(e)}", exc_info=True)
                if file_path.exists():
                    file_path.unlink()  # Remove file if loading fails
                return ToolResponse(
                    summary=error_msg,
                    content={"status": "error", "message": error_msg, "exception": str(e)},
                    error=error_msg
                )
        except Exception as e:
            error_msg = f"Failed to create tool file: {str(e)}"
            logger.error(f"Failed to write tool file '{name}': {str(e)}", exc_info=True)
            return ToolResponse(
                summary=error_msg,
                content={"status": "error", "message": error_msg, "exception": str(e)},
                error=error_msg
            )

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
    ) -> ToolResponse:
        """List all available custom tools.
        
        Args:
            agent_identity: The agent requesting the list
            
        Returns:
            ToolResponse containing list of available tools
        """
        tools = self.list_available_tools(agent_identity.id)
        if not tools:
            return ToolResponse(
                summary="No custom tools available",
                content={"tools": []},
                error=None
            )
        
        summary = f"Available tools: {', '.join(tools)}"
        return ToolResponse(
            summary=summary,
            content={"tools": tools},
            error=None
        )

    @tool
    def remove_tool(
        self,
        agent_identity: AgentIdentity,
        name: str
    ) -> ToolResponse:
        """Remove a custom tool.
        
        Args:
            agent_identity: The agent removing the tool
            name: Name of the tool to remove
            
        Returns:
            ToolResponse containing status of the removal operation
        """
        agent_dir = self.get_agent_tools_dir(agent_identity.id)
        file_path = agent_dir / f"{name}.py"
        
        if not file_path.exists():
            error_msg = f"Tool '{name}' not found"
            return ToolResponse(
                summary=error_msg,
                content={"status": "error", "message": error_msg},
                error=error_msg
            )
            
        try:
            file_path.unlink()
            
            # Remove from sys.modules if loaded
            module_name = f"{agent_identity.id}.{name}"
            if module_name in sys.modules:
                del sys.modules[module_name]
                
            success_msg = f"Tool '{name}' removed successfully"
            return ToolResponse(
                summary=success_msg,
                content={"status": "success", "message": success_msg},
                error=None
            )
        except Exception as e:
            error_msg = f"Error removing tool '{name}': {str(e)}"
            return ToolResponse(
                summary=error_msg,
                content={"status": "error", "message": error_msg, "exception": str(e)},
                error=error_msg
            )

    @tool
    def update_tool(
        self,
        agent_identity: AgentIdentity,
        name: str,
        code: str
    ) -> ToolResponse:
        """Update an existing tool with new code.
        
        Args:
            agent_identity: The agent updating the tool
            name: Name of the tool to update (without .py)
            code: New Python code for the tool
            
        Returns:
            ToolResponse containing status of the update operation
        """
        logger = logging.getLogger(__name__)
        logger.info(f"Updating tool '{name}' for agent {agent_identity.id}")
        
        # Check if tool exists
        agent_dir = self.get_agent_tools_dir(agent_identity.id)
        file_path = agent_dir / f"{name}.py"
        if not file_path.exists():
            error_msg = f"Tool '{name}' not found"
            return ToolResponse(
                summary=error_msg,
                content={"status": "error", "message": error_msg},
                error=error_msg
            )
        
        if not self.validate_tool_code(code):
            error_msg = "Invalid tool code. Must use @tool decorator and avoid unsafe operations."
            logger.error(f"Invalid tool code for '{name}': {error_msg}")
            return ToolResponse(
                summary=error_msg,
                content={"status": "error", "message": error_msg},
                error=error_msg
            )
        
        # Add necessary imports
        final_code = (
            "from swarmer.tools.utils import tool, ToolResponse\n"
            "from swarmer.tools.dependencies import requires\n"
            "from swarmer.swarmer_types import AgentIdentity\n\n"
        ) + code
        
        try:
            # Get agent instance
            agent = agent_registry.get_agent(agent_identity)
            
            # Remove old tool from agent's tools
            if name in agent.tools:
                logger.info(f"Removing old tool: {name}")
                del agent.tools[name]
            
            # Remove from sys.modules if loaded
            module_name = f"{agent_identity.id}.{name}"
            if module_name in sys.modules:
                logger.info(f"Removing module from sys.modules: {module_name}")
                del sys.modules[module_name]
            
            # Save updated tool file
            with open(file_path, "w") as f:
                f.write(final_code)
            logger.info(f"Successfully wrote updated tool file {file_path}")
            
            # Reload the tool
            try:
                self.load_tool(name, agent_identity)
                logger.info(f"Successfully reloaded tool '{name}'")
                success_msg = f"Tool '{name}' updated and reloaded successfully"
                return ToolResponse(
                    summary=success_msg,
                    content={"status": "success", "message": success_msg},
                    error=None
                )
            except Exception as e:
                error_msg = f"Failed to reload tool: {str(e)}"
                logger.error(f"Failed to reload tool '{name}': {str(e)}", exc_info=True)
                return ToolResponse(
                    summary=error_msg,
                    content={"status": "error", "message": error_msg, "exception": str(e)},
                    error=error_msg
                )
        except Exception as e:
            error_msg = f"Failed to update tool: {str(e)}"
            logger.error(f"Failed to update tool '{name}': {str(e)}", exc_info=True)
            return ToolResponse(
                summary=error_msg,
                content={"status": "error", "message": error_msg, "exception": str(e)},
                error=error_msg
            )

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