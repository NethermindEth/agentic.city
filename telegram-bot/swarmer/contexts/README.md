# Swarmer Contexts

Contexts are fundamental building blocks in the Swarmer framework that provide agents with specialized capabilities, state management, and behavioral guidelines. Each context focuses on a specific aspect of agent functionality and can be dynamically attached or detached from agents.

## Available Contexts

### 🎭 Persona Context
**Purpose**: Manages agent personalities and behavioral patterns
- Allows agents to switch between different personas
- Each persona defines a specific role, personality, and set of behaviors
- Provides tools for creating and switching between personas
- Useful for specialized roles like "Teacher", "Code Reviewer", etc.

### 🧠 Memory Context
**Purpose**: Manages persistent information across conversations
- Stores and retrieves important information from past interactions
- Provides tools for memory storage, retrieval, and management
- Helps maintain conversation continuity
- Enables learning from past experiences

## Creating New Contexts

Contexts must implement the `Context` base class and provide:

1. State Management
```python
def get_context(self, agent: AgentIdentity) -> Optional[str]:
    """Return current state information"""
```

2. Usage Instructions
```python
def get_context_instructions(self, agent: AgentIdentity) -> Optional[str]:
    """Return instructions for using this context"""
```

3. Specialized Tools
```python
tools: list[Tool] = []  # List of tools this context provides
```

## Best Practices

1. **Single Responsibility**: Each context should focus on one specific aspect of functionality
2. **Independence**: Contexts should operate independently without relying on other contexts
3. **Clear Instructions**: Provide clear guidelines for how agents should use the context
4. **State Management**: Carefully manage any persistent state to avoid conflicts
5. **Tool Design**: Design tools to be atomic and focused on specific operations

## Example: Creating a Custom Context

```python
class CustomContext(Context):
    """Example custom context implementation"""
    
    tools: list[Tool] = []
    
    def __init__(self) -> None:
        self.tools.append(self.custom_tool)
        self.id = uuid.uuid4()
        super().__init__()

    def get_context_instructions(self, agent: AgentIdentity) -> Optional[str]:
        return """
        Instructions for how the agent should use this context...
        """

    def get_context(self, agent: AgentIdentity) -> Optional[str]:
        return "Current state information..."

    @tool
    def custom_tool(self, agent_identity: AgentIdentity) -> str:
        """Tool implementation..."""
        pass
``` 