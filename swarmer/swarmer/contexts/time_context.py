"""Module for managing time-related operations and scheduling."""

from datetime import datetime, timezone
from typing import Any, Dict
from uuid import uuid4

from swarmer.swarmer_types import AgentIdentity, Context, Tool
from swarmer.tools.utils import ToolResponse, tool


class TimeContext(Context):
    """Context for handling time-related operations and scheduling tasks.

    This context provides tools for agents to manage time-based operations,
    including getting current time, scheduling tasks, and managing timeouts.
    """

    tools: list[Tool] = []

    def __init__(self) -> None:
        """Initialize time context with time management tools."""
        self.tools.extend(
            [self.get_current_time, self.format_timestamp, self.get_time_difference]
        )
        self.id = str(uuid4())

    def get_context_instructions(self, agent: AgentIdentity) -> str:
        """Get instructions for using the time context.

        Args:
            agent: The agent requesting instructions.

        Returns:
            Instructions for using time-related tools.
        """
        return """
        Time Context Instructions:
        - Use time-related tools to track and manage time
        - Available tools: get_current_time, format_timestamp, get_time_difference
        """

    def get_context(self, agent: AgentIdentity) -> Dict[str, Any]:
        """Get the current time context.

        Args:
            agent: The agent requesting context.

        Returns:
            Current time state and available tools.
        """
        current_time = datetime.now(timezone.utc)
        return {
            "current_time": current_time.isoformat(),
            "timezone": "UTC",
            "tools": [tool.__name__ for tool in self.tools],
        }

    @tool
    def get_current_time(
        self, agent_identity: AgentIdentity, format: str = "iso"
    ) -> ToolResponse:
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
                    content={"timestamp": unix_time, "format": "unix"},
                    error=None,
                )
            elif format == "human":
                human_time = now.strftime("%B %d, %Y %H:%M:%S")
                return ToolResponse(
                    summary=f"Current time (UTC): {human_time}",
                    content={"time": human_time, "format": "human"},
                    error=None,
                )
            else:  # iso format
                iso_time = now.isoformat()
                return ToolResponse(
                    summary=f"Current ISO time: {iso_time}",
                    content={"time": iso_time, "format": "iso"},
                    error=None,
                )
        except Exception as e:
            error_msg = f"Error getting current time: {str(e)}"
            return ToolResponse(summary=error_msg, content=None, error=error_msg)

    @tool
    def format_timestamp(
        self, agent_identity: AgentIdentity, timestamp: float, format: str = "human"
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
                        "input_timestamp": timestamp,
                    },
                    error=None,
                )
            else:  # human
                human_time = dt.strftime("%B %d, %Y %H:%M:%S")
                return ToolResponse(
                    summary=f"Formatted time: {human_time} UTC",
                    content={
                        "time": human_time,
                        "format": "human",
                        "input_timestamp": timestamp,
                    },
                    error=None,
                )
        except ValueError as e:
            error_msg = f"Error formatting timestamp: {str(e)}"
            return ToolResponse(summary=error_msg, content=None, error=error_msg)

    @tool
    def get_time_difference(
        self, agent_identity: AgentIdentity, timestamp1: float, timestamp2: float
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
                        "seconds": seconds,
                    },
                    "timestamps": {"first": timestamp1, "second": timestamp2},
                },
                error=None,
            )
        except Exception as e:
            error_msg = f"Error calculating time difference: {str(e)}"
            return ToolResponse(summary=error_msg, content=None, error=error_msg)

    def serialize(self) -> dict:
        """Serialize context state - TimeContext is stateless."""
        return {"id": self.id}

    def deserialize(self, state: dict, agent_identity: AgentIdentity) -> None:
        """Load state into context - TimeContext is stateless."""
        self.id = state["id"]
