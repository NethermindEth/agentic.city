from typing import Optional
import uuid
from swarmer.instructions.instruction import Persona  # Renamed from Instruction
from swarmer.tools.utils import function_to_schema, tool
from swarmer.types import AgentIdentity, Context, Tool
from swarmer.globals.agent_registry import agent_registry

class PersonaContext(Context):
    """Context for managing an agent's active persona and persona collection.

    This context allows agents to switch between different personas that define
    their personality, specialization and capabilities. It maintains the currently 
    active persona and provides tools for switching between registered personas.

    The persona context is fundamental to enabling dynamic personality changes while
    maintaining proper encapsulation of behavioral state."""
    
    tools: list[Tool] = []
    agent_persona: dict[str, Persona] = {}
    persona_collection: dict[str, Persona] = {}  # Changed from instruction_set

    def __init__(self) -> None:
        self.tools.append(PersonaContext.create_persona)
        self.id = uuid.uuid4()
        super().__init__()

    def get_context_instructions(self, agent: AgentIdentity) -> Optional[str]:
        return f"""
        As the assistant you have the ability to create and switch between different
        personas that the user defines. If the user indicates that they want to
        interact with you in a different way, you can suggest creating a new persona.
        Each persona must describe your personality, behavior and responsibilities
        in that role. Your persona defines how you interact and what capabilities
        you bring to the conversation. You can switch between personas using the
        provided functions. Personas are particularly useful when taking on specialized
        roles like "Teacher", "Code Reviewer", or "Creative Writer". If it's unclear
        what kind of persona the user is looking for, you can ask clarifying questions.
        Only mention personas if the conversation naturally leads to discussing
        different ways of interaction.
        """

    def get_context(self, agent: AgentIdentity) -> Optional[str]:
        return None

    def set_active_persona(agent_identity: AgentIdentity, persona_id: str) -> None:
        """Set the active persona by ID."""
        agent = agent_registry.get_agent(agent_identity)
        if persona_id in PersonaContext.persona_collection:
            agent.persona = PersonaContext.persona_collection[persona_id]
        else:
            raise ValueError(f"No persona found with id: {persona_id}")

    @tool
    def create_persona(agent_identity: AgentIdentity, persona: str, description: str, name: str) -> None:
        """Register a new persona with the agent.
        
        A persona defines a specific personality and role for the agent through a system prompt.
        When registered, the persona becomes available for the agent to embody.

        Args:
            agent_identity (AgentIdentity): Identity of the agent to register the persona for
            persona (str): The system prompt text that defines the agent's personality and behavior
            description (str): A description explaining this persona's characteristics and purpose
            name (str): A short descriptive name for the persona that will be used in the 
                       become_<name><random_u16> function

        The persona will be registered with a unique ID generated from its name and content.
        This ID is used internally to reference and switch between personas.
        """
        agent = agent_registry.get_agent(agent_identity)
        persona = Persona(persona, description, name)

        # Register persona
        PersonaContext.persona_collection[persona.id] = persona

        def wrapper(agent_identity: AgentIdentity) -> str:
            PersonaContext.set_active_persona(agent_identity, persona.id)
            return f"Now acting as {persona.name}"

        wrapper.__name__ = f"become_{persona.name}{persona.id[:16]}"
        wrapper.__doc__ = f"Switch to the {persona.name} persona. Only one persona switch can be called at a time and it must be the last call in the sequence."
        wrapper.schema = function_to_schema(wrapper, wrapper.__name__)
        wrapper.id = persona.id

        agent.register_tool(wrapper)

        return f"Created persona with switch function name: {wrapper.__name__}" 