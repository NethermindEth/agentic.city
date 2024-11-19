import json
from swarmer.types import AgentBase, AgentIdentity, Context, Tool, Message
from typing import Any, Optional, List, Dict, Union, Protocol, TypeVar, runtime_checkable, cast
from swarmer.globals.consitution import constitution
from litellm import completion
from swarmer.globals.agent_registry import agent_registry
from swarmer.tools.utils import ToolResponse
from swarmer.tools.types import Tool
import uuid
import logging
from pathlib import Path
import os
import importlib.util
import sys

T = TypeVar('T')

@runtime_checkable
class ToolCall(Protocol):
    id: str
    
    @property
    def function(self) -> Any:
        """The function object containing name and arguments."""
        ...

class Agent(AgentBase):
    @staticmethod
    def save_state(agent: 'Agent', file_path: str) -> None:
        """Save agent state to file"""
        state = {
            "identity": {
                "name": agent.identity.name,
                "id": agent.identity.id
            },
            "token_budget": agent.token_budget,
            "model": agent.model,
            "token_usage": agent.token_usage,
            "message_log": [msg.dict() for msg in agent.message_log],
            "contexts": {
                context.__class__.__name__: context.serialize()
                for context in agent.contexts.values()
            }
        }
        with open(file_path, 'w') as f:
            json.dump(state, f, indent=2)

    @staticmethod
    def load_state(file_path: str) -> 'Agent':
        """Load agent state from file"""
        with open(file_path, 'r') as f:
            state = json.load(f)

        # Create new agent with basic params
        agent = Agent(
            name=state["identity"]["name"],
            token_budget=state["token_budget"],
            model=state["model"]
        )
        agent.identity.id = state["identity"]["id"]
        agent.token_usage = state["token_usage"]
        agent.message_log = [Message(**msg) for msg in state["message_log"]]

        # Register agent in registry before deserializing contexts
        agent_registry.registry[agent.identity.id] = agent

        # Import and instantiate contexts dynamically
        import importlib
        import pkgutil
        
        context_classes = {}
        for module_info in pkgutil.iter_modules(['swarmer/contexts']):
            if module_info.name.endswith('_context'):
                module = importlib.import_module(f'swarmer.contexts.{module_info.name}')
                context_class_name = ''.join(word.capitalize() for word in module_info.name.split('_'))
                if hasattr(module, context_class_name):
                    context_classes[context_class_name] = getattr(module, context_class_name)

        # First register fresh contexts with the saved IDs
        for context_name, context_state in state["contexts"].items():
            context_class = context_classes[context_name]
            context = context_class()
            context.id = context_state["id"]  # Set the ID before registration
            agent.register_context(context)

        # Then deserialize their state
        for context_name, context_state in state["contexts"].items():
            agent.contexts[context_state["id"]].deserialize(context_state, agent.identity)

        return agent

    def __init__(
        self,
        name: str,
        token_budget: int,
        model: str,
    ):
        """
        Initialize an Agent with required attributes from AgentBase.
        
        Args:
            name: The display name of the agent
            token_budget: Maximum tokens the agent can use
            model: The model to use for completions
        """
        self.identity = AgentIdentity(name=name, id=str(uuid.uuid4()))
        self.contexts: dict[str, Context] = {}
        self.tools: dict[str, Tool] = {}
        self.token_budget = token_budget
        self.message_log: list[Message] = []
        self.model = model
        self.token_usage: Dict[str, int] = {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0
        }
        self.load_agent_tools()

    # -----
    # Tools
    # -----
    def register_tool(self, tool: Tool) -> None:
        """Register a tool with the agent."""
        logger = logging.getLogger(__name__)
        logger.info(f"Registering tool '{tool.__name__}' for agent {self.identity.id}")
        self.tools[tool.__name__] = tool
        logger.info(f"Successfully registered tool '{tool.__name__}'")

    def unregister_tool(self, tool_name: str) -> None:
        """Unregister a tool from the agent."""
        self.tools.pop(tool_name)

    # -----
    # Context
    # -----
    def register_context(self, context: Context) -> None:
        """Register a context with the agent."""
        self.contexts[context.id] = context
        # Register tools
        for tool in context.tools:
            self.register_tool(tool)

    def unregister_context(self, context_id: str) -> None:
        """Unregister a context from the agent."""
        self.contexts.pop(context_id)

    # -----
    # Run
    # -----
    def run_loop(self, user_input: str) -> List[Message]:
        """Run the agent loop."""
        logger = logging.getLogger(__name__)
        user_message = Message(role="user", content=user_input)

        try:
            system_message = Message(
                role="system",
                content="\n\n".join([
                    constitution.instruction,
                    *self.get_context_instructions()
                ])
            )

            context_str = "\n\n".join(self.get_context())
            context_message = Message(
                role="system", 
                content=f"Current context:\n\n{context_str}"
            )

            logger.debug(f"Making completion request for agent {self.identity.id}")
            response = completion(
                model=self.model,
                messages=[system_message, *self.message_log, context_message, user_message],
                tools=self.get_tool_schemas(),
            )

            # Add token tracking
            if response.usage:
                self.token_usage["prompt_tokens"] += response.usage.prompt_tokens
                self.token_usage["completion_tokens"] += response.usage.completion_tokens
                self.token_usage["total_tokens"] += response.usage.total_tokens

            message = response.choices[0].message
            response_history = [message]

            while response.choices[0].finish_reason == "tool_calls":
                logger.debug(f"Processing tool calls for agent {self.identity.id}")
                # TODO: handle in parallel
                for tool_call in message.tool_calls:
                    try:
                        tool_result = self.execute_tool_call(tool_call)
                        tool_result_message = Message(
                            role="tool", 
                            content=tool_result, 
                            tool_call_id=tool_call.id,
                            name=tool_call.function.name
                        )
                        response_history.append(tool_result_message)
                    except Exception as e:
                        logger.error(f"Error executing tool call: {e}", exc_info=True)
                        tool_result_message = Message(
                            role="tool", 
                            content=f"Error executing tool: {str(e)}", 
                            tool_call_id=tool_call.id,
                            name=tool_call.function.name
                        )
                        response_history.append(tool_result_message)

                context_str = "\n\n".join(self.get_context())
                context_message = Message(
                    role="system", 
                    content=f"Current context:\n\n{context_str}"
                )
    
                logger.debug(f"Making follow-up completion request for agent {self.identity.id}")
                response = completion(
                    model=self.model,
                    messages=[system_message, *self.message_log, user_message, context_message, *response_history],
                    tools=self.get_tool_schemas(),
                )
                message = response.choices[0].message
                response_history.append(message)
            
            self.message_log += [user_message, *response_history]
            return response_history

        except Exception as e:
            logger.error(f"Error in agent run loop: {e}", exc_info=True)
            error_message = Message(
                role="assistant",
                content="I apologize, but I encountered an error processing your request. Please try again."
            )
            return [error_message]

    def execute_tool(self, tool_name: str, **kwargs: Any) -> ToolResponse:
        """Execute a tool by name with given arguments.
        
        Args:
            tool_name: Name of the tool to execute
            **kwargs: Arguments to pass to the tool
            
        Returns:
            ToolResponse containing the result
        """
        if tool_name not in self.tools:
            return ToolResponse(
                summary=f"Tool {tool_name} not found",
                content=None,
                error=f"Tool {tool_name} not found"
            )

        tool = self.tools[tool_name]
        kwargs['agent_identity'] = self.identity
        
        try:
            response = tool(**kwargs)
            return cast(ToolResponse, response)
        except Exception as e:
            return ToolResponse(
                summary=f"Error executing tool: {str(e)}",
                content=None,
                error=str(e)
            )

    def execute_tool_call(self, tool_call: ToolCall) -> str:
        """Execute a tool call from the LLM.
        
        Args:
            tool_call: The tool call object from the LLM containing name and arguments
            
        Returns:
            The result of the tool execution as a string
        """
        try:
            args = json.loads(tool_call.function.arguments)
            response = self.execute_tool(tool_call.function.name, **args)
            
            # Always return a string summary for LLM consumption
            if response.error:
                return f"Error executing tool: {response.error}"
            return response.summary
            
        except Exception as e:
            return f"Error executing tool: {str(e)}"

    def get_context_instructions(self) -> list[str]:
        """Get the context instructions for the agent."""
        instructions = [context.get_context_instructions(self.identity) for context in self.contexts.values()]
        return [x for x in instructions if x is not None]

    def get_context(self) -> list[str]:
        """Get the context for the agent."""
        contexts = [context.get_context(self.identity) for context in self.contexts.values()]
        return [x for x in contexts if x is not None]


    def get_tool_schemas(self) -> Optional[List[dict]]:
        """Get the tool schemas for the agent."""
        return [tool.__tool_schema__ for tool in self.tools.values()] if self.tools else None

    def get_token_usage(self) -> Dict[str, int]:
        """Get the current token usage statistics."""
        return self.token_usage

    def clear_message_log(self) -> None:
        """Clear the agent's message history"""
        self.message_log.clear()

    def load_agent_tools(self) -> None:
        """Load all tools from the agent's tools directory."""
        tools_dir = Path(os.getenv("AGENT_TOOLS_DIRECTORY", "agent_tools")) / self.identity.id
        if not tools_dir.exists():
            return
            
        for file in tools_dir.glob("*.py"):
            if file.stem == "__init__":
                continue
                
            try:
                # Import the module with agent-specific namespace
                module_name = f"{self.identity.id}.{file.stem}"
                spec = importlib.util.spec_from_file_location(module_name, file)
                if spec is None or spec.loader is None:
                    continue
                    
                module = importlib.util.module_from_spec(spec)
                sys.modules[module_name] = module
                spec.loader.exec_module(module)
                
                # Register any tools found
                for attr_name in dir(module):
                    attr = getattr(module, attr_name)
                    if hasattr(attr, "__tool_schema__"):
                        self.register_tool(attr)
                        
            except Exception:
                continue
