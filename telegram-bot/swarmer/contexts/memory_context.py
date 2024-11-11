from typing import Optional, Dict, List, Tuple
from uuid import UUID, uuid4
import json
import time
from dataclasses import dataclass
from swarmer.tools.utils import function_to_schema, tool
from swarmer.types import AgentIdentity, Context, Tool
from swarmer.globals.agent_registry import agent_registry

@dataclass
class MemoryEntry:
    """Represents a single memory entry with metadata.
    
    Attributes:
        content (str): The actual memory content
        timestamp (float): When the memory was created/updated
        importance (int): Importance score (1-10)
        category (str): Type of memory (e.g., "user_preference", "goal", "fact")
        source (str): Where this memory came from (e.g., "user", "inference")
    """
    content: str
    timestamp: float
    importance: int
    category: str
    source: str

class MemoryContext(Context):
    """Context for managing an agent's long-term memory.

    This context allows agents to store and retrieve important information across
    conversations. Memories can include user preferences, conversation goals,
    learned facts, and other persistent information.

    Memory entries should be concise and focused on truly important information.
    Agents should actively maintain their memories by adding new insights and
    updating existing ones."""
    
    tools: List[Tool] = []
    # agent_id -> {memory_id -> MemoryEntry}

    def __init__(self) -> None:
        self.agent_memories: Dict[str, Dict[str, MemoryEntry]] = {}
        self.tools.extend([
            self.add_memory,
            self.get_memories_by_category,
            self.update_memory,
            self.remove_memory
        ])
        self.id = str(uuid4())

    def get_context_instructions(self, agent: AgentIdentity) -> Optional[str]:
        return """
        # Memory
        You have access to a persistent memory system. Use it to maintain important
        information across conversations. Use memory proactively. Anything you think
        is relevant to rememeber, you should add to memory. Follow these guidelines:

        1. Memory Management:
           - Store concise, important facts about users and conversations
           - Add new insights as you learn them
           - Update outdated information
           - Remove irrelevant memories

        2. When to Add Memories:
           - User preferences and characteristics
           - Important goals or tasks
           - Key facts learned during conversation
           - Significant context that might be useful later

        3. Memory Quality:
           - Keep memories concise and specific
           - Include source of information
           - Rate importance appropriately
           - Categorize memories properly

        4. Categories:
           - user_preference: User likes, dislikes, preferences
           - goal: Active goals or tasks
           - fact: General facts about the user or situation
           - context: Important contextual information

        Only mention memory capabilities if relevant to the conversation.
        """

    def get_context(self, agent: AgentIdentity) -> Optional[str]:
        """Return relevant memories for the current context."""
        memories = self.agent_memories.get(agent.id, {})
        if not memories:
            return None
            
        # Format memories by category
        categorized: Dict[str, List[Tuple[str, str]]] = {}
        for memory_id, memory in memories.items():
            if memory.category not in categorized:
                categorized[memory.category] = []
            categorized[memory.category].append((memory_id, memory.content))

        # Build context string
        context_parts = ["Current memories:"]
        for category, items in categorized.items():
            context_parts.append(f"\n{category.replace('_', ' ').title()}:")
            for memory_id, content in items:
                context_parts.append(f"- {content} (ID: {memory_id})")

        return "\n".join(context_parts)

    def _get_agent_memories(self, agent_identity: AgentIdentity) -> Dict[str, MemoryEntry]:
        """Get or initialize agent's memory store."""
        if agent_identity.id not in self.agent_memories:
            self.agent_memories[agent_identity.id] = {}
        return self.agent_memories[agent_identity.id]

    @tool
    def add_memory(
        self,
        agent_identity: AgentIdentity,
        content: str,
        importance: int,
        category: str,
        source: str
    ) -> str:
        """Add a new memory for the agent.
        
        Args:
            agent_identity: The agent adding the memory
            content: The memory content (keep concise and specific)
            importance: Importance score (1-10)
            category: Type of memory (user_preference, goal, fact, context)
            source: Where this memory came from (user, inference)
            
        Returns:
            Confirmation message
        """

        if not 1 <= importance <= 10:
            return "Failed to add memory: Importance must be between 1 and 10"
            
        valid_categories = ["user_preference", "goal", "fact", "context"]
        if category not in valid_categories:
            return f"Failed to add memory: Category must be one of {valid_categories}"

        memory = MemoryEntry(
            content=content,
            timestamp=time.time(),
            importance=importance,
            category=category,
            source=source
        )
        
        memory_id = str(uuid4())
        memories = self._get_agent_memories(agent_identity)
        memories[memory_id] = memory
        
        return f"Added new memory (ID: {memory_id}):\nContent: {content}\nCategory: {category}\nImportance: {importance}"

    @tool
    def get_memories_by_category(
        self,
        agent_identity: AgentIdentity,
        category: str
    ) -> str:
        """Retrieve all memories of a specific category.
        
        Args:
            agent_identity: The agent retrieving memories
            category: Category to filter by
            
        Returns:
            Formatted string of matching memories
        """
        memories = self._get_agent_memories(agent_identity)
        matching = {
            mid: m for mid, m in memories.items()
            if m.category == category
        }
        
        if not matching:
            return f"No memories found in category '{category}'"
        
        result = [f"Found {len(matching)} memories in category '{category}':"]
        for mid, memory in matching.items():
            result.append(f"- {memory.content} (Importance: {memory.importance}, Source: {memory.source})")
        
        return "\n".join(result)

    @tool
    def update_memory(
        self,
        agent_identity: AgentIdentity,
        memory_id: str,
        content: str,
        importance: Optional[int] = None
    ) -> str:
        """Update an existing memory.
        
        Args:
            agent_identity: The agent updating the memory
            memory_id: ID of the memory to update
            content: New memory content
            importance: New importance score (optional)
            
        Returns:
            Confirmation message
        """
        memories = self._get_agent_memories(agent_identity)
        if memory_id not in memories:
            return f"Failed to update: Memory {memory_id} not found"
            
        memory = memories[memory_id]
        old_content = memory.content
        memory.content = content
        memory.timestamp = time.time()
        
        changes = [f"Content: {old_content} → {content}"]
        
        if importance is not None:
            if not 1 <= importance <= 10:
                return "Failed to update: Importance must be between 1 and 10"
            old_importance = memory.importance
            memory.importance = importance
            changes.append(f"Importance: {old_importance} → {importance}")
            
        return f"Updated memory (ID: {memory_id}):\n" + "\n".join(changes)

    @tool
    def remove_memory(
        self,
        agent_identity: AgentIdentity,
        memory_id: str
    ) -> str:
        """Remove a memory.
        
        Args:
            agent_identity: The agent removing the memory
            memory_id: ID of the memory to remove
            
        Returns:
            Confirmation message
        """
        memories = self._get_agent_memories(agent_identity)
        if memory_id not in memories:
            return f"Failed to remove: Memory {memory_id} not found"
            
        memory = memories[memory_id]
        del memories[memory_id]
        return f"Removed memory (ID: {memory_id}):\nContent: {memory.content}\nCategory: {memory.category}"

    def serialize(self) -> dict:
        """Serialize context state"""
        return {
            "id": self.id,
            "agent_memories": {
                agent_id: {
                    memory_id: {
                        "content": memory.content,
                        "importance": memory.importance,
                        "category": memory.category,
                        "source": memory.source,
                        "timestamp": memory.timestamp
                    }
                    for memory_id, memory in memories.items()
                }
                for agent_id, memories in self.agent_memories.items()
            }
        }

    def deserialize(self, state: dict, agent_identity: AgentIdentity) -> None:
        """Load state into this context instance"""
        self.id = state["id"]
        
        # Restore memories
        self.agent_memories = {
            agent_id: {
                memory_id: MemoryEntry(**memory_data)
                for memory_id, memory_data in memories.items()
            }
            for agent_id, memories in state["agent_memories"].items()
        }