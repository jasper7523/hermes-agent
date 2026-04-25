from mcp.server.fastmcp import FastMCP
import asyncio
import sys
import os

# Add scripts dir to path to import perplexity_search
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from perplexity_search import perplexity_search

# Initialize FastMCP Server
mcp = FastMCP("Perplexity-CDP-MCP")

@mcp.tool()
async def search_perplexity(query: str) -> str:
    """
    Search Perplexity using the local CDP Desktop App.
    Use this tool to get up-to-date internet research, academic references, or real-time web answers.
    It returns a fully formatted Markdown string with inline citations.
    """
    # Since perplexity_search inside uses asyncio.run() and we are in an async context,
    # we should run it in a thread executor, or we can just call the underlying client directly.
    # To keep it safe and avoid nested event loops:
    from perplexity_search import PerplexityCDP
    client = PerplexityCDP()
    try:
        return await client.search(query)
    except Exception as e:
        return f"Error connecting to Perplexity App: {str(e)}"

if __name__ == "__main__":
    # Start the stdio server
    mcp.run()
