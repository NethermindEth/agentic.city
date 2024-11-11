from typing import Any, Callable, Literal, Optional, Protocol, List, Dict, Union
from dataclasses import dataclass
from abc import ABC, abstractmethod
from litellm import Message as AnnoyingMessage

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
    """Represents the identity of an agent with a name and unique identifier.

    Attributes:
        name (str): The display name of the agent
        id (str): Unique identifier for the agent
    """
    name: str
    id: str

class InstructionBase(ABC):
    """Represents a system prompt that defines an agent's behavior and directives.

    Agents will follow these instructions precisely. Users can create multiple instructions
    to define different agent behaviors and switch between them.

    Instruction names should be short and descriptive. To the LLM they will appear as
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
    def __init__(self, instruction: str, description: str, name: str) -> None:
        pass

ToolableType = Callable[..., str]

class Tool(Protocol):
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
        schema (dict): JSON schema describing the tool interface in OpenAI format
        id (str): Unique identifier (hash of source code)
        __name__ (str): The function name used in schemas
        __doc__ (str): Documentation string used in schemas
        __call__ (Callable): The wrapped function
    """
    __call__: ToolableType
    __name__: str
    __tool_doc__: str
    __tool_schema__: dict

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
    tools: List[Tool]

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

    @abstractmethod
    def serialize(self) -> dict:
        """Serialize context state to a dictionary"""
        pass

    @classmethod
    @abstractmethod
    def deserialize(cls, state: dict) -> 'Context':
        """Create a context from serialized state"""
        pass

    @abstractmethod
    def deserialize(self, state: dict, agent_identity: AgentIdentity) -> None:
        """Load state into this context instance"""
        pass

class AgentBase(ABC):
    """Abstract base class representing an AI agent with its capabilities and settings.
    
    Agents are modular entities whose behavior is shaped by their attached contexts.
    Each context provides a different aspect of functionality, from personality management
    to memory retention to environmental interaction.

    Attributes:
        identity (AgentIdentity): The agent's identity information
        instruction (InstructionBase): Current active instruction defining behavior
        instruction_set (dict[str, InstructionBase]): Available instructions
        context (dict[str, Context]): Active contexts providing different capabilities
        tools (dict[str, Tool]): Available tools from all contexts
        token_budget (int): Maximum tokens the agent can use
        model (str): The model to use for the agent
        _history (list[Message]): Conversation history
    """
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
    def get_context_instructions(self) -> list[str]:
        """Get the context instructions for the agent.
        
        Returns a list of instruction strings from all registered contexts that help guide
        the agent's behavior. Each context can provide its own set of instructions on how
        the agent should interact with its capabilities.

        Returns:
            list[str]: List of instruction strings from all contexts, excluding None values
        """
        pass

    @abstractmethod
    def get_context(self) -> list[str]:
        """Get the current context state for the agent.
        
        Returns a list of context strings representing the current state of all registered
        contexts. Each context can provide information about its current state that is
        relevant for the agent's decision making.

        Returns:
            list[str]: List of context state strings from all contexts, excluding None values
        """
        pass

    @abstractmethod
    def register_context(self, context: Context) -> None:
        """Register a context with the agent.
        
        This method allows the agent to incorporate a new context, providing it with
        additional capabilities and behaviors.
        """
        pass

    @abstractmethod
    def unregister_context(self, context_id: str) -> None:
        """Unregister a context from the agent.
        
        This method allows the agent to remove a context, preventing it from being used.
        """
        pass

    @abstractmethod
    def register_tool(self, tool: Tool) -> None:
        """Register a tool with the agent.
        
        This method allows the agent to incorporate a new tool, providing it with
        additional capabilities.
        """
        pass

    @abstractmethod
    def unregister_tool(self, tool_name: str) -> None:
        """Unregister a tool from the agent.
        
        This method allows the agent to remove a tool, preventing it from being used.
        """
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

class AgentRegistry(ABC):
    """Registry for managing and accessing agents by their unique identifiers.
    
    Attributes:
        registry (dict[str, AgentBase]): A dictionary mapping agent uuids to their instances
    """
    registry: Dict[str, AgentBase]

    @abstractmethod
    def get_agent(self, agent_identity: AgentIdentity) -> AgentBase:
        pass
