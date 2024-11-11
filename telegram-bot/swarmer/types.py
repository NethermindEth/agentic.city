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
    """Represents a function that an agent can use to affect its environment.
    
    Tools are the primary way agents interact with the world outside their
    conversation context. Each tool has a schema describing its interface
    and a unique identifier for versioning.

    Important:
        The first parameter of every tool MUST be agent_identity: AgentIdentity.
        This parameter identifies which agent invoked the tool and enables
        agent-specific behavior.

    Tools should:
    1. Be atomic - do one thing well
    2. Be stateless when possible
    3. Handle errors gracefully
    4. Have clear documentation
    5. Include proper type hints
    6. Always accept agent_identity as first parameter

    Example:
        @tool
        def my_tool(agent_identity: AgentIdentity, param1: str) -> str:
            agent = agent_registry.get_agent(agent_identity)
            return f"Performed action for {agent.identity.name}"

    Attributes:
        schema (str): JSON schema describing the tool interface in OpenAI format
        id (str): Unique identifier (hash of source code)
        __name__ (str): The function name used in schemas
        __doc__ (str): Documentation string used in schemas
        __annotations__ (dict): Type hints used for schema generation
    """
    schema: str
    id: str

class Context(ABC):
    """A Context represents a dynamic aspect of an agent's operational environment.
    
    Contexts are fundamental building blocks that provide agents with:
    1. State Management: Maintain and manage dynamic state that persists across interactions
    2. Specialized Tools: Expose domain-specific tools for interacting with the context
    3. Behavioral Guidelines: Provide instructions on how to utilize the context
    4. Environmental Awareness: Supply real-time information about their current state
    
    Each context is independent and focuses on a specific aspect of agent functionality,
    such as personality management, memory retention, or environmental exploration.
    
    Attributes:
        id (str): Unique identifier for the context
        tools (list[Tool]): Tools this context provides to the agent
    """
    id: str
    tools: list[Tool]

    @abstractmethod
    def __init__(self) -> None:
        pass

    @abstractmethod
    def get_context(self, agent: AgentIdentity) -> Optional[str]:
        """Retrieve the current state information for this context.
        
        This method returns real-time information about the context's current state
        that the agent should be aware of when making decisions.
        
        Args:
            agent: The identity of the agent requesting context
            
        Returns:
            String describing current context state or None if no state info is needed
        """
        pass

    @abstractmethod
    def get_context_instructions(self, agent: AgentIdentity) -> Optional[str]:
        """Retrieve instructions for how the agent should use this context.
        
        This method returns guidelines and behavioral instructions that help the agent
        understand how to properly utilize this context and its tools.
        
        Args:
            agent: The identity of the agent requesting instructions
            
        Returns:
            String containing usage instructions or None if no instructions needed
        """
        pass

class AgentBase(ABC):
    """Abstract base class representing an AI agent with its capabilities and settings.
    
    Agents are modular entities whose behavior is shaped by their attached contexts.
    Each context provides a different aspect of functionality, from personality management
    to memory retention to environmental interaction.

    Attributes:
        identity (AgentIdentity): The agent's identity information
        persona (Persona): Current active persona defining behavior
        persona_collection (dict[str, Persona]): Available personas
        context (dict[str, Context]): Active contexts providing different capabilities
        tools (dict[str, Tool]): Available tools from all contexts
        token_budget (int): Maximum tokens the agent can use
        model (str): The model to use for the agent
        _history (list[Message]): Conversation history
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
