from typing import Optional, Callable, Any, List, cast
from functools import wraps
import sys
import pdb
import uuid
from swarmer.swarmer_types import Context, Tool, AgentIdentity
from swarmer.globals.agent_registry import agent_registry
from swarmer.tools.utils import tool

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
        self.traced_tools: dict[str, bool] = {}  # tool_name -> is_traced
        self.original_tools: dict[str, Tool] = {}  # Keep original tool references
        self.tools.extend([
            self.trace_tool,
            self.untrace_tool,
            self.list_traced_tools
        ])
        self.id = str(uuid.uuid4())
        
    def get_context_instructions(self, identity: AgentIdentity) -> Optional[str]:
        return """
        # Debugging
        When a user referes to debugging something they are always reffering to
        the tools available to you. Always use the full tool name with the id in this context.

        You have access to debugging capabilities. Use them to:
        - Trace tool execution for debugging
        - Examine tool behavior and state
        - Debug issues with tool execution

        Guidelines:
        1. When to use debugging:
           - Investigating tool behavior
           - Understanding tool execution flow
           - Debugging tool issues
           
        2. Available commands:
           - trace_tool: Start debugging a tool
           - untrace_tool: Stop debugging a tool
           - list_traced_tools: See what's being traced
        """
        
    def get_context(self, identity: AgentIdentity) -> Optional[str]:
        if not self.traced_tools:
            return None
        return f"Currently tracing tools: {', '.join(name for name, is_traced in self.traced_tools.items() if is_traced)}"

    def create_trace_wrapper(self, tool: Tool) -> Tool:
        """Create a traced version of a tool"""
        @wraps(tool)
        def _wrapper(identity: AgentIdentity, *args: Any, **kwargs: Any) -> Any:
            def trace_func(frame: Any, event: str, arg: Any) -> Optional[Callable]:
                if event == 'line' and frame.f_code.co_name == tool.__name__:
                    print(f"\n🔍 Debugging {tool.__name__} at line {frame.f_lineno}")
                    print(f"Locals: {frame.f_locals}")
                    pdb.set_trace()
                return trace_func
            
            sys.settrace(trace_func)
            try:
                result = tool(identity, *args, **kwargs)
            finally:
                sys.settrace(None)
            return result
            
        wrapper = cast(Tool, _wrapper)
        wrapper.__name__ = tool.__name__
        wrapper.__tool_schema__ = tool.__tool_schema__
        return wrapper

    @tool
    def trace_tool(
        self,
        agent_identity: AgentIdentity,
        tool_name: str
    ) -> str:
        """Start tracing a tool's execution for debugging.
        
        Args:
            agent_identity: The agent enabling tracing
            tool_name: Name of the tool to trace
            
        Returns:
            Confirmation message about tracing status
        """
        agent = agent_registry.get_agent(agent_identity)
        if tool_name not in agent.tools:
            return f"❌ Tool {tool_name} not found"
            
        if tool_name in self.traced_tools and self.traced_tools[tool_name]:
            return f"Tool {tool_name} is already being traced"
            
        # Store original tool if not already stored
        if tool_name not in self.original_tools:
            self.original_tools[tool_name] = agent.tools[tool_name]
            
        # Create and register traced version
        traced_tool = self.create_trace_wrapper(self.original_tools[tool_name])
        agent.tools[tool_name] = traced_tool
        self.traced_tools[tool_name] = True
        
        return f"✅ Now tracing tool: {tool_name}"

    @tool
    def untrace_tool(
        self,
        agent_identity: AgentIdentity,
        tool_name: str
    ) -> str:
        """Stop tracing a tool's execution.
        
        Args:
            agent_identity: The agent disabling tracing
            tool_name: Name of the tool to stop tracing
            
        Returns:
            Confirmation message about tracing status
        """
        agent = agent_registry.get_agent(agent_identity)
        if tool_name not in agent.tools or tool_name not in self.traced_tools or not self.traced_tools[tool_name]:
            return f"Tool {tool_name} is not being traced"
            
        # Restore original tool
        agent.tools[tool_name] = self.original_tools[tool_name]
        self.traced_tools[tool_name] = False
        
        return f"✅ Stopped tracing tool: {tool_name}"

    @tool
    def list_traced_tools(
        self,
        agent_identity: AgentIdentity
    ) -> str:
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

    def serialize(self) -> dict:
        """Serialize context state"""
        return {
            "id": self.id,
            "traced_tools": self.traced_tools,
            # Don't serialize original_tools as they'll be re-created
        }

    def deserialize(self, state: dict, agent_identity: AgentIdentity) -> None:
        """Load state into this context instance"""
        self.id = state["id"]
        self.traced_tools = state["traced_tools"]
        agent = agent_registry.get_agent(agent_identity)
        # Restore traced tools
        for tool_name, is_traced in self.traced_tools.items():
            if is_traced and tool_name in agent.tools:
                self.original_tools[tool_name] = agent.tools[tool_name]
                agent.tools[tool_name] = self.create_trace_wrapper(agent.tools[tool_name])
