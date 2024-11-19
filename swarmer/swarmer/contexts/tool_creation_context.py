"""Module for dynamic tool creation and management."""

import ast
import importlib.util
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, List
from uuid import uuid4

from swarmer.globals.agent_registry import agent_registry
from swarmer.swarmer_types import AgentIdentity, Context, Tool
from swarmer.tools.utils import ToolResponse, tool


class ToolCreationContext(Context):
    """Context for dynamically creating and managing agent tools.

    This context enables agents to create, modify, and manage their own tools
    at runtime, allowing for dynamic expansion of capabilities.
    """

    tools: List[Tool] = []

    def __init__(self) -> None:
        """Initialize tool creation context with tool management capabilities."""
        self.tools.extend(
            [self.create_tool, self.list_tools, self.remove_tool, self.update_tool]
        )
        self.id = str(uuid4())
        self.base_tools_dir = Path(os.getenv("AGENT_TOOLS_DIRECTORY", "agent_tools"))
        self.base_tools_dir.mkdir(parents=True, exist_ok=True)

    def get_context_instructions(self, agent: AgentIdentity) -> str:
        """Get instructions for using the tool creation context.

        Args:
            agent: The agent requesting instructions.

        Returns:
            Instructions for using tool creation capabilities.
        """
        return """
        Tool Creation Context Instructions:
        - Use create_tool to define new tools
        - Use remove_tool to delete existing tools
        - Use list_tools to see available tools
        """

    def get_context(self, agent: AgentIdentity) -> Dict[str, Any]:
        """Get the current tool creation context.

        Args:
            agent: The agent requesting context.

        Returns:
            Current tool state and available tools.
        """
        tools = self.list_available_tools(agent.id)
        if not tools:
            return {"available_tools": [], "created_tools": [], "tools": []}
        return {
            "available_tools": tools,
            "created_tools": tools,
            "tools": tools,
        }

    def get_agent_tools_dir(self, agent_id: str) -> Path:
        """Get the tools directory for a specific agent.

        Args:
            agent_id: The ID of the agent.

        Returns:
            The directory path for the agent's tools.
        """
        agent_dir = self.base_tools_dir / agent_id
        agent_dir.mkdir(parents=True, exist_ok=True)
        return agent_dir

    def list_available_tools(self, agent_id: str) -> List[str]:
        """List all available custom tools for an agent.

        Args:
            agent_id: The ID of the agent.

        Returns:
            A list of available tool names.
        """
        tools = []
        agent_dir = self.get_agent_tools_dir(agent_id)
        for file in agent_dir.glob("*.py"):
            module_name = file.stem
            if module_name != "__init__":
                tools.append(module_name)
        return tools

    def validate_tool_code(self, code: str) -> bool:
        """Validate tool code for safety and correctness.

        Args:
            code: The tool code to validate.

        Returns:
            True if the code is valid, False otherwise.
        """
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
        self, agent_identity: AgentIdentity, name: str, code: str
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
                error=error,
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
                    error=None,
                )
            except Exception as e:
                error_msg = f"Failed to load tool: {str(e)}"
                logger.error(f"Failed to load tool '{name}': {str(e)}", exc_info=True)
                if file_path.exists():
                    file_path.unlink()  # Remove file if loading fails
                return ToolResponse(
                    summary=error_msg,
                    content={
                        "status": "error",
                        "message": error_msg,
                        "exception": str(e),
                    },
                    error=error_msg,
                )
        except Exception as e:
            error_msg = f"Failed to create tool file: {str(e)}"
            logger.error(f"Failed to write tool file '{name}': {str(e)}", exc_info=True)
            return ToolResponse(
                summary=error_msg,
                content={"status": "error", "message": error_msg, "exception": str(e)},
                error=error_msg,
            )

    def load_tool(self, name: str, agent_identity: AgentIdentity) -> None:
        """Load a tool module and register it with the agent.

        Args:
            name: The name of the tool to load
            agent_identity: The identity of the agent loading the tool
        """
        agent_dir = self.get_agent_tools_dir(agent_identity.id)
        file_path = agent_dir / f"{name}.py"

        # Import the module
        spec = importlib.util.spec_from_file_location(
            f"{agent_identity.id}.{name}", file_path
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
    def list_tools(self, agent_identity: AgentIdentity) -> ToolResponse:
        """List all available custom tools.

        Args:
            agent_identity: The agent requesting the list

        Returns:
            ToolResponse containing list of available tools
        """
        tools = self.list_available_tools(agent_identity.id)
        if not tools:
            return ToolResponse(
                summary="No custom tools available", content={"tools": []}, error=None
            )

        summary = f"Available tools: {', '.join(tools)}"
        return ToolResponse(summary=summary, content={"tools": tools}, error=None)

    @tool
    def remove_tool(self, agent_identity: AgentIdentity, name: str) -> ToolResponse:
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
                error=error_msg,
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
                error=None,
            )
        except Exception as e:
            error_msg = f"Error removing tool '{name}': {str(e)}"
            return ToolResponse(
                summary=error_msg,
                content={"status": "error", "message": error_msg, "exception": str(e)},
                error=error_msg,
            )

    @tool
    def update_tool(
        self, agent_identity: AgentIdentity, name: str, code: str
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
                error=error_msg,
            )

        if not self.validate_tool_code(code):
            error_msg = "Invalid tool code. Must use @tool decorator and avoid unsafe operations."
            logger.error(f"Invalid tool code for '{name}': {error_msg}")
            return ToolResponse(
                summary=error_msg,
                content={"status": "error", "message": error_msg},
                error=error_msg,
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
                    error=None,
                )
            except Exception as e:
                error_msg = f"Failed to reload tool: {str(e)}"
                logger.error(f"Failed to reload tool '{name}': {str(e)}", exc_info=True)
                return ToolResponse(
                    summary=error_msg,
                    content={
                        "status": "error",
                        "message": error_msg,
                        "exception": str(e),
                    },
                    error=error_msg,
                )
        except Exception as e:
            error_msg = f"Failed to update tool: {str(e)}"
            logger.error(f"Failed to update tool '{name}': {str(e)}", exc_info=True)
            return ToolResponse(
                summary=error_msg,
                content={"status": "error", "message": error_msg, "exception": str(e)},
                error=error_msg,
            )

    def serialize(self) -> Dict:
        """Serialize the tool creation context state to a dictionary.

        Returns:
            A dictionary containing the serialized state.
        """
        return {
            "id": self.id,
            "tools": list(self.tools),
        }

    def deserialize(self, state: Dict, agent_identity: AgentIdentity) -> None:
        """Load a serialized state into the tool creation context.

        Args:
            state: The serialized state to load.
            agent_identity: The identity of the agent loading the state.
        """
        self.id = state["id"]

        # Reload all tools
        for tool_name in self.list_available_tools(agent_identity.id):
            try:
                self.load_tool(tool_name, agent_identity)
            except Exception:
                pass  # Skip failed tools
