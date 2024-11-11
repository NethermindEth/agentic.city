from typing import Dict, Optional
from flask import Flask, render_template_string
import threading
from swarmer.debug_ui.context_ui import ContextDebugUI
from swarmer.types import AgentBase
from litellm import Message

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
    def __init__(self, agent: AgentBase, port: int = 5000) -> None:
        self.agent = agent
        self.port = port
        self.app = Flask(__name__)
        
        @self.app.route('/')
        def home() -> str:
            # Create context UIs
            context_uis = {}
            for context in self.agent.contexts.values():
                ui = ContextDebugUI.get_ui_for_context(context)
                if ui:
                    context_uis[context.id] = ui.render()
            
            # Get constitution text
            from swarmer.globals.consitution import constitution
            constitution_text = constitution.instruction
            
            # Get context instructions and current context
            context_instructions = self.agent.get_context_instructions()
            current_context = self.agent.get_context()
                    
            return render_template_string(
                HTML_TEMPLATE, 
                agent=self.agent,
                context_uis=context_uis,
                constitution_text=constitution_text,
                context_instructions=context_instructions,
                current_context=current_context
            )
    
    def start(self) -> None:
        """Start the debug UI server in a separate thread"""
        def run_server() -> None:
            self.app.run(port=self.port, debug=False)
            
        self.server_thread = threading.Thread(target=run_server, daemon=True)
        self.server_thread.start()
        
        # Open the browser
        # webbrowser.open(f'http://127.0.0.1:{self.port}')