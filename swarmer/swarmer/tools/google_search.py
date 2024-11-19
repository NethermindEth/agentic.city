"""Tool for performing Google searches.

This module provides functionality for executing Google searches and processing
the results in a format suitable for agent consumption.
"""

from swarmer.swarmer_types import AgentIdentity
from swarmer.tools.dependencies import requires
from swarmer.tools.utils import ToolResponse, tool


@requires("googlesearch-python")
@tool
def search_google(
    agent_identity: AgentIdentity, query: str, num_results: int = 5
) -> ToolResponse:
    """Execute a Google search and return the results.

    Args:
        agent_identity: The identity of the agent making the request
        query: The search query string.
        num_results: Number of results to return (default: 5).

    Returns:
        A ToolResponse containing the search results.
    """
    try:
        from googlesearch import search  # type: ignore

        # search() returns an iterator of URLs
        results = list(search(query, num_results=num_results, advanced=True))

        formatted_results = [
            {
                "title": result.title or "No title available",
                "link": result.url,
                "description": result.description or "No description available",
            }
            for result in results
        ]

        summary = f"Found {len(formatted_results)} results for '{query}'"
        return ToolResponse(summary=summary, content=formatted_results, error=None)
    except Exception as e:
        error_msg = f"Search failed: {str(e)}"
        return ToolResponse(summary=error_msg, content=[], error=error_msg)
