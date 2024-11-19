from abc import ABC, abstractmethod
from swarmer.contexts.persona_context import PersonaContext
from swarmer.contexts.memory_context import MemoryContext
from swarmer.contexts.crypto_context import CryptoContext
from swarmer.contexts.tool_creation_context import ToolCreationContext
from typing import TYPE_CHECKING, Optional
import json

if TYPE_CHECKING:
    from swarmer.swarmer_types import Context, Message

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
        elif isinstance(context, ToolCreationContext):
            return ToolCreationContextUI(context)
        return None

    @staticmethod
    def render_message(message: 'Message') -> str:
        """Render a message with tool call information"""
        html = f"<div class='message {message.role}'>"
        html += f"<div class='message-header'>{message.role.upper()}</div>"
        
        # Handle tool calls
        if hasattr(message, 'tool_calls') and message.tool_calls:
            html += "<div class='tool-calls'>"
            for tool_call in message.tool_calls:
                html += f"""
                <div class='tool-call'>
                    <div class='tool-name'>{tool_call.function.name}</div>
                    <pre class='tool-args'>{json.dumps(json.loads(tool_call.function.arguments), indent=2)}</pre>
                </div>
                """
            html += "</div>"
            
        # Handle tool results
        if message.role == "tool":
            html += f"<div class='tool-result'><pre>{message.content}</pre></div>"
        else:
            html += f"<div class='message-content'>{message.content}</div>"
            
        html += "</div>"
        return html

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
                        <span class="importance">Importance: {memory.importance}</span>
                    </div>
                    <div class="memory-content">{memory.content}</div>
                    <div class="memory-meta">
                        ID: {memory_id}
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
        """

class ToolCreationContextUI(ContextDebugUI):
    def __init__(self, context: ToolCreationContext):
        self.context = context
        
    def render(self) -> str:
        html = """
        <div class="context-section tool-creation-context">
            <h3>Tool Creation Context</h3>
            <div class="tools">
        """
        
        # Group tools by agent
        for agent_dir in self.context.base_tools_dir.glob("*"):
            if not agent_dir.is_dir():
                continue
                
            agent_id = agent_dir.name
            html += f"<div class='agent-tools'><h4>Agent: {agent_id}</h4>"
            
            # List tools for this agent
            tools = []
            for tool_file in agent_dir.glob("*.py"):
                with open(tool_file, 'r') as f:
                    code = f.read()
                tools.append((tool_file.stem, code))
            
            for tool_name, code in tools:
                html += f"""
                <div class="tool-entry">
                    <div class="tool-header">
                        <span class="tool-name">{tool_name}</span>
                        <button onclick="copyToolCode('{tool_name}')" class="copy-btn">
                            📋 Copy Code
                        </button>
                    </div>
                    <pre class="tool-code" id="code-{tool_name}">{code}</pre>
                </div>
                """
            
            html += "</div>"
            
        html += """
        </div></div>
        
        <style>
            .tool-creation-context .tool-entry {
                background: #1a1a1a;
                border-radius: 8px;
                margin: 10px 0;
                padding: 15px;
            }
            .tool-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 10px;
            }
            .tool-name {
                font-weight: bold;
                color: #00ff00;
            }
            .tool-code {
                background: #000;
                padding: 10px;
                border-radius: 4px;
                overflow-x: auto;
            }
            .message .tool-calls {
                background: #2a2a2a;
                border-left: 3px solid #00ff00;
                margin: 10px 0;
                padding: 10px;
            }
            .message .tool-call {
                margin: 5px 0;
            }
            .message .tool-name {
                color: #00ff00;
                font-weight: bold;
            }
            .message .tool-args {
                background: #1a1a1a;
                padding: 8px;
                border-radius: 4px;
                margin: 5px 0;
            }
            .message .tool-result {
                background: #1a1a1a;
                border-left: 3px solid #0088ff;
                padding: 10px;
                margin: 5px 0;
            }
        </style>
        
        <script>
            function copyToolCode(toolName) {
                const code = document.getElementById(`code-${toolName}`).textContent;
                navigator.clipboard.writeText(code);
                
                const btn = event.target;
                const originalText = btn.textContent;
                btn.textContent = '✓ Copied!';
                setTimeout(() => btn.textContent = originalText, 2000);
            }
        </script>
        """
        return html