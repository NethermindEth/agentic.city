from typing import List
from swarmer.tools.utils import tool, ToolResponse
from swarmer.tools.dependencies import requires
from swarmer.swarmer_types import AgentIdentity

@requires('googlesearch-python')
@tool
def search_google(agent_identity: AgentIdentity, query: str, num_results: int = 5) -> ToolResponse:
    """
    Search Google for the given query and return results.
    
    Args:
        agent_identity: The identity of the agent making the request
        query: The search query
        num_results: Maximum number of results to return (default: 5)
        
    Returns:
        ToolResponse containing search results with titles, links and descriptions
    """
    try:
        from googlesearch import search  # type: ignore
        
        # search() returns an iterator of URLs
        results = list(search(query, num_results=num_results, advanced=True))
        
        formatted_results = [
            {
                'title': result.title or 'No title available',
                'link': result.url,
                'description': result.description or 'No description available'
            }
            for result in results
        ]
        
        summary = f"Found {len(formatted_results)} results for '{query}'"
        return ToolResponse(
            summary=summary,
            content=formatted_results,
            error=None
        )
    except Exception as e:
        error_msg = f"Search failed: {str(e)}"
        return ToolResponse(
            summary=error_msg,
            content=[],
            error=error_msg
        )
