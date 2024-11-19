"""Module for managing agent personas and personality traits."""

import uuid
from typing import Any, Dict, List, Optional, cast

from swarmer.globals.agent_registry import agent_registry
from swarmer.instructions.instruction import Persona
from swarmer.swarmer_types import AgentIdentity, Context, Tool
from swarmer.tools.utils import ToolResponse, function_to_schema, tool


class PersonaContext(Context):
    """Context for managing agent personality and behavior characteristics.

    This context enables agents to maintain consistent personas across interactions,
    including personality traits, communication style, and behavioral patterns.

    The persona context is fundamental to enabling dynamic personality changes while
    maintaining proper encapsulation of behavioral state.
    """

    tools: List[Tool] = []

    def __init__(self) -> None:
        """Initialize persona context with personality management tools."""
        self.tools.append(self.create_persona)
        self.agent_persona: Dict[str, Persona] = {}
        self.persona_collection: Dict[str, Persona] = {}
        self.id = str(uuid.uuid4())

    def get_context_instructions(self, agent: AgentIdentity) -> str:
        """Get instructions for using the persona context.

        Args:
            agent: The identity of the agent requesting instructions.

        Returns:
            Instructions for using persona management tools.
        """
        return """
        Persona Context Instructions:
        - Maintain consistent personality traits
        - Follow defined behavioral patterns
        - Use persona-specific language and tone
        """

    def get_context(self, agent: AgentIdentity) -> Dict[str, Any]:
        """Get the current persona state.

        Args:
            agent: The agent requesting context.

        Returns:
            Current persona state including traits and behaviors.
        """
        return {
            "traits": None,
            "behaviors": None,
            "tools": [tool.__name__ for tool in self.tools],
        }

    def set_active_persona(
        self, agent_identity: AgentIdentity, persona_id: str
    ) -> None:
        """Set the active persona by ID.

        Args:
            agent_identity: The identity of the agent setting the active persona.
            persona_id: The ID of the persona to set as active.
        """
        if persona_id in self.persona_collection:
            self.agent_persona[agent_identity.id] = self.persona_collection[persona_id]
        else:
            raise ValueError(f"No persona found with id: {persona_id}")

    def get_active_persona(self, agent_identity: AgentIdentity) -> Optional[Persona]:
        """Get the active persona for the given agent.

        Args:
            agent_identity: The identity of the agent requesting the active persona.

        Returns:
            The active persona for the given agent.
        """
        return self.agent_persona.get(agent_identity.id)

    def persona_switch_tool(
        self, agent_identity: AgentIdentity, persona_id: str
    ) -> ToolResponse:
        """Class-level method for persona switching.

        Args:
            agent_identity: The identity of the agent switching personas.
            persona_id: The ID of the persona to switch to.

        Returns:
            A ToolResponse containing the result of the persona switch.
        """
        try:
            self.set_active_persona(agent_identity, persona_id)
            persona_name = self.persona_collection[persona_id].name
            return ToolResponse(
                summary=f"Now acting as {persona_name}",
                content={
                    "status": "success",
                    "persona": {"id": persona_id, "name": persona_name},
                },
                error=None,
            )
        except Exception as e:
            error_msg = f"Failed to switch persona: {str(e)}"
            return ToolResponse(summary=error_msg, content=None, error=error_msg)

    @tool
    def create_persona(
        self, agent_identity: AgentIdentity, persona: str, description: str, name: str
    ) -> ToolResponse:
        """Register a new persona with the agent.

        A persona defines a specific personality and role for the agent through a system prompt.
        When registered, the persona becomes available for the agent to embody.

        Args:
            agent_identity (AgentIdentity): Identity of the agent to register the persona for
            persona (str): The system prompt text that defines the agent's personality and behavior
            description (str): A description explaining this persona's characteristics and purpose
            name (str): A short descriptive name for the persona that will be used in the
                       become_<n><random_u16> function

        Returns:
            ToolResponse containing the created persona's details and switch function name
        """
        try:
            agent = agent_registry.get_agent(agent_identity)
            persona_obj = Persona(persona, description, name)

            # Register persona
            self.persona_collection[persona_obj.id] = persona_obj

            def _wrapper(agent_identity: AgentIdentity) -> ToolResponse:
                return self.persona_switch_tool(agent_identity, persona_obj.id)

            wrapper = cast(Tool, _wrapper)
            wrapper.__name__ = f"become_{persona_obj.name}_{persona_obj.id[:16]}"
            wrapper.__doc__ = f"Switch to the {persona_obj.name} persona. Only one persona switch can be called at a time and it must be the last call in the sequence."
            wrapper.__tool_schema__ = function_to_schema(wrapper, wrapper.__name__)

            agent.register_tool(wrapper)

            success_msg = (
                f"Created persona with switch function name: {wrapper.__name__}"
            )
            return ToolResponse(
                summary=success_msg,
                content={
                    "status": "success",
                    "persona": {
                        "id": persona_obj.id,
                        "name": persona_obj.name,
                        "description": description,
                        "switch_function": wrapper.__name__,
                    },
                },
                error=None,
            )
        except Exception as e:
            error_msg = f"Failed to create persona: {str(e)}"
            return ToolResponse(summary=error_msg, content=None, error=error_msg)

    def serialize(self) -> Dict:
        """Serialize context state.

        Returns:
            A dictionary containing the context state.
        """
        return {
            "id": self.id,
            "agent_persona": {
                agent_id: {
                    "instruction": persona.instruction,
                    "description": persona.description,
                    "name": persona.name,
                }
                for agent_id, persona in self.agent_persona.items()
            },
            "persona_collection": {
                persona_id: {
                    "instruction": persona.instruction,
                    "description": persona.description,
                    "name": persona.name,
                }
                for persona_id, persona in self.persona_collection.items()
            },
        }

    def deserialize(self, state: Dict, agent_identity: AgentIdentity) -> None:
        """Load state into this context instance.

        Args:
            state: The state to load into the context.
            agent_identity: The identity of the agent loading the state.
        """
        self.id = state["id"]

        # Restore personas
        self.persona_collection = {
            persona_id: Persona(**persona_data)
            for persona_id, persona_data in state["persona_collection"].items()
        }
        self.agent_persona = {
            agent_id: Persona(**persona_data)
            for agent_id, persona_data in state["agent_persona"].items()
        }

        # Recreate switch tools for each persona
        for persona in self.persona_collection.values():
            self.create_persona(
                agent_identity=agent_identity,
                persona=persona.instruction,
                description=persona.description,
                name=persona.name,
            )
