import os
import asyncio
from mcp.server.fastmcp import FastMCP
from playwright.async_api import async_playwright

# Initialize FastMCP server
mcp = FastMCP("Gemini Web Oracle")

GEMINI_URL = "https://gemini.google.com/app"

@mcp.tool()
async def gemini_web_chat(prompt: str) -> str:
    """
    Send a prompt to Gemini Web (Pro) and capture the response.
    Requires an authenticated session in the automated browser.
    """
    async with async_playwright() as p:
        # We use a persistent context to stay logged in
        user_data_dir = os.path.join(os.getcwd(), ".gemini_web_session")
        context = await p.chromium.launch_persistent_context(
            user_data_dir,
            headless=False, # Set to False for first-time login or debugging
            args=["--remote-debugging-port=9223"]
        )
        
        page = await context.new_page()
        await page.goto(GEMINI_URL)
        
        # Check if we need to login
        if "signin" in page.url:
            return "Error: Please log in to Gemini in the opened browser window first."
            
        try:
            # Locate the input area (Gemini's specific selector)
            # This is subject to change by Google, N7 will monitor
            input_selector = "div[contenteditable='true'][role='textbox']"
            await page.wait_for_selector(input_selector, timeout=10000)
            
            # Type the prompt
            await page.fill(input_selector, prompt)
            await page.keyboard.press("Enter")
            
            # Wait for response (look for the stop button or wait for text stability)
            # This is a simplified logic, real implementation will use mutation observers
            await asyncio.sleep(15) # Wait for initial generation
            
            # Capture the last response block
            responses = await page.query_selector_all(".model-response-text")
            if responses:
                last_response = await responses[-1].inner_text()
                return last_response
            else:
                return "Error: Could not capture response from Gemini Web."
                
        except Exception as e:
            return f"Error during Gemini Web automation: {str(e)}"
        finally:
            await context.close()

if __name__ == "__main__":
    mcp.run()
