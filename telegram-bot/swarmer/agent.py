import json
from swarmer.types import AgentBase, AgentIdentity, Context, Tool, Message
from typing import Any, Optional, List, Dict
from swarmer.globals.consitution import constitution
from litellm import completion
import uuid
from swarmer.debug_ui.server import DebugUIServer

class Agent(AgentBase):
    def __init__(
        self,
        name: str,
        token_budget: int,
        model: str,
        debug_ui: bool = True,
    ):
        """
        Initialize an Agent with required attributes from AgentBase.
        
        Args:
            name: The display name of the agent
            token_budget: Maximum tokens the agent can use
            model: The model to use for completions
            debug_ui: Whether to start the debug UI server
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

        if debug_ui:
            self.debug_server = DebugUIServer(self)
            self.debug_server.start()

    # -----
    # Tools
    # -----
    def register_tool(self, tool: Tool) -> None:
        """Register a tool with the agent."""
        self.tools[tool.__name__] = tool

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
        user_message = Message(role="user", content=user_input)

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
            # TODO: handle in parallel
            for tool_call in message.tool_calls:
                print(f"tool_call: {tool_call}")
                tool_result = self.execute_tool_call(tool_call)
                tool_result_message = Message(role="tool", content=tool_result, tool_call_id=tool_call.id)
                response_history.append(tool_result_message)

            context_str = "\n\n".join(self.get_context())
            context_message = Message(
                role="system", 
                content=f"Current context:\n\n{context_str}"
            )
 
            response = completion(
                model=self.model,
                messages=[system_message, *self.message_log, user_message, context_message, *response_history],
                tools=self.get_tool_schemas(),
            )
            message = response.choices[0].message
            response_history.append(message)
        
        self.message_log += [user_message, *response_history]
        return response_history

    # TODO fix the tool_call type
    def execute_tool_call(self, tool_call: Any) -> str:
        """Execute a tool call and return a formatted result string"""
        name = tool_call.function.name
        args = json.loads(tool_call.function.arguments)
        
        result = self.tools[name](self.identity, **args)
        return str(result)

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
        print([type(tool) for tool in self.tools.values()])
        return [tool.__tool_schema__ for tool in self.tools.values()] if self.tools else None

    def get_token_usage(self) -> Dict[str, int]:
        """Get the current token usage statistics."""
        return self.token_usage
