from typing import Optional
from uuid import uuid4
import time
from datetime import datetime, timezone
from swarmer.tools.utils import tool
from swarmer.types import AgentIdentity, Context, Tool

class TimeContext(Context):
    """Context for managing time-related operations and awareness.
    
    This context provides tools for:
    - Getting current time in different formats
    - Converting between timezones
    - Basic time calculations
    
    The context is intentionally lightweight and stateless, focusing on 
    providing time awareness to agents."""
    
    tools: list[Tool] = []

    def __init__(self) -> None:
        self.tools.extend([
            self.get_current_time,
            self.format_timestamp,
            self.get_time_difference
        ])
        self.id = str(uuid4())

    def get_context_instructions(self, agent: AgentIdentity) -> Optional[str]:
        return """
        You have access to time-related tools that allow you to:
        1. Get the current time in different formats
        2. Format timestamps into human-readable strings
        3. Calculate time differences
        
        Use these capabilities when:
        - Referencing the current time
        - Discussing time periods
        - Calculating durations
        
        Time is always handled in UTC to avoid timezone confusion.
        Don't mention time capabilities just use the tooling to be accurate
        """

    def get_context(self, agent: AgentIdentity) -> Optional[str]:
        """Provide current time context."""
        current_time = datetime.now(timezone.utc)
        return f"Current UTC time: {current_time.strftime('%Y-%m-%d %H:%M:%S')}"

    @tool
    def get_current_time(self, agent_identity: AgentIdentity, format: str = "iso") -> str:
        """Get the current time in UTC.
        
        Args:
            agent_identity: The agent requesting the time
            format: Output format ('iso', 'unix', or 'human')
            
        Returns:
            Current time in requested format
        """
        now = datetime.now(timezone.utc)
        
        if format == "unix":
            return f"Current Unix timestamp: {int(now.timestamp())}"
        elif format == "human":
            return f"Current time (UTC): {now.strftime('%B %d, %Y %H:%M:%S')}"
        else:  # iso format
            return f"Current ISO time: {now.isoformat()}"

    @tool
    def format_timestamp(
        self,
        agent_identity: AgentIdentity,
        timestamp: float,
        format: str = "human"
    ) -> str:
        """Format a Unix timestamp into a human-readable string.
        
        Args:
            agent_identity: The agent requesting formatting
            timestamp: Unix timestamp to format
            format: Output format ('iso', 'human')
            
        Returns:
            Formatted time string
        """
        try:
            dt = datetime.fromtimestamp(timestamp, timezone.utc)
            if format == "iso":
                return f"Formatted time: {dt.isoformat()}"
            else:  # human
                return f"Formatted time: {dt.strftime('%B %d, %Y %H:%M:%S')} UTC"
        except ValueError as e:
            return f"Error formatting timestamp: {str(e)}"

    @tool
    def get_time_difference(
        self,
        agent_identity: AgentIdentity,
        timestamp1: float,
        timestamp2: float
    ) -> str:
        """Calculate the difference between two timestamps.
        
        Args:
            agent_identity: The agent requesting the calculation
            timestamp1: First Unix timestamp
            timestamp2: Second Unix timestamp
            
        Returns:
            Time difference in a human-readable format
        """
        try:
            diff_seconds = abs(timestamp2 - timestamp1)
            days = int(diff_seconds // (24 * 3600))
            remaining = diff_seconds % (24 * 3600)
            hours = int(remaining // 3600)
            remaining %= 3600
            minutes = int(remaining // 60)
            seconds = int(remaining % 60)
            
            parts = []
            if days > 0:
                parts.append(f"{days} days")
            if hours > 0:
                parts.append(f"{hours} hours")
            if minutes > 0:
                parts.append(f"{minutes} minutes")
            if seconds > 0 or not parts:
                parts.append(f"{seconds} seconds")
                
            return f"Time difference: {', '.join(parts)}"
        except ValueError as e:
            return f"Error calculating time difference: {str(e)}"

    def serialize(self) -> dict:
        """Serialize context state - TimeContext is stateless."""
        return {
            "id": self.id
        }

    def deserialize(self, state: dict, agent_identity: AgentIdentity) -> None:
        """Load state into context - TimeContext is stateless."""
        self.id = state["id"]
