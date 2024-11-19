"""Instruction module for managing agent behavior directives.

This module provides classes for defining and managing instructions that guide agent
behavior. Instructions can be static or dynamic, and can be composed to create
complex behavior patterns.
"""

import hashlib

from swarmer.swarmer_types import InstructionBase


class Instruction(InstructionBase):
    """Base class for agent behavior instructions.

    This class represents a single instruction that guides agent behavior. It can
    be used directly for simple instructions or extended for more complex behavior
    patterns.

    Attributes:
        instruction: The text of the instruction.
        description: A brief description of the instruction.
        name: A unique name for the instruction.
    """

    def __init__(self, instruction: str, description: str, name: str) -> None:
        """Initialize an instruction.

        Args:
            instruction: The text of the instruction.
            description: A brief description of the instruction.
            name: A unique name for the instruction.
        """
        # TODO: (vulnerability) fix this hash to avoid collisions
        self.id = hashlib.sha256(f"{name}:::{instruction}".encode()).hexdigest()
        self.instruction = instruction
        self.description = description
        self.name = name


class Persona(InstructionBase):
    """Persona class for agent behavior instructions.

    This class represents a persona that guides agent behavior. It can be used to
    define a specific role or character that an agent can take on.

    Attributes:
        instruction: The text of the instruction.
        description: A brief description of the instruction.
        name: A unique name for the instruction.
    """

    def __init__(self, instruction: str, description: str, name: str) -> None:
        """Initialize a persona instruction.

        Args:
            instruction: The text of the instruction.
            description: A brief description of the instruction.
            name: A unique name for the instruction.
        """
        # TODO: (vulnerability) fix this hash to avoid collisions
        self.id = hashlib.sha256(f"{name}:::{instruction}".encode()).hexdigest()
        self.instruction = instruction
        self.description = description
        self.name = name
