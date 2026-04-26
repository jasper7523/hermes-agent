import os
import json
import httpx
from mcp.server.fastmcp import FastMCP

# Initialize FastMCP server
mcp = FastMCP("Ollama Local Oracle")

OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://127.0.0.1:11434/api")

@mcp.tool()
async def ollama_chat(prompt: str, model: str = "gemma4:latest", system_prompt: str = "") -> str:
    """
    Chat with a local Ollama model.
    Use this for cost-free inference or sensitive legal data.
    """
    url = f"{OLLAMA_URL}/generate"
    
    payload = {
        "model": model,
        "prompt": prompt,
        "system": system_prompt,
        "stream": False,
        "options": {
            "temperature": 0.7,
            "num_predict": 2048
        }
    }
    
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            result = response.json()
            return result.get("response", "Error: Empty response from Ollama.")
    except Exception as e:
        return f"Error connecting to Ollama: {str(e)}"

@mcp.tool()
async def ollama_list_models() -> str:
    """
    List all available models in the local Ollama instance.
    """
    url = f"{OLLAMA_URL}/tags"
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url)
            response.raise_for_status()
            models = response.json().get("models", [])
            names = [m["name"] for m in models]
            return f"Available Ollama Models: {', '.join(names)}"
    except Exception as e:
        return f"Error fetching Ollama models: {str(e)}"

if __name__ == "__main__":
    mcp.run()
