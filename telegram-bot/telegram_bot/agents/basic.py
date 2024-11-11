from swarmer.agent import Agent
from swarmer.globals.agent_registry import agent_registry
from swarmer.contexts.instruction_context import InstructionContext

agent = Agent("Basic", token_budget=100000, model="gpt-4o")
agent_registry.registry[agent.identity.uuid] = agent

instruction_context = InstructionContext()

agent.register_context(instruction_context)
agent.register_tool(instruction_context.tools[0])

