"""Agent module providing core functionality for AI agents with tool and context support."""

import importlib.util
import json
import logging
import os
import sys
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional, Protocol, cast, runtime_checkable

from litellm import completion

from swarmer.globals.agent_registry import agent_registry
from swarmer.globals.constitution import constitution
from swarmer.swarmer_types import AgentBase, AgentContext, AgentIdentity, Message, Tool
from swarmer.tools.utils import ToolResponse

T = Any


@runtime_checkable
class ToolCall(Protocol):
    """A representation of a tool call from the LLM."""

    id: str

    @property
    def function(self) -> Any:
        """Get the function object containing name and arguments."""
        ...


class Agent(AgentBase):
    """An AI agent with capabilities for using tools and maintaining context.

    The Agent class represents an AI assistant that can use tools, maintain context,
    and interact with users through a defined interface. It manages its own state,
    including message history and token usage.
    """

    @staticmethod
    def save_state(agent: "Agent", file_path: str) -> None:
        """Save agent state to file.

        Args:
            agent: The agent to save state for.
            file_path: The file path to save the state to.
        """
        state = {
            "identity": {"name": agent.identity.name, "id": agent.identity.id},
            "token_budget": agent.token_budget,
            "model": agent.model,
            "token_usage": agent.token_usage,
            "message_log": [msg.dict() for msg in agent.message_log],
            "contexts": {
                context.__class__.__name__: context.serialize()
                for context in agent.contexts.values()
            },
        }
        with open(file_path, "w") as f:
            json.dump(state, f, indent=2)

    @staticmethod
    def load_state(file_path: str) -> "Agent":
        """Load agent state from file.

        Args:
            file_path: The file path to load the state from.

        Returns:
            The loaded agent.
        """
        with open(file_path, "r") as f:
            state = json.load(f)

        # Create new agent with basic params
        agent = Agent(
            name=state["identity"]["name"],
            token_budget=state["token_budget"],
            model=state["model"],
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
        for module_info in pkgutil.iter_modules(["swarmer/contexts"]):
            if module_info.name.endswith("_context"):
                module = importlib.import_module(f"swarmer.contexts.{module_info.name}")
                context_class_name = "".join(
                    word.capitalize() for word in module_info.name.split("_")
                )
                if hasattr(module, context_class_name):
                    context_classes[context_class_name] = getattr(
                        module, context_class_name
                    )

        # First register fresh contexts with the saved IDs
        for context_name, context_state in state["contexts"].items():
            context_class = context_classes[context_name]
            context = context_class()
            context.id = context_state["id"]  # Set the ID before registration
            agent.register_context(context)

        # Then deserialize their state
        for context_name, context_state in state["contexts"].items():
            agent.contexts[context_state["id"]].deserialize(
                context_state, agent.identity
            )

        return agent

    def __init__(
        self,
        name: str,
        token_budget: int,
        model: str,
    ):
        """Initialize an Agent with required attributes from AgentBase.

        Args:
            name: The display name of the agent.
            token_budget: Maximum tokens the agent can use.
            model: The model to use for completions.
        """
        self.identity = AgentIdentity(name=name, user_id=str(uuid.uuid4()))
        self.contexts: Dict[str, AgentContext] = {}
        self.tools: Dict[str, Tool] = {}
        self.token_budget = token_budget
        self.message_log: List[Message] = []
        self.model = model
        self.token_usage: Dict[str, int] = {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0,
        }
        self.load_agent_tools()

    # -----
    # Tools
    # -----
    def register_tool(self, tool: Tool) -> None:
        """Register a tool with the agent.

        Args:
            tool: The tool to register.
        """
        logger = logging.getLogger(__name__)
        logger.info(f"Registering tool '{tool.__name__}' for agent {self.identity.id}")
        self.tools[tool.__name__] = tool
        logger.info(f"Successfully registered tool '{tool.__name__}'")

    def unregister_tool(self, tool_name: str) -> None:
        """Unregister a tool from the agent.

        Args:
            tool_name: The name of the tool to unregister.
        """
        self.tools.pop(tool_name)

    # -----
    # Context
    # -----
    def register_context(self, context: AgentContext) -> None:
        """Register a context with the agent.

        Args:
            context: The context to register.
        """
        self.contexts[context.id] = context
        # Register tools
        for tool in context.tools:
            self.register_tool(tool)

    def unregister_context(self, context_id: str) -> None:
        """Unregister a context from the agent.

        Args:
            context_id: The ID of the context to unregister.
        """
        self.contexts.pop(context_id)

    # -----
    # Run
    # -----
    def run_loop(self, user_input: str) -> List[Message]:
        """Run the agent loop.

        Args:
            user_input: The user input to process.

        Returns:
            A list of messages representing the agent's response.
        """
        logger = logging.getLogger(__name__)
        user_message = Message(role="user", content=user_input)

        try:
            # Get context and instructions
            context = self.get_context()
            instructions = self.get_context_instructions()

            # Build system message with context and instructions
            system_content = constitution.instruction + "\n\n"
            if context:
                system_content += "Current context:\n" + "\n".join(context) + "\n\n"
            if instructions:
                system_content += "Instructions:\n" + "\n".join(instructions)

            system_message = Message(role="system", content=system_content)

            context_str = "\n\n".join(self.get_context())
            context_message = Message(
                role="system", content=f"Current context:\n\n{context_str}"
            )

            logger.debug(f"Making completion request for agent {self.identity.id}")
            response = completion(
                model=self.model,
                messages=[
                    system_message,
                    *self.message_log,
                    context_message,
                    user_message,
                ],
                tools=self.get_tool_schemas(),
            )

            # Add token tracking
            if response.usage:
                self.token_usage["prompt_tokens"] += response.usage.prompt_tokens
                self.token_usage[
                    "completion_tokens"
                ] += response.usage.completion_tokens
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
                            name=tool_call.function.name,
                        )
                        response_history.append(tool_result_message)
                    except Exception as e:
                        logger.error(f"Error executing tool call: {e}", exc_info=True)
                        tool_result_message = Message(
                            role="tool",
                            content=f"Error executing tool: {str(e)}",
                            tool_call_id=tool_call.id,
                            name=tool_call.function.name,
                        )
                        response_history.append(tool_result_message)

                context_str = "\n\n".join(self.get_context())
                context_message = Message(
                    role="system", content=f"Current context:\n\n{context_str}"
                )

                logger.debug(
                    f"Making follow-up completion request for agent {self.identity.id}"
                )
                response = completion(
                    model=self.model,
                    messages=[
                        system_message,
                        *self.message_log,
                        user_message,
                        context_message,
                        *response_history,
                    ],
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
                content="I apologize, but I encountered an error processing your request. Please try again.",
            )
            return [error_message]

    def execute_tool(self, tool_name: str, **kwargs: Any) -> ToolResponse:
        """Execute a tool by name with given arguments.

        Args:
            tool_name: The name of the tool to execute.
            **kwargs: The arguments to pass to the tool.

        Returns:
            A ToolResponse containing the result.
        """
        if tool_name not in self.tools:
            return ToolResponse(
                summary=f"Tool {tool_name} not found",
                content=None,
                error=f"Tool {tool_name} not found",
            )

        tool = self.tools[tool_name]
        kwargs["agent_identity"] = self.identity

        try:
            response = tool(**kwargs)
            return cast(ToolResponse, response)
        except Exception as e:
            return ToolResponse(
                summary=f"Error executing tool: {str(e)}", content=None, error=str(e)
            )

    def execute_tool_call(self, tool_call: ToolCall) -> str:
        """Execute a tool call from the LLM.

        Args:
            tool_call: The tool call object from the LLM containing name and arguments.

        Returns:
            The result of the tool execution as a string.
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
        """Get the context instructions for the agent.

        Returns:
            A list of context instructions.
        """
        instructions = [
            context.get_context_instructions(self.identity)
            for context in self.contexts.values()
        ]
        return [x for x in instructions if x is not None]

    def context_to_string(self, context_data: Dict[str, Any]) -> str:
        """Convert context data to a string representation.

        Args:
            context_data: The context data to convert.

        Returns:
            A string representation of the context data.
        """
        parts = []
        for key, value in context_data.items():
            if isinstance(value, list):
                value = ", ".join(str(v) for v in value)
            parts.append(f"{key}: {value}")
        return "; ".join(parts)

    def get_context(self) -> List[str]:
        """Get the context for the agent.

        Returns:
            A list of context strings.
        """
        contexts = [
            context.get_context(self.identity) for context in self.contexts.values()
        ]
        return [self.context_to_string(x) for x in contexts if x is not None]

    def get_all_contexts(self) -> List[Dict[str, Any]]:
        """Get all context data.

        Returns:
            List of context data dictionaries.
        """
        return self.get_all_context_data()

    def get_tool_schemas(self) -> Optional[List[dict]]:
        """Get the tool schemas for the agent.

        Returns:
            A list of tool schemas or None if no tools are registered.
        """
        if not self.tools:
            return None

        # Get all tool schemas
        tool_schemas = []
        for tool in self.tools.values():
            if hasattr(tool, "__tool_schema__"):
                tool_schemas.append(tool.__tool_schema__)

        return tool_schemas

    def get_token_usage(self) -> Dict[str, int]:
        """Get the current token usage statistics.

        Returns:
            A dictionary containing token usage statistics.
        """
        return self.token_usage

    def clear_message_log(self) -> None:
        """Clear the agent's message history."""
        self.message_log.clear()

    def load_agent_tools(self) -> None:
        """Load all tools from the agent's tools directory."""
        tools_dir = (
            Path(os.getenv("AGENT_TOOLS_DIRECTORY", "agent_tools")) / self.identity.id
        )
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

    def get_all_tool_names(self) -> List[str]:
        """Get all tool names from all contexts.

        Returns:
            List of tool names.
        """
        tool_names = []
        for context in self.contexts.values():
            context_data = context.get_context(self.identity)
            if "tools" in context_data:
                tool_names.extend(context_data["tools"])
        return tool_names

    def get_all_tools(self) -> List[Tool]:
        """Get all tools from all contexts.

        Returns:
            List of all tools.
        """
        tools = []
        for context in self.contexts.values():
            tools.extend(context.tools)
        return tools

    def get_all_context_data(self) -> List[Dict[str, Any]]:
        """Get all context data.

        Returns:
            List of context data dictionaries.
        """
        return [
            context.get_context(self.identity) for context in self.contexts.values()
        ]
