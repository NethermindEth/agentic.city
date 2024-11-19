"""
Global Agent Registry Module

This module provides a singleton registry for managing active agent instances across the application.
The registry maintains a mapping between agent identities and their corresponding agent instances,
allowing for centralized agent management and retrieval.

The registry is primarily used by:
1. Message handlers to access agent instances for processing user messages
2. Agent manager for agent lifecycle management (creation, retrieval)
3. Info commands to display agent information

Usage:
   from swarmer.globals.agent_registry import agent_registry
   
   # Get an agent by identity
   agent = agent_registry.get_agent(agent_identity)
"""

from swarmer.types import AgentBase, AgentIdentity, AgentRegistry

class AgentRegistry_(AgentRegistry):
   def __init__(self) -> None:
      """Initialize an empty agent registry."""
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
