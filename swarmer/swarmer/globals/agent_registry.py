"""
Agent registry module for managing agent instances.

This module provides a singleton registry for tracking and managing agent instances
across the Swarmer system. It ensures unique agent IDs and provides methods for
agent lifecycle management.
"""

from typing import Dict

from swarmer.swarmer_types import AgentBase, AgentIdentity, AgentRegistry


class AgentRegistry_(AgentRegistry):
    """Registry for managing agent instances.

    This class implements the Singleton pattern to provide a global registry of
    agent instances. It ensures unique agent IDs and provides methods for
    registering, retrieving, and unregistering agents.
    """

    _instance = None
    _agents: Dict[str, AgentBase] = {}

    def __new__(cls) -> "AgentRegistry_":
        """Create or return the singleton instance.

        Returns:
            The singleton AgentRegistry instance.
        """
        if cls._instance is None:
            cls._instance = super(AgentRegistry_, cls).__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        """Initialize an empty agent registry."""
        if not hasattr(self, "registry"):
            self.registry: dict[str, AgentBase] = {}

    def get_agent(self, agent_identity: AgentIdentity) -> AgentBase:
        """
        Retrieve an agent instance by its identity.

        Args:
            agent_identity: The identity of the agent to retrieve

        Returns:
            The agent instance associated with the given identity

        Raises:
            KeyError: If no agent exists for the given identity
        """
        return self.registry[agent_identity.id]


agent_registry = AgentRegistry_()
