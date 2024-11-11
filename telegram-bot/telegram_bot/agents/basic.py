from swarmer.agent import Agent
from swarmer.globals.agent_registry import agent_registry
from swarmer.contexts.persona_context import PersonaContext
from swarmer.contexts.memory_context import MemoryContext

# Create agent
agent = Agent("Basic", token_budget=100000, model="gpt-4o")
agent_registry.registry[agent.identity.uuid] = agent

# Initialize contexts
persona_context = PersonaContext()
memory_context = MemoryContext()

# Register contexts
agent.register_context(persona_context)
agent.register_context(memory_context)

# Register tools from each context
# Note: Using static class methods to avoid binding issues
agent.register_tool(PersonaContext.create_persona)
agent.register_tool(MemoryContext.add_memory)
agent.register_tool(MemoryContext.get_memories_by_category)
agent.register_tool(MemoryContext.update_memory)
agent.register_tool(MemoryContext.remove_memory)

