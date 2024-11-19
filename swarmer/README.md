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
- ⚡ Tool Creation Context: Dynamic tool creation and management
- 🕒 Time Context: Time awareness and scheduling
- 💰 Crypto Context: Cryptocurrency operations
- 🔍 Debug Context: Runtime debugging capabilities

[Learn more about contexts](./contexts/README.md)

### 🛠️ Dynamic Tool Creation
- Agents can create and modify their own tools at runtime
- Each agent has an isolated tools directory
- Tools are automatically loaded on agent startup
- Built-in code validation and safety checks
- Tools persist across sessions

Example tool creation:
```python
# Create a new tool
tool_code = """
@tool
def calculate_average(agent_identity: AgentIdentity, numbers: str) -> str:
    '''Calculate the average of a list of numbers.
    
    Args:
        agent_identity: The agent using the tool
        numbers: Comma-separated list of numbers
        
    Returns:
        The calculated average
    '''
    nums = [float(n.strip()) for n in numbers.split(",")]
    avg = sum(nums) / len(nums)
    return f"The average is: {avg}"
"""

# Use the tool creation context
agent.contexts["tool_creation"].create_tool("calculate_average", tool_code)
```

### 🤖 Agent Identity
- Each agent has a unique identity specified by UUID
- Agents can maintain multiple personas
- State persists across conversations
- Isolated tool environments per agent

### 💾 State Persistence
- JSON-based serialization system
- Each context handles its own state
- Tools are recreated on load
- Human-readable state files
- Automatic state saving

[Learn more about serialization](./docs/serialization.md)

### 📡 Event Handling
- Cron-like scheduled operations
- Data stream subscriptions
- Event-driven agent activation

## Getting Started

1. Set up environment variables:
```bash
# Core settings
export OPENAI_API_KEY=your_key_here
export AGENT_TOOLS_DIRECTORY=/path/to/agent/tools

# Optional settings
export KEYS_DIRECTORY=/path/to/secure/keys
```

2. Create an agent with desired contexts:
```python
from swarmer.agent import Agent
from swarmer.contexts.persona_context import PersonaContext
from swarmer.contexts.memory_context import MemoryContext
from swarmer.contexts.tool_creation_context import ToolCreationContext

# Create agent
agent = Agent("Assistant", token_budget=1000000, model="gpt-4")

# Add contexts
agent.register_context(PersonaContext())
agent.register_context(MemoryContext())
agent.register_context(ToolCreationContext())

# Run agent
response = agent.run_loop("Hello!")

# Save state
Agent.save_state(agent, "agent_state.json")

# Load state
agent = Agent.load_state("agent_state.json")
```

## Documentation
- [Message Flow](./docs/message_flow.md)
- [Contexts](./contexts/README.md)
- [Tools](./docs/tools.md)
- [Serialization](./docs/serialization.md)
