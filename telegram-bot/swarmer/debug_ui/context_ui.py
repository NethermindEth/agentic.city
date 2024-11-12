from abc import ABC, abstractmethod
from swarmer.contexts.persona_context import PersonaContext
from swarmer.contexts.memory_context import MemoryContext
from swarmer.contexts.crypto_context import CryptoContext
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
        if isinstance(context, MemoryContext):
            return MemoryContextUI(context)
        elif isinstance(context, PersonaContext):
            return PersonaContextUI(context)
        elif isinstance(context, CryptoContext):
            return CryptoContextUI(context)
        return None

class MemoryContextUI(ContextDebugUI):
    def __init__(self, context: MemoryContext):
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

class PersonaContextUI(ContextDebugUI):
    def __init__(self, context: PersonaContext):
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

class CryptoContextUI(ContextDebugUI):
    def __init__(self, context: CryptoContext):
        self.context = context
        
    def render(self) -> str:
        balance = self.context.w3.from_wei(
            self.context.w3.eth.get_balance(self.context.faucet_address), 
            'ether'
        )
        
        return f"""
        <div class="context-section crypto-context">
            <h3>Crypto Context</h3>
            
            <div class="faucet-info">
                <h4>🚰 Faucet Address</h4>
                <div class="address-box">
                    <code id="faucet-address">{self.context.faucet_address}</code>
                    <button onclick="copyToClipboard('faucet-address')" class="copy-btn">
                        📋 Copy
                    </button>
                </div>
                <div class="faucet-balance">
                    Balance: {balance} ETH
                </div>
            </div>
        </div>

        <style>
            .faucet-info {{
                background: linear-gradient(135deg, #1a1a1a 0%, #2a2a2a 100%);
                border-radius: 8px;
                padding: 20px;
                margin: 10px 0;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            }}
            .address-box {{
                display: flex;
                align-items: center;
                background: #000;
                padding: 10px;
                border-radius: 4px;
                margin: 10px 0;
            }}
            .copy-btn {{
                margin-left: 10px;
                padding: 5px 10px;
                border: none;
                border-radius: 4px;
                background: #444;
                color: white;
                cursor: pointer;
            }}
            .copy-btn:hover {{
                background: #555;
            }}
            .faucet-balance {{
                color: #00ff00;
                font-weight: bold;
            }}
        </style>
        
        <script>
            function copyToClipboard(elementId) {{
                const text = document.getElementById(elementId).textContent;
                navigator.clipboard.writeText(text);
                
                const btn = event.target;
                const originalText = btn.textContent;
                btn.textContent = '✓ Copied!';
                setTimeout(() => btn.textContent = originalText, 2000);
            }}
        </script>
        """