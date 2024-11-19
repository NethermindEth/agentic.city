from typing import Optional, Dict, List
from uuid import UUID, uuid4
import time
from dataclasses import dataclass
from swarmer.tools.utils import tool, ToolResponse
from swarmer.swarmer_types import AgentIdentity, Context, Tool

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

    def to_dict(self) -> dict:
        """Convert memory entry to dictionary."""
        return {
            "content": self.content,
            "timestamp": self.timestamp,
            "importance": self.importance
        }

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
    ) -> ToolResponse:
        """Add a new memory for the agent.
        
        Args:
            agent_identity: The agent adding the memory
            content: The memory content (keep concise and specific)
            importance: Importance score (1-10)
            
        Returns:
            ToolResponse containing the new memory details
        """
        if not 1 <= importance <= 10:
            error_msg = "Failed to add memory: Importance must be between 1 and 10"
            return ToolResponse(
                summary=error_msg,
                content=None,
                error=error_msg
            )

        try:
            memory = MemoryEntry(
                content=content,
                timestamp=time.time(),
                importance=importance
            )
            
            memory_id = str(uuid4())
            memories = self._get_agent_memories(agent_identity)
            memories[memory_id] = memory
            
            success_msg = f"Added new memory: {content} (Importance: {importance})"
            return ToolResponse(
                summary=success_msg,
                content={
                    "status": "success",
                    "memory": {
                        "id": memory_id,
                        **memory.to_dict()
                    }
                },
                error=None
            )
        except Exception as e:
            error_msg = f"Failed to add memory: {str(e)}"
            return ToolResponse(
                summary=error_msg,
                content=None,
                error=error_msg
            )

    @tool
    def get_memories(
        self,
        agent_identity: AgentIdentity,
    ) -> ToolResponse:
        """Retrieve all memories.
        
        Args:
            agent_identity: The agent retrieving memories
            
        Returns:
            ToolResponse containing all memories
        """
        try:
            memories = self._get_agent_memories(agent_identity)
            
            if not memories:
                return ToolResponse(
                    summary="No memories found",
                    content={"memories": []},
                    error=None
                )
            
            memory_list = []
            summary_items = []
            for mid, memory in memories.items():
                memory_list.append({
                    "id": mid,
                    **memory.to_dict()
                })
                summary_items.append(f"- {memory.content} (Importance: {memory.importance})")
            
            summary = f"Found {len(memories)} memories:\n" + "\n".join(summary_items)
            return ToolResponse(
                summary=summary,
                content={
                    "count": len(memories),
                    "memories": memory_list
                },
                error=None
            )
        except Exception as e:
            error_msg = f"Failed to retrieve memories: {str(e)}"
            return ToolResponse(
                summary=error_msg,
                content=None,
                error=error_msg
            )

    @tool
    def update_memory(
        self,
        agent_identity: AgentIdentity,
        memory_id: str,
        content: str,
        importance: Optional[int] = None
    ) -> ToolResponse:
        """Update an existing memory.
        
        Args:
            agent_identity: The agent updating the memory
            memory_id: ID of the memory to update
            content: New memory content
            importance: New importance score (optional)
            
        Returns:
            ToolResponse containing the updated memory details
        """
        try:
            memories = self._get_agent_memories(agent_identity)
            if memory_id not in memories:
                error_msg = f"Failed to update: Memory {memory_id} not found"
                return ToolResponse(
                    summary=error_msg,
                    content=None,
                    error=error_msg
                )
                
            memory = memories[memory_id]
            changes = {
                "old": memory.to_dict(),
                "new": {}
            }
            
            # Update content
            old_content = memory.content
            memory.content = content
            memory.timestamp = time.time()
            changes["new"]["content"] = content
            
            # Update importance if provided
            if importance is not None:
                if not 1 <= importance <= 10:
                    error_msg = "Failed to update: Importance must be between 1 and 10"
                    return ToolResponse(
                        summary=error_msg,
                        content=None,
                        error=error_msg
                    )
                old_importance = memory.importance
                memory.importance = importance
                changes["new"]["importance"] = importance
            else:
                changes["new"]["importance"] = memory.importance
                
            changes["new"]["timestamp"] = memory.timestamp
            
            summary = f"Updated memory: {content}"
            if importance is not None:
                summary += f" (Importance: {importance})"
                
            return ToolResponse(
                summary=summary,
                content={
                    "status": "success",
                    "memory_id": memory_id,
                    "changes": changes
                },
                error=None
            )
        except Exception as e:
            error_msg = f"Failed to update memory: {str(e)}"
            return ToolResponse(
                summary=error_msg,
                content=None,
                error=error_msg
            )

    @tool
    def remove_memory(
        self,
        agent_identity: AgentIdentity,
        memory_id: str
    ) -> ToolResponse:
        """Remove a memory.
        
        Args:
            agent_identity: The agent removing the memory
            memory_id: ID of the memory to remove
            
        Returns:
            ToolResponse containing the status of the removal operation
        """
        try:
            memories = self._get_agent_memories(agent_identity)
            if memory_id not in memories:
                error_msg = f"Failed to remove: Memory {memory_id} not found"
                return ToolResponse(
                    summary=error_msg,
                    content=None,
                    error=error_msg
                )
                
            memory = memories[memory_id]
            del memories[memory_id]
            
            return ToolResponse(
                summary=f"Removed memory: {memory.content}",
                content={
                    "status": "success",
                    "removed_memory": {
                        "id": memory_id,
                        **memory.to_dict()
                    }
                },
                error=None
            )
        except Exception as e:
            error_msg = f"Failed to remove memory: {str(e)}"
            return ToolResponse(
                summary=error_msg,
                content=None,
                error=error_msg
            )

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