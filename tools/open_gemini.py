import asyncio
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        await page.goto("https://gemini.google.com")
        print("Browser opened. Please login.")
        await asyncio.sleep(120)  # Give user 2 minutes to login
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
