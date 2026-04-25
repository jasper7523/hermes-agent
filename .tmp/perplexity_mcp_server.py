import sys
import asyncio
from mcp.server.fastmcp import FastMCP
from pathlib import Path

# Add hermes-agent to path to load perplexity_search
HERMES_AGENT_DIR = Path(r"d:\hermes-agent")
sys.path.append(str(HERMES_AGENT_DIR / "scripts"))

from perplexity_search import PerplexityCDP

mcp = FastMCP("perplexity-cdp-server")

@mcp.tool()
async def search_perplexity_pro(query: str) -> str:
    """
    Search using Perplexity Pro (CDP automation).
    Uses the local Chrome browser instance connected to Perplexity to run the query and retrieve Markdown output.
    Returns the markdown result or an error message.
    """
    try:
        client = PerplexityCDP()
        result = await client.search(query)
        return result
    except Exception as e:
        return f"Error executing Perplexity Search: {str(e)}"

if __name__ == "__main__":
    mcp.run(transport='stdio')
