"""Type definitions for the Swarmer framework."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Literal, Optional, Protocol, runtime_checkable
from uuid import uuid4

from litellm import Message as AnnoyingMessage

from swarmer.tools.types import Tool


class Message(AnnoyingMessage):
    """A message exchanged between agents or between agents and users.

    Attributes:
        content: The text content of the message.
        role: The role of the message sender (assistant, user, system, tool, function).
        function_call: A dictionary representing a function call.
        tool_calls: A list of tool calls.
    """

    def __init__(
        self,
        content: Optional[str] = None,
        role: Literal["assistant", "user", "system", "tool", "function"] = "assistant",
        function_call: Optional[dict] = None,
        tool_calls: Optional[list] = None,
        **params: Any,
    ):
        """Initialize a message.

        Args:
            content: The text content of the message.
            role: The role of the message sender.
            function_call: A dictionary representing a function call.
            tool_calls: A list of tool calls.
            **params: Additional parameters.
        """
        super().__init__(
            content, role, function_call, tool_calls, **params  # type: ignore
        )


@dataclass
class AgentIdentity:
    """Identity information for an agent."""

    id: str
    user_id: str
    name: str

    def __init__(self, name: str, user_id: str):
        """Initialize an agent identity.

        Args:
            name: The name of the agent.
            user_id: The ID of the user who owns this agent.
        """
        self.id = str(uuid4())
        self.name = name
        self.user_id = user_id


@runtime_checkable
class AgentContext(Protocol):
    """Protocol defining the interface for agent contexts."""

    id: str
    tools: List[Tool]

    def get_context(self, agent: AgentIdentity) -> Dict[str, Any]:
        """Get the current state of this context."""
        ...

    def get_context_instructions(self, agent: AgentIdentity) -> str:
        """Get instructions for how to use this context."""
        ...

    def serialize(self) -> Dict[str, Any]:
        """Serialize context state to a dictionary."""
        ...

    def deserialize(self, state: Dict[str, Any], agent_identity: AgentIdentity) -> None:
        """Load state into this context instance."""
        ...


class InstructionBase(ABC):
    """Base class for agent instructions.

    Instructions provide specific directives that guide agent behavior in
    different situations.

    Attributes:
        id: Unique identifier for the instruction.
        instruction: The text of the instruction.
        description: A brief description of what the instruction does.
        name: A human-readable name for the instruction.
    """

    def __init__(self, instruction: str, description: str, name: str) -> None:
        """Initialize an instruction.

        Args:
            instruction: The text of the instruction.
            description: A brief description of what the instruction does.
            name: A human-readable name for the instruction.
        """
        self.id = ""  # Set by child classes
        self.instruction = instruction
        self.description = description
        self.name = name


class Context(AgentContext, ABC):
    """Base class for agent contexts.

    A context represents a specific aspect of an agent's behavior or capabilities,
    such as memory, persona, or tool usage.

    Attributes:
        tools: List of tools available in this context.
        id: Unique identifier for this context.
    """

    def __init__(self) -> None:
        """Initialize a context with default settings."""
        self.tools: List[Tool] = []
        self.id: str = str(uuid4())

    @abstractmethod
    def get_context(self, agent: AgentIdentity) -> Dict[str, Any]:
        """Get the current state of this context.

        Args:
            agent: The agent requesting the context.

        Returns:
            The current state of this context.
        """
        pass

    @abstractmethod
    def get_context_instructions(self, agent: AgentIdentity) -> str:
        """Get instructions for how to use this context.

        Args:
            agent: The agent requesting instructions.

        Returns:
            Instructions for using this context.
        """
        pass

    @abstractmethod
    def serialize(self) -> Dict[str, Any]:
        """Serialize context state to a dictionary.

        Returns:
            Serialized context state.
        """
        pass

    @abstractmethod
    def deserialize(self, state: Dict[str, Any], agent_identity: AgentIdentity) -> None:
        """Load state into this context instance.

        Args:
            state: The state to load.
            agent_identity: The identity of the agent loading the state.
        """
        pass


class AgentBase(ABC):
    """Abstract base class representing an AI agent with its capabilities and settings."""

    identity: AgentIdentity
    contexts: Dict[str, AgentContext]
    tools: Dict[str, Tool]
    token_budget: int
    model: str
    _history: List[Message]

    def __init__(self) -> None:
        """Initialize an agent with default settings."""
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
    def register_context(self, context: AgentContext) -> None:
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


class Constitution(ABC):
    """Base class for agent behavior rules.

    The constitution defines the core rules and principles that govern agent
    behavior, including operational constraints and ethical guidelines.

    Attributes:
        instruction: The text containing the agent's behavioral rules.
    """

    def __init__(self, instruction: str) -> None:
        """Initialize the constitution.

        Args:
            instruction: The text containing the agent's behavioral rules.
        """
        self.instruction = instruction


class AgentRegistry(ABC):
    """Registry for managing and accessing agent instances.

    This class provides a centralized way to track and manage agent instances,
    ensuring unique identifiers and proper lifecycle management.

    Attributes:
        registry: Dictionary mapping agent IDs to agent instances.
    """

    def __init__(self) -> None:
        """Initialize an empty agent registry."""
        self.registry: Dict[str, "AgentBase"] = {}

    @abstractmethod
    def get_agent(self, agent_identity: AgentIdentity) -> "AgentBase":
        """Retrieve an agent instance by its identity.

        Args:
            agent_identity: The identity of the agent to retrieve.

        Returns:
            The agent instance associated with the given identity.

        Raises:
            KeyError: If no agent exists with the given identity.
        """
        pass
