"""Module for debugging agent tool usage and behavior."""

import logging
from typing import Any, Dict, List, cast
from uuid import uuid4

from swarmer.swarmer_types import AgentIdentity, Context, Tool
from swarmer.tools.utils import tool

logger = logging.getLogger(__name__)


class DebugContext(Context):
    """Context for debugging tool execution.

    This context provides debugging capabilities for tools, allowing agents to:
    - Trace tool execution with interactive debugging
    - View local variables and execution state
    - Step through tool code
    - Manage which tools are being traced
    """

    tools: List[Tool] = []

    def __init__(self) -> None:
        """Initialize the debug context with debugging tools and state tracking."""
        self.traced_tools: Dict[str, bool] = {}  # tool_name -> is_traced
        self.tools.extend([self.trace_tool, self.untrace_tool, self.list_traced_tools])
        self.id = str(uuid4())

    def get_context_instructions(self, agent_identity: AgentIdentity) -> str:
        """Get instructions for using the debug context.

        Args:
            agent_identity: The identity of the agent requesting instructions.

        Returns:
            Instructions for using debugging tools.
        """
        return """
        Debug Context Instructions:
        - Use 'trace_tool' to start debugging a tool
        - Use 'untrace_tool' to stop debugging a tool
        - Use 'list_traced_tools' to see which tools are being traced
        """

    def get_context(self, agent_identity: AgentIdentity) -> Dict[str, Any]:
        """Get the current state of the debug context.

        Args:
            agent_identity: The identity of the agent requesting context.

        Returns:
            Current debugging state and available tools.
        """
        return {
            "traced_tools": {
                name: is_traced for name, is_traced in self.traced_tools.items()
            },
            "tools": [tool.__name__ for tool in self.tools],
        }

    def create_trace_wrapper(self, tool: Tool) -> Tool:
        """Create a wrapper for tracing tool execution.

        Args:
            tool: The tool to wrap.

        Returns:
            A wrapped version of the tool that includes tracing.
        """
        if not hasattr(tool, "__name__"):
            return tool

        tool_name = tool.__name__
        self.traced_tools[tool_name] = True

        def wrapper(*args: Any, **kwargs: Any) -> Any:
            logger.info(f"Tool {tool_name} called with args: {args}, kwargs: {kwargs}")
            try:
                result = tool(*args, **kwargs)
                logger.info(f"Tool {tool_name} returned: {result}")
                return result
            except Exception as e:
                logger.error(f"Tool {tool_name} failed with error: {e}")
                raise

        # Copy all attributes to make wrapper comply with Tool protocol
        for attr in ["__name__", "__doc__", "__tool_schema__", "__tool_doc__"]:
            if hasattr(tool, attr):
                setattr(wrapper, attr, getattr(tool, attr))

        return cast(Tool, wrapper)

    @tool
    def trace_tool(self, agent_identity: AgentIdentity, tool_name: str) -> str:
        """Start tracing a tool's execution for debugging.

        Args:
            agent_identity: The agent enabling tracing
            tool_name: Name of the tool to trace

        Returns:
            Confirmation message about tracing status
        """
        if tool_name not in self.traced_tools:
            self.traced_tools[tool_name] = True
            return f"Now tracing {tool_name}"
        elif self.traced_tools[tool_name]:
            return f"Tool {tool_name} is already being traced"
        else:
            self.traced_tools[tool_name] = True
            return f"Now tracing {tool_name}"

    @tool
    def untrace_tool(self, agent_identity: AgentIdentity, tool_name: str) -> str:
        """Stop tracing a tool's execution.

        Args:
            agent_identity: The agent disabling tracing
            tool_name: Name of the tool to stop tracing

        Returns:
            Confirmation message about tracing status
        """
        if tool_name not in self.traced_tools or not self.traced_tools[tool_name]:
            return f"Tool {tool_name} is not being traced"

        self.traced_tools[tool_name] = False
        return f"Stopped tracing {tool_name}"

    @tool
    def list_traced_tools(self, agent_identity: AgentIdentity) -> str:
        """List all tools currently being traced.

        Args:
            agent_identity: The agent requesting the list

        Returns:
            List of tools currently being traced
        """
        traced = [name for name, is_traced in self.traced_tools.items() if is_traced]
        if not traced:
            return "No tools are currently being traced"
        return f"Currently tracing: {', '.join(traced)}"

    def serialize(self) -> Dict:
        """Serialize context state.

        Returns:
            Serialized context state.
        """
        return {
            "id": self.id,
            "traced_tools": self.traced_tools,
        }

    def deserialize(self, state: Dict, agent_identity: AgentIdentity) -> None:
        """Load state into this context instance.

        Args:
            state: The state to be loaded.
            agent_identity: The identity of the agent loading the state.
        """
        self.id = state["id"]
        self.traced_tools = state["traced_tools"]
