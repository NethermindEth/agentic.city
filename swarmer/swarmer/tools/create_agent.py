"""Tool for creating new agent instances.

This module provides functionality for dynamically creating new agent instances
with specified identities and configurations.
"""

from swarmer.agent import Agent
from swarmer.globals.agent_registry import agent_registry
from swarmer.swarmer_types import AgentIdentity
from swarmer.tools.utils import ToolResponse, tool


@tool
def create_agent(
    agent_identity: AgentIdentity, name: str, token_budget: int, model: str
) -> ToolResponse:
    """Create a new agent instance.

    Args:
        agent_identity (AgentIdentity): The identity information for the new agent
        name (str): The display name of the new agent
        token_budget (int): Maximum tokens the agent can use
        model (str): The model to use for this agent (e.g. "gpt-4")

    Returns:
        A ToolResponse containing the result of the agent creation.
    """
    agent = Agent(name, token_budget, model)
    agent_registry.registry[agent_identity.id] = agent

    return ToolResponse(
        summary=f"Created new agent '{name}' with ID: {agent.identity.id}",
        content=agent.identity.id,
        error=None,
    )
