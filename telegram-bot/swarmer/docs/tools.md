# Tools in Swarmer

Tools are functions that agents can use to interact with their environment and perform actions. They are the primary way agents affect the world outside their conversation context.

## Tool Architecture

### Core Components

1. **Tool Definition and Agent Identity**
   ```python
   @tool
   def my_tool(agent_identity: AgentIdentity, arg1: str, arg2: int) -> str:
       """Tool documentation string"""
       # agent_identity is always the first parameter
       # It identifies which agent invoked the tool
       agent = agent_registry.get_agent(agent_identity)
       # Now you can perform agent-specific operations
       pass
   ```

   **Important**: Every tool's first parameter must be `agent_identity: AgentIdentity`. This:
   - Identifies which agent invoked the tool
   - Enables agent-specific behavior and state management
   - Provides access to the agent's contexts and capabilities
   - Allows tools to modify agent state appropriately

2. **Tool Schema**
   - Automatically generated from function signature
   - Compatible with OpenAI's function calling format
   - Includes:
     - Name
     - Description (from docstring)
     - Parameters and types
     - Return type

3. **Tool Identity**
   - Each tool has a unique ID (hash of its source code)
   - Used for tool versioning and updates
   - Helps prevent duplicate tools

## Tool Registration Flow

1. **Context Level**
   ```python
   class MyContext(Context):
       tools: list[Tool] = []
       
       def __init__(self) -> None:
           # INCORRECT - Don't use self.my_tool
           # self.tools.append(self.my_tool)  # This binds context as first param!
           
           # CORRECT - Use the static class method
           self.tools.append(MyContext.my_tool)
           self.id = uuid.uuid4()

       @tool
       def my_tool(agent_identity: AgentIdentity, arg1: str) -> str:
           """Tool implementation"""
           pass
   ```

   **Important**: Tools must be registered using their static class method version (MyContext.my_tool), 
   not the instance method version (self.my_tool). Using self.my_tool will incorrectly bind the 
   context instance as the first parameter instead of agent_identity.

2. **Agent Level**
   ```python
   def register_tool(self, tool: Tool) -> None:
       """Register a tool with the agent."""
       self.tools[tool.__name__] = tool
   ```

## Tool Types

### 1. Context Tools
- Bound to specific contexts
- Manage context-specific state
- Example: Persona switching, memory operations

### 2. System Tools
- Core system functionality
- Available to all agents
- Example: Agent creation, environment info

### 3. Custom Tools
- User-defined functionality
- Can be dynamically added
- Example: API integrations, custom actions

## Tool Decorator

The `@tool` decorator provides:
1. Schema Generation
2. Tool Registration
3. Error Handling
4. Type Validation

```python
def tool(func: Callable[[AgentIdentity, *tuple[Any, ...]], str]) -> Tool:
    """Decorator that adds OpenAI function schema to a tool."""
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
        
    wrapper.__doc__ = func.__doc__
    wrapper.__annotations__ = func.__annotations__
    wrapper.id = hashlib.sha256(inspect.getsource(func).encode()).hexdigest()
    wrapper.__name__ = func.__name__
    wrapper.schema = function_to_schema(func, wrapper.__name__)

    return wrapper
```

## Best Practices

1. **Documentation**
   ```python
   @tool
   def my_tool(agent_identity: AgentIdentity, param: str) -> str:
       """Clear description of what the tool does.
       
       Args:
           agent_identity: The identity of the calling agent
           param: Description of the parameter
           
       Returns:
           Description of what is returned
           
       Example:
           my_tool(agent, "example")
       """
   ```

2. **Error Handling**
   ```python
   @tool
   def safe_tool(agent_identity: AgentIdentity) -> str:
       try:
           # Tool implementation
           return "Successfully performed action X"  # Describe success
       except Exception as e:
           return f"Error: {str(e)}"  # Describe failure
   ```

3. **Type Hints**
   - Always include proper type hints
   - Helps with schema generation
   - Improves tool usability

4. **Atomic Design**
   - Each tool should do one thing well
   - Avoid complex multi-step operations
   - Break complex operations into multiple tools

5. **State Management**
   - Tools should be stateless when possible
   - State should be managed by contexts
   - Use agent_identity for agent-specific operations

## Tool Usage Example

```python
from swarmer.tools.utils import tool
from swarmer.types import AgentIdentity

class WeatherContext(Context):
    """Context for weather-related operations."""
    
    tools: list[Tool] = []
    
    def __init__(self) -> None:
        self.tools.append(self.get_weather)
        self.id = uuid.uuid4()
        
    @tool
    def get_weather(
        agent_identity: AgentIdentity,
        location: str,
        unit: str = "celsius"
    ) -> str:
        """Get current weather for a location.
        
        Args:
            agent_identity: The calling agent's identity
            location: City or location name
            unit: Temperature unit (celsius/fahrenheit)
            
        Returns:
            Current weather information as a string
        """
        # Implementation
        return f"Weather in {location}: 20°{unit}"
```

## Tool Limitations

1. **Security**
   - Tools have access to agent identity
   - Need careful permission management
   - Tool source code hashing isn't fully secure

2. **Performance**
   - Tools are executed synchronously by default
   - Complex tools can block the agent
   - Consider async for heavy operations

3. **State**
   - Tools should minimize state
   - Use contexts for persistent state
   - Be careful with global state

## Future Improvements

1. **Async Support**
   - Parallel tool execution
   - Non-blocking operations
   - Event-driven tools

2. **Better Security**
   - Improved tool verification
   - Permission system
   - Sandboxing

3. **Tool Composition**
   - Combining tools
   - Tool pipelines
   - Tool dependencies 

## Tool Requirements

1. **Agent Identity Parameter**
   ```python
   @tool
   def my_tool(agent_identity: AgentIdentity, arg1: str) -> str:
       """Tool documentation string"""
       # agent_identity is always the first parameter
       return "Action completed: modified user preference"  # Must return descriptive result
   ```

2. **Return Value**
   - Must return a non-empty string describing the result
   - String should explain what action was taken
   - Helps agent understand tool execution outcome
   - Examples:
     ```python
     # Good return values:
     return "Memory added: User prefers dark mode"
     return "Error: Invalid category provided"
     return "Updated persona to: Math Teacher"
     
     # Bad return values:
     return ""  # Empty string not allowed
     return None  # Must return string
     return "Done"  # Too vague
     ```

3. **Error Handling**
   ```python
   @tool
   def safe_tool(agent_identity: AgentIdentity) -> str:
       try:
           # Tool implementation
           return "Successfully performed action X"  # Describe success
       except Exception as e:
           return f"Error: {str(e)}"  # Describe failure
   ```