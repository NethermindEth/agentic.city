from typing import Any, Callable, Optional
from dataclasses import dataclass
from abc import ABC, abstractmethod
from litellm import Message

@dataclass
class AgentIdentity:
    """Represents the identity of an agent with a name and unique identifier.

    Attributes:
        name (str): The display name of the agent
        uuid (str): Unique identifier for the agent
    """
    name: str
    uuid: str

class InstructionBase(ABC):
    """Represents a system prompt that defines an agent's behavior and directives.

    Agents will follow these instructions precisely. Users can create multiple instructions
    to define different agent behaviors and switch between them.

    Instruciton names should be short and descriptive. To the LLM they will appear as
    switch_to_<name>_mode

    Attributes:
        instruction (str): The system prompt text that guides the agent's behavior
        description (str): A description explaining what behavior this instruction creates
        name (str): A name for the instruction
        id (str): hash of the instruction, and name
    """
    instruction: str
    description: str
    name: str
    id: str

    @abstractmethod
    def __init__(self, instruction: str, description: str) -> None:
        pass

class Tool(Callable[[AgentIdentity, *tuple[Any, ...]], Any]):
    """Represents a tool or function that an agent can use.

    Attributes:
        schema (str): JSON schema for the tool's input and output in OpenAI's format (json_schema)
        id (str): hash of the tool's source code TODO (vulnerability): this is not secure, we would need to hash all dependencies or rely on nix. But this will work for now.
    """
    schema: str
    id: str

class Context(ABC):
    """Represents dynamic contextual information and tools that can be accessed by an agent.
    
    Contexts provide time-sensitive data, memory, or other information that may change between
    invocations. Agents can interact with and modify contexts through exposed tools.

    Attributes:
        id (str): hash of the context's source code TODO (vulnerability): this is not secure, we would need to hash all dependencies or rely on nix. But this will work for now.
        tools (list[Tool]): List of tools exposed by this context that allow the agent to interact with it
        get_context (Callable): Function that retrieves the current context state for a specific agent
        get_context_instructions (Callable): Function that retrieves the instructions for how the agent should use and interact with this context
    """
    id: str
    tools: list[Tool]

    @abstractmethod
    def __init__(self) -> None:
        pass

    @abstractmethod
    def get_context(self, agent: AgentIdentity) -> Optional[str]:
        pass

    @abstractmethod
    def get_context_instructions(self, agent: AgentIdentity) -> Optional[str]:
        pass

class AgentBase(ABC):
    """Abstract base class representing an AI agent with its capabilities and settings.

    Attributes:
        identity (AgentIdentity): The agent's identity information
        instruction (Instruction): Current active instruction
        instruction_set (dict[str, Instruction]): Set of available instructions
        context (dict[str, Context]): Set of available contexts (context_id -> context)
        tools (dict[str, Tool]): Set of available tools (name -> tool)
        token_budget (int): Maximum tokens the agent can use
        model (str): The model to use for the agent
    """
    identity: AgentIdentity
    # TODO: model instructions as a context
    instruction: InstructionBase
    instruction_set: dict[str, InstructionBase]
    context: dict[str, Context]
    tools: dict[str, Tool]
    token_budget: int
    model: str
    _history: list[Message]

    @abstractmethod
    def __init__(self) -> None:
        pass

@dataclass
class Constitution:
    """Represents the fundamental rules and principles that govern an agent's behavior.
    
    The Constitution serves as the top-level system prompt that is injected into all agent
    incarnations. The rules and behaviors defined in the Constitution take absolute precedence
    and cannot be overridden, even by user instructions that may conflict with them.

    Attributes:
        instruction (str): The core immutable rules and principles that define the agent's
            fundamental behavior and constraints
    """
    instruction: str

class AgentRegistry:
    """Registry for managing and accessing agents by their unique identifiers.
    
    Attributes:
        registry (dict[str, AgentBase]): A dictionary mapping agent uuids to their instances
    """
    registry: dict[str, AgentBase]

    @abstractmethod
    def get_agent(self, agent_identity: AgentIdentity) -> AgentBase:
        pass
