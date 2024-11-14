from typing import Optional, Dict, List
from uuid import UUID, uuid4
import time
from dataclasses import dataclass
from swarmer.tools.utils import tool
from swarmer.types import AgentIdentity, Context, Tool

@dataclass
class MemoryEntry:
    """Represents a single memory entry with metadata.
    
    Attributes:
        content (str): The actual memory content
        timestamp (float): When the memory was created/updated
        importance (int): Importance score (1-10)
    """
    content: str
    timestamp: float
    importance: int

class MemoryContext(Context):
    """Context for managing an agent's long-term memory.

    This context allows agents to store and retrieve important information across
    conversations. Memories can include user preferences, conversation history,
    learned facts, and other persistent information.

    Memory entries should be concise and focused on truly important information."""
    
    tools: List[Tool] = []

    def __init__(self) -> None:
        self.agent_memories: Dict[str, Dict[str, MemoryEntry]] = {}
        self.tools.extend([
            self.add_memory,
            self.get_memories,
            self.update_memory,
            self.remove_memory
        ])
        self.id = str(uuid4())

    def get_context_instructions(self, agent: AgentIdentity) -> Optional[str]:
        return """
        # Memory
        You have access to a persistent memory system. Use it to maintain important
        information across conversations. Use memory proactively - anything you think
        is relevant to remember, you should add to memory. Follow these guidelines:

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
           - Rate importance appropriately (1-10)
           - More important memories (8-10) should be key facts that significantly impact interactions
           - Less important memories (1-4) can be minor preferences or temporary context

        Only mention memory capabilities if relevant to the conversation.
        """

    def get_context(self, agent: AgentIdentity) -> Optional[str]:
        """Return relevant memories for the current context."""
        memories = self.agent_memories.get(agent.id, {})
        if not memories:
            return None
            
        # Sort memories by importance
        sorted_memories = sorted(
            memories.items(),
            key=lambda x: x[1].importance,
            reverse=True
        )

        context_parts = ["Current memories:"]
        for memory_id, memory in sorted_memories:
            context_parts.append(f"- {memory.content} (ID: {memory_id}, Importance: {memory.importance})")

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
        importance: int
    ) -> str:
        """Add a new memory for the agent.
        
        Args:
            agent_identity: The agent adding the memory
            content: The memory content (keep concise and specific)
            importance: Importance score (1-10)
            
        Returns:
            Confirmation message
        """
        if not 1 <= importance <= 10:
            return "Failed to add memory: Importance must be between 1 and 10"

        memory = MemoryEntry(
            content=content,
            timestamp=time.time(),
            importance=importance
        )
        
        memory_id = str(uuid4())
        memories = self._get_agent_memories(agent_identity)
        memories[memory_id] = memory
        
        return f"Added new memory (ID: {memory_id}):\nContent: {content}\nImportance: {importance}"

    @tool
    def get_memories(
        self,
        agent_identity: AgentIdentity,
    ) -> str:
        """Retrieve all memories.
        
        Args:
            agent_identity: The agent retrieving memories
            
        Returns:
            Formatted string of memories
        """
        memories = self._get_agent_memories(agent_identity)
        
        if not memories:
            return "No memories found"
        
        result = [f"Found {len(memories)} memories:"]
        for mid, memory in memories.items():
            result.append(f"- {memory.content} (ID: {mid}, Importance: {memory.importance})")
        
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
        return f"Removed memory (ID: {memory_id}):\nContent: {memory.content}"

    def serialize(self) -> dict:
        """Serialize context state"""
        return {
            "id": self.id,
            "agent_memories": {
                agent_id: {
                    memory_id: {
                        "content": memory.content,
                        "importance": memory.importance,
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