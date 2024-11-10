from swarmer.tools.utils import tool
from swarmer.types import AgentIdentity
from swarmer.agent import Agent
from swarmer.globals.agent_registry import agent_registry

@tool
def create_agent(agent_identity: AgentIdentity, name: str, token_budget: int, model: str) -> str:
    """
    Creates a new assistant which will operate separately from the current assistant.

    Args:
        agent_identity (AgentIdentity): The identity information for the new agent
        name (str): The display name of the new agent
        token_budget (int): Maximum tokens the agent can use
        model (str): The model to use for this agent (e.g. "gpt-4")

    Returns:
        str: The UUID of the newly created agent
    """
    agent = Agent(name, token_budget, model)
    agent_registry.registry[agent_identity.uuid] = agent
    return agent.identity.uuid
