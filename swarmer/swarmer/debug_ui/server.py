"""Server component for the debug UI."""

import threading
from typing import Dict, Optional, cast

from flask import Flask, abort, render_template_string

from swarmer.agent import Agent
from swarmer.debug_ui.context_ui import ContextDebugUI
from swarmer.swarmer_types import Context

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Agent Debug UI - {{ agent.identity.name }}</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background: #f5f5f5;
        }

        .container {
            max-width: 1200px;
            margin: 0 auto;
        }

        .header {
            display: flex;
            justify-content: space-between;
            align-items: start;
            margin-bottom: 20px;
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }

        .token-usage {
            text-align: right;
            padding: 10px;
            background: #f8f9fa;
            border-radius: 5px;
        }

        .token-usage h3 {
            margin-top: 0;
        }

        .tabs {
            background: white;
            padding: 10px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }

        .tab-buttons {
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
            border-bottom: 1px solid #dee2e6;
            padding-bottom: 10px;
        }

        .tab-button {
            padding: 10px 20px;
            border: none;
            background: none;
            cursor: pointer;
            font-size: 16px;
            border-radius: 5px;
            transition: all 0.2s;
        }

        .tab-button:hover {
            background: #f8f9fa;
        }

        .tab-button.active {
            background: #007bff;
            color: white;
        }

        .tab-content {
            display: none;
            padding: 20px;
            background: white;
            border-radius: 5px;
        }

        .tab-content.active {
            display: block;
        }

        /* Message styles */
        .message {
            padding: 15px;
            margin: 10px 0;
            border-radius: 8px;
            border: 1px solid #dee2e6;
        }

        .user { background-color: #e3f2fd; }
        .assistant { background-color: #f8f9fa; }
        .system { background-color: #fff3e0; }
        .tool { background-color: #e8f5e9; }

        /* Tools section */
        .tool-entry {
            margin: 15px 0;
            padding: 15px;
            background: #f8f9fa;
            border-radius: 8px;
            border-left: 4px solid #007bff;
        }

        /* Context sections */
        .context-section {
            margin: 15px 0;
            padding: 15px;
            background: #f8f9fa;
            border-radius: 8px;
            border: 1px solid #dee2e6;
        }

        /* Utility classes */
        .metadata { font-size: 0.9em; color: #666; }
        .content { white-space: pre-wrap; }
        code {
            background: #e9ecef;
            padding: 2px 4px;
            border-radius: 3px;
            font-family: monospace;
        }
    </style>
    <script>
        function showTab(tabId) {
            // Save active tab to localStorage
            localStorage.setItem('activeTab', tabId);

            // Hide all tabs
            document.querySelectorAll('.tab-content').forEach(tab => {
                tab.classList.remove('active');
            });

            // Remove active class from all buttons
            document.querySelectorAll('.tab-button').forEach(button => {
                button.classList.remove('active');
            });

            // Show selected tab
            document.getElementById(tabId).classList.add('active');
            document.querySelector(`[onclick="showTab('${tabId}')"]`).classList.add('active');
        }

        // Handle message view toggle
        document.addEventListener('DOMContentLoaded', function() {
            const checkbox = document.getElementById('showFullSequence');
            const savedState = localStorage.getItem('showFullSequence');
            checkbox.checked = savedState === 'true';
            toggleMessageView();

            // Restore active tab
            const activeTab = localStorage.getItem('activeTab') || 'messages-tab';
            showTab(activeTab);
        });

        function toggleMessageView() {
            const checkbox = document.getElementById('showFullSequence');
            const standardView = document.getElementById('standardMessages');
            const fullView = document.getElementById('fullSequence');
            localStorage.setItem('showFullSequence', checkbox.checked);

            if (checkbox.checked) {
                standardView.style.display = 'none';
                fullView.style.display = 'block';
            } else {
                standardView.style.display = 'block';
                fullView.style.display = 'none';
            }
        }
    </script>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Agent: {{ agent.identity.name }}</h1>
            <div class="token-usage">
                <h3>Token Usage</h3>
                <p>Prompt tokens: {{ agent.token_usage['prompt_tokens'] }}</p>
                <p>Completion tokens: {{ agent.token_usage['completion_tokens'] }}</p>
                <p>Total tokens: {{ agent.token_usage['total_tokens'] }}</p>
            </div>
        </div>

        <div class="tabs">
            <div class="tab-buttons">
                <button class="tab-button active" onclick="showTab('messages-tab')">Messages</button>
                <button class="tab-button" onclick="showTab('tools-tab')">Tools</button>
                <button class="tab-button" onclick="showTab('contexts-tab')">Contexts</button>
            </div>

            <div id="messages-tab" class="tab-content active">
                <div class="message-controls">
                    <label class="toggle">
                        <input type="checkbox" id="showFullSequence" onchange="toggleMessageView()">
                        Show Full Message Sequence
                    </label>
                </div>

                <div id="standardMessages" class="messages">
                    {% for message in agent.message_log %}
                        <div class="message {{ message.role }}">
                            <div class="metadata">
                                <strong>Role:</strong> {{ message.role }}
                                {% if message.tool_call_id %}
                                    <br><strong>Tool Call ID:</strong> {{ message.tool_call_id }}
                                {% endif %}
                            </div>
                            <div class="content">{{ message.content }}</div>
                        </div>
                    {% endfor %}
                </div>

                <div id="fullSequence" class="messages" style="display: none;">
                    <div class="message system">
                        <div class="metadata">
                            <strong>Role:</strong> system
                            <br><strong>Type:</strong> Constitution & Instructions
                        </div>
                        <div class="content">{{ "\n\n".join([constitution_text] + context_instructions) }}</div>
                    </div>

                    {% for message in agent.message_log %}
                        <div class="message {{ message.role }}">
                            <div class="metadata">
                                <strong>Role:</strong> {{ message.role }}
                                {% if message.tool_call_id %}
                                    <br><strong>Tool Call ID:</strong> {{ message.tool_call_id }}
                                {% endif %}
                            </div>
                            <div class="content">{{ message.content }}</div>
                        </div>
                    {% endfor %}

                    <div class="message system">
                        <div class="metadata">
                            <strong>Role:</strong> system
                            <br><strong>Type:</strong> Current Context State
                        </div>
                        <div class="content">{{ "\n\n".join(current_context) }}</div>
                    </div>
                </div>
            </div>

            <div id="tools-tab" class="tab-content">
                <div class="tools">
                    {% for name, tool in agent.tools.items() %}
                        <div class="tool-entry">
                            <h4>{{ name }}</h4>
                            <div class="tool-schema">
                                <div class="tool-meta">
                                    <strong>Description:</strong> {{ tool.__tool_schema__.get('description', 'No description') }}
                                </div>
                                {% if tool.__tool_schema__.get('parameters') %}
                                    <div class="tool-parameters">
                                        <strong>Parameters:</strong>
                                        <ul>
                                        {% for param in tool.__tool_schema__.get('parameters', {}).get('properties', {}).items() %}
                                            <li>
                                                <code>{{ param[0] }}</code>
                                                {% if param[1].get('type') %}
                                                    <span class="param-type">({{ param[1]['type'] }})</span>
                                                {% endif %}
                                                {% if param[1].get('description') %}
                                                    <br>
                                                    <span class="param-desc">{{ param[1]['description'] }}</span>
                                                {% endif %}
                                            </li>
                                        {% endfor %}
                                        </ul>
                                    </div>
                                {% endif %}
                            </div>
                        </div>
                    {% endfor %}
                </div>
            </div>

            <div id="contexts-tab" class="tab-content">
                {% for context in agent.contexts.values() %}
                    {{ context_uis.get(context.id, '') | safe }}
                {% endfor %}
            </div>
        </div>
    </div>
</body>
</html>
"""


class DebugUIServer:
    """Debug server for monitoring and interacting with Swarmer agents.

    This class provides a web interface for real-time monitoring of agent states,
    contexts, and interactions. It uses Flask to serve the debug UI and handle
    HTTP requests.
    """

    def __init__(self, port: int = 5000) -> None:
        """Initialize the debug server.

        Args:
            port: The port number to listen on.
        """
        self.port = port
        self.agents: Dict[int, Agent] = {}
        self.app = Flask(__name__)
        self.server_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()

        @self.app.route("/")
        def home() -> str:
            """Display list of all agents."""
            agent_list = {
                user_id: agent.identity.name for user_id, agent in self.agents.items()
            }
            return render_template_string(
                """
                <html>
                <head>
                    <title>Agent Debug UI</title>
                    <style>
                        body {
                            font-family: Arial, sans-serif;
                            margin: 0;
                            padding: 20px;
                            background: #f5f5f5;
                        }
                        .agent-list {
                            max-width: 800px;
                            margin: 0 auto;
                        }
                        .agent-entry {
                            background: white;
                            padding: 15px;
                            margin: 10px 0;
                            border-radius: 8px;
                            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                        }
                        a {
                            color: #007bff;
                            text-decoration: none;
                        }
                        a:hover {
                            text-decoration: underline;
                        }
                    </style>
                </head>
                <body>
                    <div class="agent-list">
                        <h1>Active Agents</h1>
                        {% for user_id, name in agents.items() %}
                            <div class="agent-entry">
                                <h3>{{ name }}</h3>
                                <p>User ID: {{ user_id }}</p>
                                <a href="/agent/{{ user_id }}">View Details →</a>
                            </div>
                        {% else %}
                            <p>No active agents</p>
                        {% endfor %}
                    </div>
                </body>
                </html>
                """,
                agents=agent_list,
            )

        @self.app.route("/agent/<int:user_id>")
        def agent_details(user_id: int) -> str:
            """Display details for a specific agent."""
            agent = self.agents.get(user_id)
            if not agent:
                abort(404)

            # Create context UIs
            context_uis = {}
            if agent and agent.contexts:
                for context in agent.contexts.values():
                    # Cast AgentContext to Context for type compatibility
                    context_ui = ContextDebugUI.get_ui_for_context(
                        cast(Context, context)
                    )
                    if context_ui and hasattr(context, "id"):
                        context_uis[context.id] = context_ui.render()

            # Get constitution text
            from swarmer.globals.constitution import constitution

            constitution_text = constitution.instruction

            # Get context instructions and current context
            context_instructions = agent.get_context_instructions() if agent else []
            current_context = agent.get_context() if agent else []

            return render_template_string(
                HTML_TEMPLATE,
                agent=agent,
                context_uis=context_uis,
                constitution_text=constitution_text,
                context_instructions=context_instructions,
                current_context=current_context,
            )

    def register_agent(self, agent: Agent) -> None:
        """Register an agent with the debug UI server.

        Args:
            agent: The agent to register for monitoring.
        """
        if hasattr(agent.identity, "user_id"):
            self.agents[int(agent.identity.user_id)] = agent

    def unregister_agent(self, agent: Agent) -> None:
        """Remove an agent from the debug UI server.

        Args:
            agent: The agent to unregister.
        """
        if hasattr(agent.identity, "user_id"):
            self.agents.pop(int(agent.identity.user_id), None)

    def start(self) -> None:
        """Start the debug UI server in a separate thread."""

    def stop(self) -> None:
        """Stop the debug UI server and clean up resources."""

    def _run(self) -> None:
        """Run the Flask server in the background thread."""
        from werkzeug.serving import make_server

        self.server = make_server("127.0.0.1", self.port, self.app)
        self.server.serve_forever()

    def run(self) -> None:
        """Start the debug UI server in a separate thread."""
        self.server_thread = threading.Thread(target=self._run, daemon=True)
        self.server_thread.start()
