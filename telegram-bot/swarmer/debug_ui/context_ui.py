from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from swarmer.types import Context

class ContextDebugUI(ABC):
    """Base class for context-specific debug UI components"""
    
    @abstractmethod
    def render(self) -> str:
        """Return HTML string for this context's debug view"""
        pass

    @staticmethod
    def get_ui_for_context(context: 'Context') -> Optional['ContextDebugUI']:
        """Factory method to get the appropriate UI for a context"""
        from swarmer.contexts.memory_context import MemoryContext
        from swarmer.contexts.instruction_context import InstructionContext
        from swarmer.contexts.persona_context import PersonaContext
        
        if isinstance(context, MemoryContext):
            return MemoryContextUI(context)
        elif isinstance(context, InstructionContext):
            return InstructionContextUI(context)
        elif isinstance(context, PersonaContext):
            return PersonaContextUI(context)
        return None

class MemoryContextUI(ContextDebugUI):
    def __init__(self, context: 'MemoryContext'):
        self.context = context
        
    def render(self) -> str:
        memories = self.context.agent_memories
        
        html = """
        <div class="context-section memory-context">
            <h3>Memory Context</h3>
            <div class="memories">
        """
        
        for agent_id, agent_memories in memories.items():
            html += f"<div class='agent-memories'><h4>Agent: {agent_id}</h4>"
            for memory_id, memory in agent_memories.items():
                html += f"""
                <div class="memory-entry">
                    <div class="memory-header">
                        <span class="category">{memory.category}</span>
                        <span class="importance">Importance: {memory.importance}</span>
                    </div>
                    <div class="memory-content">{memory.content}</div>
                    <div class="memory-meta">
                        Source: {memory.source} | ID: {memory_id}
                    </div>
                </div>
                """
            html += "</div>"
            
        html += "</div></div>"
        return html

class InstructionContextUI(ContextDebugUI):
    def __init__(self, context: 'InstructionContext'):
        self.context = context
        
    def render(self) -> str:
        instructions = self.context.instruction_set
        
        html = """
        <div class="context-section instruction-context">
            <h3>Instruction Context</h3>
            <div class="instructions">
        """
        
        for instruction_id, instruction in instructions.items():
            html += f"""
            <div class="instruction-entry">
                <h4>{instruction.name}</h4>
                <div class="instruction-content">{instruction.instruction}</div>
                <div class="instruction-meta">
                    Description: {instruction.description}<br>
                    ID: {instruction_id}
                </div>
            </div>
            """
            
        html += "</div></div>"
        return html

class PersonaContextUI(ContextDebugUI):
    def __init__(self, context: 'PersonaContext'):
        self.context = context
        
    def render(self) -> str:
        personas = self.context.persona_collection
        
        html = """
        <div class="context-section persona-context">
            <h3>Persona Context</h3>
            <div class="personas">
        """
        
        for persona_id, persona in personas.items():
            html += f"""
            <div class="persona-entry">
                <h4>{persona.name}</h4>
                <div class="persona-content">{persona.instruction}</div>
                <div class="persona-meta">
                    Description: {persona.description}<br>
                    ID: {persona_id}
                </div>
            </div>
            """
            
        html += "</div></div>"
        return html 