"""Tool for reading and processing web content.

This module provides functionality for fetching and processing content from web
pages, including text extraction and basic content analysis.
"""

from swarmer.swarmer_types import AgentIdentity
from swarmer.tools.dependencies import requires
from swarmer.tools.utils import ToolResponse, tool


@requires("requests", "beautifulsoup4")
@tool
def read_webpage(
    agent_identity: AgentIdentity, url: str, extract_text: bool = True
) -> ToolResponse:
    """Read and process content from a webpage.

    Args:
        agent_identity: The identity of the agent making the request
        url: The URL of the webpage to read.
        extract_text: Whether to extract plain text from HTML (default: True).

    Returns:
        A ToolResponse containing the processed webpage content.
    """
    try:
        import requests
        from bs4 import BeautifulSoup

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        # Get title
        title = soup.title.string if soup.title else "No title found"

        # Get main content (this is a simple implementation)
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()

        # Get text content
        text = soup.get_text()

        # Break into lines and remove leading/trailing space
        lines = (line.strip() for line in text.splitlines())
        # Break multi-headlines into a line each
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        # Drop blank lines
        content = " ".join(chunk for chunk in chunks if chunk)

        # Limit content length for summary
        summary = f"Successfully read webpage: {title}"
        content_preview = content[:200] + "..." if len(content) > 200 else content

        return ToolResponse(
            summary=summary,
            content={
                "title": title,
                "content": content[:5000],  # Limit full content length
                "preview": content_preview,
                "url": url,
            },
            error=None,
        )

    except Exception as e:
        error_msg = f"Failed to read webpage: {str(e)}"
        return ToolResponse(
            summary=error_msg,
            content={"title": "Error", "content": "", "preview": error_msg, "url": url},
            error=error_msg,
        )
