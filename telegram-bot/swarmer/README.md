# Swarmer Framework

Swarmer is a modular framework for building intelligent agents with specialized capabilities.

## Key Features

### 🧩 Context-Based Architecture
Agents gain capabilities through attachable contexts that provide:
- Specialized functionality (memory, personality management, etc.)
- State management
- Domain-specific tools
- Behavioral guidelines

+ [Learn about message flow and context injection](./docs/message_flow.md)

Available contexts include:
- 🎭 Persona Context: Personality and behavior management
- 🧠 Memory Context: Information persistence across conversations
- 🗺️ Explorer Context: Environmental awareness and navigation

[Learn more about contexts](./contexts/README.md)

### 🤖 Agent Identity
- Each agent has a unique identity specified by UUID
- Agents can maintain multiple personas
- State persists across conversations

### 🔄 Dynamic Tool Management
- Tools can be added/removed at runtime
- Contexts provide specialized tool sets
- Parallel tool execution support

### 📡 Event Handling
- Cron-like scheduled operations
- Data stream subscriptions
- Event-driven agent activation

## Getting Started

1. Set up environment variables for your model:
```bash
# See https://docs.litellm.ai/docs/#litellm-python-sdk
export OPENAI_API_KEY=your_key_here
```

2. Create an agent with desired contexts:
```python
from swarmer.agent import Agent
from swarmer.contexts.persona_context import PersonaContext

# Create agent
agent = Agent("Assistant", token_budget=1000000, model="gpt-4")

# Add persona context
persona_context = PersonaContext()
agent.register_context(persona_context)

# Run agent
response = agent.run_loop("Hello!")
```
