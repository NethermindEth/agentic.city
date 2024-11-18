import os
import json
import logging
from typing import Dict, Optional
from pathlib import Path
import atexit
from threading import Timer, Event
from swarmer.agent import Agent
from swarmer.globals.agent_registry import agent_registry
from swarmer.contexts.persona_context import PersonaContext
from swarmer.contexts.memory_context import MemoryContext
from swarmer.contexts.time_context import TimeContext
from swarmer.contexts.crypto_context import CryptoContext
from swarmer.contexts.debug_context import DebugContext
from swarmer.contexts.tool_creation_context import ToolCreationContext
from swarmer.debug_ui.server import DebugUIServer

logger = logging.getLogger(__name__)

class AgentManager:
    def __init__(self, save_dir: str = "data/agents", autosave_interval: int = 20, debug_ui: bool = True):
        self.agents: Dict[int, Agent] = {}
        self.save_dir = Path(save_dir)
        self.save_dir.mkdir(parents=True, exist_ok=True)
        self.autosave_interval = autosave_interval
        self._stop_event = Event()
        self._autosave_timer: Optional[Timer] = None
        self._setup_autosave()
        atexit.register(self.shutdown)

        # Initialize debug UI if enabled
        self.debug_ui = DebugUIServer() if debug_ui else None
        if self.debug_ui:
            self.debug_ui.start()

    def _setup_autosave(self) -> None:
        """Setup periodic autosave"""
        if self._stop_event.is_set():
            return
            
        def schedule_next_save() -> None:
            if not self._stop_event.is_set():
                self.save_all_agents()
                self._autosave_timer = Timer(self.autosave_interval, schedule_next_save)
                self._autosave_timer.daemon = True
                self._autosave_timer.start()
        
        self._autosave_timer = Timer(self.autosave_interval, schedule_next_save)
        self._autosave_timer.daemon = True
        self._autosave_timer.start()

    def shutdown(self) -> None:
        """Gracefully shutdown the agent manager"""
        logger.info("Shutting down AgentManager...")
        self._stop_event.set()
        
        # Cancel autosave timer
        if self._autosave_timer:
            self._autosave_timer.cancel()
        
        # Final save
        self.save_all_agents()
        
        # Shutdown debug UI
        if self.debug_ui:
            self.debug_ui.shutdown()
        
        logger.info("AgentManager shutdown complete")

    def get_agent_path(self, user_id: int) -> Path:
        """Get the file path for a user's agent"""
        return self.save_dir / f"agent_{user_id}.pkl"

    def create_agent(self, user_id: int) -> Agent:
        """Create a new agent for a user"""
        agent = Agent(f"User_{user_id}", token_budget=100000, model="gpt-4")
        agent_registry.registry[agent.identity.id] = agent

        # Initialize and register contexts
        persona_context = PersonaContext()
        memory_context = MemoryContext()
        time_context = TimeContext()
        crypto_context = CryptoContext()
        debug_context = DebugContext()
        tool_creation_context = ToolCreationContext()

        agent.register_context(persona_context)
        agent.register_context(memory_context)
        agent.register_context(time_context)
        agent.register_context(crypto_context)
        agent.register_context(debug_context)
        agent.register_context(tool_creation_context)

        # Create agent's tools directory
        tools_dir = Path(os.getenv("AGENT_TOOLS_DIRECTORY", "agent_tools")) / agent.identity.id
        tools_dir.mkdir(parents=True, exist_ok=True)

        self.agents[user_id] = agent
        return agent

    def get_or_create_agent(self, user_id: int) -> Agent:
        """Get existing agent or create new one"""
        if user_id in self.agents:
            return self.agents[user_id]

        # Try to load from disk
        agent_path = self.get_agent_path(user_id)
        if agent_path.exists():
            try:
                agent = Agent.load_state(str(agent_path))
                self.agents[user_id] = agent
                agent_registry.registry[agent.identity.id] = agent
                logger.info(f"Loaded agent for user {user_id}")
                
                # Ensure tool directory exists after loading
                tools_dir = Path(os.getenv("AGENT_TOOLS_DIRECTORY", "agent_tools")) / agent.identity.id
                tools_dir.mkdir(parents=True, exist_ok=True)
                
            except Exception as e:
                import traceback
                logger.error(f"Failed to load agent for user {user_id}: {e}")
                agent = self.create_agent(user_id)
        else:
            # Create new if not found
            agent = self.create_agent(user_id)

        # Register with debug UI if enabled
        if self.debug_ui:
            self.debug_ui.register_agent(user_id, agent)

        return agent

    def save_agent(self, user_id: int) -> None:
        """Save a specific agent to disk"""
        if user_id not in self.agents:
            return

        agent_path = self.get_agent_path(user_id)
        try:
            Agent.save_state(self.agents[user_id], str(agent_path))
        except Exception as e:
            logger.error(f"Failed to save agent for user {user_id}: {e}")

    def save_all_agents(self) -> None:
        """Save all agents to disk"""
        for user_id in self.agents:
            self.save_agent(user_id)

    def remove_agent(self, user_id: int) -> bool:
        """Remove an agent for a user"""
        if user_id not in self.agents:
            return False

        # Remove from memory
        agent = self.agents.pop(user_id)
        agent_registry.registry.pop(agent.identity.id, None)

        # Remove from debug UI if enabled
        if self.debug_ui:
            self.debug_ui.unregister_agent(user_id)

        # Remove from disk
        agent_path = self.get_agent_path(user_id)
        try:
            if agent_path.exists():
                agent_path.unlink()
            
            # Also remove any associated crypto keys
            key_path = Path(os.getenv("KEYS_DIRECTORY", "secure/keys")) / f"{agent.identity.id}.key"
            if key_path.exists():
                key_path.unlink()
                
            # Remove agent's tools directory
            tools_dir = Path(os.getenv("AGENT_TOOLS_DIRECTORY", "agent_tools")) / agent.identity.id
            if tools_dir.exists():
                import shutil
                shutil.rmtree(tools_dir)
                
            return True
        except Exception as e:
            logger.error(f"Failed to remove agent file for user {user_id}: {e}")
            return False

# Global agent manager instance
agent_manager = AgentManager()