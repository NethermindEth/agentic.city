from typing import Any, Callable, Literal, Optional, Protocol, List, Dict, Union
from typing_extensions import runtime_checkable
from dataclasses import dataclass
from abc import ABC, abstractmethod
from litellm import Message as AnnoyingMessage
from swarmer.tools.types import Tool, ToolResponse, ToolableType

class Message(AnnoyingMessage):
    """Wrapper around litellm.Message to make it compatible with the rest of the codebase."""
    def __init__(
        self,
        content: Optional[str] = None,
        role: Literal["assistant", "user", "system", "tool", "function"] = "assistant",
        function_call: Optional[dict] = None,
        tool_calls: Optional[list] = None,
        **params: Any,
    ):
        super().__init__(
            content,
            role, # type: ignore
            function_call,
            tool_calls,
            **params
        )

@dataclass
class AgentIdentity:
    """Represents the identity of an agent with a name and unique identifier."""
    name: str
    id: str

class InstructionBase(ABC):
    """Represents a system prompt that defines an agent's behavior and directives."""
    instruction: str
    description: str
    name: str
    id: str

    @abstractmethod
    def __init__(self, instruction: str, description: str, name: str) -> None:
        pass

class Context(ABC):
    """A Context represents a dynamic aspect of an agent's operational environment."""
    id: str
    tools: List[Tool]

    @abstractmethod
    def __init__(self) -> None:
        pass

    @abstractmethod
    def get_context(self, agent: AgentIdentity) -> Optional[str]:
        """Get the current state of this context."""
        pass

    @abstractmethod
    def get_context_instructions(self, agent: AgentIdentity) -> Optional[str]:
        """Get instructions for how to use this context."""
        pass

    @abstractmethod
    def serialize(self) -> dict:
        """Serialize context state to a dictionary."""
        pass

    @abstractmethod
    def deserialize(self, state: dict, agent_identity: AgentIdentity) -> None:
        """Load state into this context instance."""
        pass

class AgentBase(ABC):
    """Abstract base class representing an AI agent with its capabilities and settings."""
    identity: AgentIdentity
    contexts: Dict[str, Context]
    tools: Dict[str, Tool]
    token_budget: int
    model: str
    _history: List[Message]

    @abstractmethod
    def __init__(self) -> None:
        pass

    @abstractmethod
    def get_context_instructions(self) -> List[str]:
        """Get instructions from all contexts."""
        pass

    @abstractmethod
    def get_context(self) -> List[str]:
        """Get current state from all contexts."""
        pass

    @abstractmethod
    def register_context(self, context: Context) -> None:
        """Register a new context."""
        pass

    @abstractmethod
    def unregister_context(self, context_id: str) -> None:
        """Remove a context."""
        pass

    @abstractmethod
    def register_tool(self, tool: Tool) -> None:
        """Register a new tool."""
        pass

    @abstractmethod
    def unregister_tool(self, tool_name: str) -> None:
        """Remove a tool."""
        pass

class Constitution:
    """Represents the fundamental rules and principles that govern an agent's behavior."""
    def __init__(self, instruction: str):
        self.instruction = instruction

class AgentRegistry(ABC):
    """Registry for managing and accessing agents by their unique identifiers."""
    registry: Dict[str, AgentBase]

    @abstractmethod
    def get_agent(self, agent_identity: AgentIdentity) -> Optional[AgentBase]:
        pass
