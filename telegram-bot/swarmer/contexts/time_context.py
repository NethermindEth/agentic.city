from typing import Optional
from uuid import uuid4
import time
from datetime import datetime, timezone
from swarmer.tools.utils import tool, ToolResponse
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
    def get_current_time(self, agent_identity: AgentIdentity, format: str = "iso") -> ToolResponse:
        """Get the current time in UTC.
        
        Args:
            agent_identity: The agent requesting the time
            format: Output format ('iso', 'unix', or 'human')
            
        Returns:
            ToolResponse containing the current time in requested format
        """
        now = datetime.now(timezone.utc)
        
        try:
            if format == "unix":
                unix_time = int(now.timestamp())
                return ToolResponse(
                    summary=f"Current Unix timestamp: {unix_time}",
                    content={
                        "timestamp": unix_time,
                        "format": "unix"
                    },
                    error=None
                )
            elif format == "human":
                human_time = now.strftime('%B %d, %Y %H:%M:%S')
                return ToolResponse(
                    summary=f"Current time (UTC): {human_time}",
                    content={
                        "time": human_time,
                        "format": "human"
                    },
                    error=None
                )
            else:  # iso format
                iso_time = now.isoformat()
                return ToolResponse(
                    summary=f"Current ISO time: {iso_time}",
                    content={
                        "time": iso_time,
                        "format": "iso"
                    },
                    error=None
                )
        except Exception as e:
            error_msg = f"Error getting current time: {str(e)}"
            return ToolResponse(
                summary=error_msg,
                content=None,
                error=error_msg
            )

    @tool
    def format_timestamp(
        self,
        agent_identity: AgentIdentity,
        timestamp: float,
        format: str = "human"
    ) -> ToolResponse:
        """Format a Unix timestamp into a human-readable string.
        
        Args:
            agent_identity: The agent requesting formatting
            timestamp: Unix timestamp to format
            format: Output format ('iso', 'human')
            
        Returns:
            ToolResponse containing the formatted time string
        """
        try:
            dt = datetime.fromtimestamp(timestamp, timezone.utc)
            if format == "iso":
                iso_time = dt.isoformat()
                return ToolResponse(
                    summary=f"Formatted time: {iso_time}",
                    content={
                        "time": iso_time,
                        "format": "iso",
                        "input_timestamp": timestamp
                    },
                    error=None
                )
            else:  # human
                human_time = dt.strftime('%B %d, %Y %H:%M:%S')
                return ToolResponse(
                    summary=f"Formatted time: {human_time} UTC",
                    content={
                        "time": human_time,
                        "format": "human",
                        "input_timestamp": timestamp
                    },
                    error=None
                )
        except ValueError as e:
            error_msg = f"Error formatting timestamp: {str(e)}"
            return ToolResponse(
                summary=error_msg,
                content=None,
                error=error_msg
            )

    @tool
    def get_time_difference(
        self,
        agent_identity: AgentIdentity,
        timestamp1: float,
        timestamp2: float
    ) -> ToolResponse:
        """Calculate the difference between two Unix timestamps.
        
        Args:
            agent_identity: The agent requesting the calculation
            timestamp1: First Unix timestamp
            timestamp2: Second Unix timestamp
            
        Returns:
            ToolResponse containing the time difference in seconds and a human-readable format
        """
        try:
            diff_seconds = abs(timestamp2 - timestamp1)
            days = int(diff_seconds // (24 * 3600))
            remaining = diff_seconds % (24 * 3600)
            hours = int(remaining // 3600)
            remaining %= 3600
            minutes = int(remaining // 60)
            seconds = int(remaining % 60)
            
            human_diff = []
            if days > 0:
                human_diff.append(f"{days} days")
            if hours > 0:
                human_diff.append(f"{hours} hours")
            if minutes > 0:
                human_diff.append(f"{minutes} minutes")
            if seconds > 0 or not human_diff:
                human_diff.append(f"{seconds} seconds")
                
            human_readable = ", ".join(human_diff)
            
            return ToolResponse(
                summary=f"Time difference: {human_readable}",
                content={
                    "difference_seconds": diff_seconds,
                    "human_readable": human_readable,
                    "components": {
                        "days": days,
                        "hours": hours,
                        "minutes": minutes,
                        "seconds": seconds
                    },
                    "timestamps": {
                        "first": timestamp1,
                        "second": timestamp2
                    }
                },
                error=None
            )
        except Exception as e:
            error_msg = f"Error calculating time difference: {str(e)}"
            return ToolResponse(
                summary=error_msg,
                content=None,
                error=error_msg
            )

    def serialize(self) -> dict:
        """Serialize context state - TimeContext is stateless."""
        return {
            "id": self.id
        }

    def deserialize(self, state: dict, agent_identity: AgentIdentity) -> None:
        """Load state into context - TimeContext is stateless."""
        self.id = state["id"]
