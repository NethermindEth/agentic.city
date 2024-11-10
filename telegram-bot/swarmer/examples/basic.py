from swarmer.agent import Agent
from swarmer.globals.agent_registry import agent_registry

agent = Agent("Basic", token_budget=1000000, model="gpt-4o")
agent_registry.registry[agent.identity.uuid] = agent

print(agent.run_loop("Hello, how are you?"))
