"""Module implementing web search functionality for agents."""

from typing import Any, Dict, List
from uuid import uuid4

from swarmer.swarmer_types import AgentIdentity, Context, Tool
from swarmer.tools.google_search import search_google
from swarmer.tools.web_reader import read_webpage


class SearchContext(Context):
    """Context for performing web searches and retrieving information.

    This context provides tools for agents to search the web and retrieve
    information using various search engines and methods.
    """

    def __init__(self) -> None:
        """Initialize search context with web search tools."""
        super().__init__()
        self.tools: List[Tool] = []  # Initialize tools list
        # Cast the functions to Tool type since they should implement the protocol
        self.tools.extend([Tool(search_google), Tool(read_webpage)])  # type: ignore
        self.id = str(uuid4())

    def get_context(self, agent: AgentIdentity) -> Dict[str, Any]:
        """Get the current search context.

        Args:
            agent: The agent requesting context.

        Returns:
            Current search state and available tools.
        """
        return {
            "current_query": None,
            "tools": [tool.__name__ for tool in self.tools],
        }

    def get_context_instructions(self, agent: AgentIdentity) -> str:
        """Get instructions for using the search context.

        Args:
            agent: The identity of the agent requesting instructions.

        Returns:
            Instructions for using search tools.
        """
        return """
        You have access to web search and content reading tools that allow you to:
        1. Search Google for information
        2. Read and extract content from web pages

        Use these capabilities when you need to:
        - Find information on the web
        - Read and analyze webpage content
        - Research topics or answer questions

        The tools will handle:
        - Search result formatting
        - Content extraction and cleaning
        - Error handling and rate limiting
        """

    def serialize(self) -> dict:
        """Serialize context state - SearchContext is stateless."""
        return {"id": self.id}

    def deserialize(self, state: dict, agent_identity: AgentIdentity) -> None:
        """Load state into context - SearchContext is stateless."""
        self.id = state["id"]
