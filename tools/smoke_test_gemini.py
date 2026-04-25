import asyncio
from playwright.async_api import async_playwright

async def test():
    try:
        async with async_playwright() as p:
            browser = await p.chromium.connect_over_cdp("http://localhost:9222")
            context = browser.contexts[0]
            # Find the active gemini page
            page = None
            for p_obj in context.pages:
                if "gemini.google.com" in p_obj.url:
                    page = p_obj
                    break
            
            if not page:
                print("Gemini page not found. Opening new one...")
                page = await context.new_page()
                await page.goto("https://gemini.google.com/app")
            
            print(f"Connected to: {page.url}")
            input_selector = "div[contenteditable='true'][role='textbox']"
            await page.wait_for_selector(input_selector)
            await page.fill(input_selector, "冒煙測試：請回覆「系統接管成功」並加上一段關於企業法遵的小建議。")
            await page.keyboard.press("Enter")
            
            print("Message sent, waiting for response...")
            await asyncio.sleep(10)
            
            responses = await page.query_selector_all(".model-response-text")
            if responses:
                print("--- GEMINI RESPONSE ---")
                print(await responses[-1].inner_text())
                print("-----------------------")
            else:
                print("Could not find response text.")
                
    except Exception as e:
        print(f"Test failed: {e}")

if __name__ == "__main__":
    asyncio.run(test())
