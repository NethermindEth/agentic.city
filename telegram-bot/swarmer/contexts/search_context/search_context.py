from typing import Optional, cast, List
from uuid import uuid4
from swarmer.types import AgentIdentity, Context, Tool
from swarmer.tools.google_search import search_google
from swarmer.tools.web_reader import read_webpage

class SearchContext(Context):
    """Context for web search and content reading tools."""
    
    def __init__(self) -> None:
        self.tools: List[Tool] = []  # Initialize tools list
        self.tools.extend([
            cast(Tool, search_google),
            cast(Tool, read_webpage)
        ])
        self.id = str(uuid4())
    
    def get_context(self, agent: AgentIdentity) -> Optional[str]:
        """No persistent context needed for search tools."""
        return None
    
    def get_context_instructions(self, agent: AgentIdentity) -> Optional[str]:
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
        return {
            "id": self.id
        }
    
    def deserialize(self, state: dict, agent_identity: AgentIdentity) -> None:
        """Load state into context - SearchContext is stateless."""
        self.id = state["id"]
