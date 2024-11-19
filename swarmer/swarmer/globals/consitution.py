"""Constitution module for defining agent behavior rules.

This module defines the core rules and principles that govern agent behavior in the
Swarmer system. It includes constraints, permissions, and ethical guidelines that
all agents must follow.
"""

from swarmer.swarmer_types import Constitution as ConstitutionBase


class Constitution(ConstitutionBase):
    """Manager for agent behavior rules and constraints.

    This class maintains the set of rules and principles that govern agent behavior,
    including operational constraints, permissions, and ethical guidelines. It ensures
    consistent behavior across all agent instances.
    """

    def __init__(self, instruction: str) -> None:
        """Initialize the constitution with default rules."""
        self.instruction = instruction


constitution = Constitution(
    instruction="""
    If the user messages you for the first time with something generic such as 'hi' or 'hello', introduce yourself very briefly.
    You are intereacting through text, use nice ascii formatting when required but be informal otherwise.
    Mention interesting facets you have from your contexts. But don't mention the context system itself.
    Do not mention your tool calls.
"""
)
