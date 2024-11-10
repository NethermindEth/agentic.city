from typing import Optional
from swarmer.instructions.instruction import Instruction
from swarmer.tools.utils import function_to_schema, tool
from swarmer.types import AgentIdentity, Context, Tool
from swarmer.globals.agent_registry import agent_registry

class InstructionContext(Context):
    """Context for managing an agent's active instruction and instruction set.

    This context allows agents to switch between different behavioral instructions that define
    their specialization and capabilities. It maintains the currently active instruction and
    provides tools for switching between registered instructions.

    The instruction context is fundamental to enabling dynamic agent behavior changes while
    maintaining proper encapsulation of instruction state."""
    tools: list[Tool] = []
    agent_instruction: dict[str, Instruction] = {}
    instruction_set: dict[str, Instruction] = {}

    def __init__(self) -> None:
        super().__init__()

    def get_context_instructions(self, agent: AgentIdentity) -> Optional[str]:
        return self.instruction

    def get_context(self, agent: AgentIdentity) -> Optional[str]:
        return None

    @tool
    def set_active_instruction(agent_identity: AgentIdentity, instruction_id: str) -> None:
        """Set the active instruction by ID."""
        agent = agent_registry.get_agent(agent_identity)
        if instruction_id in agent.instruction_set:
            agent.instruction = agent.instruction_set[instruction_id]
        else:
            raise ValueError(f"No instruction found with id: {instruction_id}")

    # -----
    # Instructions
    # -----
    @tool
    def create_instruction(agent_identity: AgentIdentity, instruction: str, description: str, name: str) -> None:
        """Register an instruction with the agent.
        
        An instruction defines a specific behavior mode or role for an agent through a system prompt.
        When registered, the instruction becomes available for the agent to switch to.

        Args:
            agent_identity (AgentIdentity): Identity of the agent to register the instruction for
            instruction (str): The system prompt text that guides the agent's behavior
            description (str): A description explaining what behavior this instruction creates
            name (str): A short descriptive name for the instruction that will be used in the 
                       switch_to_<name><random_u16>_mode function

        The instruction will be registered with a unique ID generated from its name and content.
        This ID is used internally to reference and switch between instructions.
        """
        agent = agent_registry.get_agent(agent_identity)
        instruction = Instruction(instruction, description, name)

        # Register instruction
        InstructionContext.instruction_set[instruction.id] = instruction

        def wrapper(agent_identity: AgentIdentity):
            InstructionContext.set_active_instruction(agent_identity, instruction.id)

        wrapper.__name__ = f"switch_to_{instruction.name}_mode"
        wrapper.__doc__ = f"Switch the agent to {instruction.name} mode. Only one switch function can be called at a time and it must be the last call in the sequence."
        wrapper.schema = function_to_schema(wrapper)
        # In this case we inherit the instruction id as the tool id
        wrapper.id = instruction.id


        agent.register_tool(wrapper)