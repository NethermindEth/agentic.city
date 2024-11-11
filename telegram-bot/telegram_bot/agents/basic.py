from swarmer.agent import Agent
from swarmer.globals.agent_registry import agent_registry
from swarmer.contexts.persona_context import PersonaContext

agent = Agent("Basic", token_budget=100000, model="gpt-4o")
agent_registry.registry[agent.identity.uuid] = agent

persona_context = PersonaContext()

agent.register_context(persona_context)
agent.register_tool(persona_context.tools[0])

