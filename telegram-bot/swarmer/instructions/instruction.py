from swarmer.types import InstructionBase
import hashlib

class Instruction(InstructionBase):
    def __init__(self, instruction: str, description: str, name: str) -> None:
        ## TODO: (vulnerability) fix this hash to avoid collisions
        self.id = hashlib.sha256(f"{name}:::{instruction}".encode()).hexdigest()
        self.instruction = instruction
        self.description = description
        self.name = name
