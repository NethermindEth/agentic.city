"""UI components for debugging contexts."""

import json
from abc import ABC, abstractmethod
from typing import Optional

from nicegui import ui

from swarmer.contexts.crypto_context import CryptoContext
from swarmer.contexts.memory_context import MemoryContext
from swarmer.contexts.persona_context import PersonaContext
from swarmer.contexts.tool_creation_context import ToolCreationContext
from swarmer.message import Message
from swarmer.swarmer_types import AgentIdentity, Context


class ContextDebugUI(ABC):
    """Abstract base class for context debug UI components."""

    @abstractmethod
    def render(self) -> str:
        """Render the debug UI.

        Returns:
            HTML string representation of the debug UI.
        """
        pass

    @staticmethod
    def get_ui_for_context(context: Context) -> Optional["ContextDebugUI"]:
        """Get the appropriate UI component for a given context.

        Args:
            context: The context to get a UI component for.

        Returns:
            A UI component for the context, or None if no UI is available.
        """
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
    def render_message(message: Message) -> str:
        """Render a message with tool call information.

        Args:
            message: The message to render.

        Returns:
            HTML string representation of the message.
        """
        html = f"<div class='message {message.role}'>"
        html += f"<div class='message-header'>{message.role.upper()}</div>"

        # Handle tool calls
        if hasattr(message, "tool_calls") and message.tool_calls:
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
    """UI component for displaying memory context debug information."""

    def __init__(self, context: MemoryContext) -> None:
        """Initialize the MemoryContextUI component.

        Args:
            context: The memory context to display.
        """
        self.context = context

    def render(self) -> str:
        """Generate the HTML representation of the memory context debug view.

        Returns:
            HTML string representation of the memory context.
        """
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
    """UI component for displaying persona context debug information."""

    def __init__(self, context: PersonaContext) -> None:
        """Initialize the PersonaContextUI component.

        Args:
            context: The persona context to display.
        """
        self.context = context

    def render(self) -> str:
        """Render the persona context debug view.

        Returns:
            HTML string representation of the persona context.
        """
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
    """UI component for displaying cryptocurrency context debug information."""

    def __init__(self, context: CryptoContext) -> None:
        """Initialize the CryptoContextUI component.

        Args:
            context: The crypto context to display.
        """
        self.context = context

    def render(self) -> str:
        """Generate the HTML representation of the crypto context debug view.

        Returns:
            HTML string representation of the crypto context.
        """
        balance = self.context.w3.from_wei(
            self.context.w3.eth.get_balance(self.context.faucet_address), "ether"
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
    """UI component for displaying tool creation context debug information."""

    def __init__(self, context: ToolCreationContext) -> None:
        """Initialize the ToolCreationContextUI component.

        Args:
            context: The tool creation context to display.
        """
        self.context = context

    def render(self) -> str:
        """Return HTML string for the ToolCreationContext debug view."""
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
                with open(tool_file, "r") as f:
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


def create_context_card(context: Context, agent_identity: AgentIdentity) -> None:
    """Create a UI card for displaying context information.

    Args:
        context: The context to display.
        agent_identity: The identity of the agent.
    """
    with ui.card():
        ui.label(f"Context: {context.__class__.__name__}")
        display_context_info(context, agent_identity)


def display_context_info(context: Context, agent_identity: AgentIdentity) -> None:
    """Display detailed information about a context.

    Args:
        context: The context to display information for.
        agent_identity: The identity of the agent.
    """
    instructions = context.get_context_instructions(agent_identity)
    if instructions:
        with ui.expansion("Instructions", value=True):
            ui.markdown(instructions)


class ContextInstructionsTab:
    """Tab for displaying context instructions."""

    def __init__(self, context: Context, agent_identity: AgentIdentity) -> None:
        """Initialize the context instructions tab.

        Args:
            context: The context to display instructions for.
            agent_identity: The identity of the agent.
        """
        self.context = context
        self.agent_identity = agent_identity

    def render(self) -> None:
        """Render the instructions tab content."""
        instructions = self.context.get_context_instructions(self.agent_identity)
        if instructions:
            ui.markdown(instructions)
