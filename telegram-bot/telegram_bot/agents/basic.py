from swarmer.agent import Agent
from swarmer.globals.agent_registry import agent_registry
from swarmer.contexts.persona_context import PersonaContext
from swarmer.contexts.memory_context import MemoryContext

# Create agent
agent = Agent("Basic", token_budget=100000, model="gpt-4o")
agent_registry.registry[agent.identity.id] = agent

# Initialize contexts
persona_context = PersonaContext()
memory_context = MemoryContext()

# Register contexts
agent.register_context(persona_context)
agent.register_context(memory_context)