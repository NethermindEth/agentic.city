from swarmer.agent import Agent
from swarmer.contexts.persona_context import PersonaContext
from swarmer.globals.agent_registry import agent_registry

agent = Agent("Basic", token_budget=1000000, model="gpt-4o")
agent_registry.registry[agent.identity.id] = agent

persona_context = PersonaContext()

agent.register_context(persona_context)

print(agent.run_loop("List the tools available to you"))
print(agent.run_loop("create an instruction called math_teacher who explains math problems step by step"))
print(agent.run_loop("Now list the tools available to you"))
print(agent.run_loop("Switch to the math_teacher instruction"))
print(agent.run_loop("Explain to me the solution to the equation x^2 + 2x - 3 = 0"))
