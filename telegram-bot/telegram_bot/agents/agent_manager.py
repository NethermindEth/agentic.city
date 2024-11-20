"""Module for managing agent lifecycle, persistence, and interactions."""

import atexit
import logging
import os
from pathlib import Path
from threading import Event, Timer
from typing import Dict, Optional

from swarmer.agent import Agent
from swarmer.contexts.crypto_context import CryptoContext
from swarmer.contexts.debug_context import DebugContext
from swarmer.contexts.memory_context import MemoryContext
from swarmer.contexts.persona_context import PersonaContext
from swarmer.contexts.search_context import SearchContext
from swarmer.contexts.time_context import TimeContext
from swarmer.contexts.tool_creation_context import ToolCreationContext
from swarmer.debug_ui.server import DebugUIServer
from swarmer.globals.agent_registry import agent_registry

logger = logging.getLogger(__name__)


class AgentManager:
    """Manages the lifecycle, persistence, and interactions of agents in the system.

    Handles agent creation, saving, loading, and cleanup operations. Also manages
    the debug UI interface if enabled.
    """

    def __init__(
        self,
        save_dir: str = "data/agents",
        autosave_interval: int = 20,
        debug_ui: bool = True,
    ):
        """Initialize the AgentManager.

        Args:
            save_dir: Directory where agent data will be saved
            autosave_interval: Time in seconds between autosaves
            debug_ui: Whether to enable the debug UI interface
        """
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
        """Set up periodic autosave for all agents."""
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
        """Gracefully shut down the agent manager and save all agents."""
        logger.info("Shutting down AgentManager...")
        self._stop_event.set()

        # Cancel autosave timer
        if self._autosave_timer:
            self._autosave_timer.cancel()

        # Final save
        self.save_all_agents()

        # Shutdown debug UI
        if self.debug_ui:
            if hasattr(self.debug_ui, "server"):
                self.debug_ui.server.shutdown()
            self._stop_event.set()

        logger.info("AgentManager shutdown complete")

    def get_agent_path(self, user_id: int) -> Path:
        """Get the file path for a user's agent.

        Args:
            user_id: The unique identifier for the user

        Returns:
            Path to the agent's save file
        """
        return self.save_dir / f"agent_{user_id}.pkl"

    def create_agent(self, user_id: int) -> Agent:
        """Create a new agent for a user.

        Args:
            user_id: The unique identifier for the user

        Returns:
            Newly created Agent instance
        """
        agent = Agent(f"User_{user_id}", token_budget=100000, model="gpt-4")
        agent_registry.registry[agent.identity.id] = agent

        # Initialize and register contexts
        persona_context = PersonaContext()
        memory_context = MemoryContext()
        time_context = TimeContext()
        crypto_context = CryptoContext()
        debug_context = DebugContext()
        tool_creation_context = ToolCreationContext()
        search_context = SearchContext()

        agent.register_context(persona_context)
        agent.register_context(memory_context)
        agent.register_context(time_context)
        agent.register_context(crypto_context)
        agent.register_context(debug_context)
        agent.register_context(tool_creation_context)
        agent.register_context(search_context)

        # Create agent's tools directory
        tools_dir = (
            Path(os.getenv("AGENT_TOOLS_DIRECTORY", "agent_tools")) / agent.identity.id
        )
        tools_dir.mkdir(parents=True, exist_ok=True)

        self.agents[user_id] = agent
        return agent

    def get_or_create_agent(self, user_id: int) -> Agent:
        """Get an existing agent or create a new one.

        Args:
            user_id: The unique identifier for the user

        Returns:
            Existing or newly created Agent instance
        """
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
                tools_dir = (
                    Path(os.getenv("AGENT_TOOLS_DIRECTORY", "agent_tools"))
                    / agent.identity.id
                )
                tools_dir.mkdir(parents=True, exist_ok=True)
                return agent

            except Exception as e:
                logger.error(f"Failed to load agent for user {user_id}: {e}")
                agent = self.create_agent(user_id)
                return agent
        else:
            # Create new if not found
            agent = self.create_agent(user_id)
            return agent

    def save_agent(self, user_id: int) -> None:
        """Save a specific agent to disk.

        Args:
            user_id: The unique identifier for the user whose agent should be saved
        """
        if user_id not in self.agents:
            return

        agent_path = self.get_agent_path(user_id)
        try:
            Agent.save_state(self.agents[user_id], str(agent_path))
        except Exception as e:
            logger.error(f"Failed to save agent for user {user_id}: {e}")

    def save_all_agents(self) -> None:
        """Save all active agents to disk."""
        for user_id in self.agents:
            self.save_agent(user_id)

    def remove_agent(self, user_id: int) -> None:
        """Remove an agent for a user.

        Args:
            user_id: The unique identifier for the user whose agent should be removed
        """
        if user_id not in self.agents:
            return

        # Remove from memory and registry
        agent = self.agents.pop(user_id)
        agent_registry.registry.pop(agent.identity.id, None)

        # Remove from disk
        agent_path = self.get_agent_path(user_id)
        if agent_path.exists():
            try:
                agent_path.unlink()
            except Exception as e:
                logger.error(f"Failed to delete agent file for user {user_id}: {e}")

        # Remove from debug UI
        if self.debug_ui and user_id in self.agents:
            agent = self.agents[user_id]
            if hasattr(agent.identity, "user_id"):
                self.debug_ui.agents.pop(int(agent.identity.user_id), None)

        logger.info(f"Removed agent for user {user_id}")


# Global agent manager instance
agent_manager = AgentManager()
