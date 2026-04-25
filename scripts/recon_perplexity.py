import time
from playwright.sync_api import sync_playwright

def run_recon():
    print("[*] Connecting to Perplexity App over CDP (Port 9222)...")
    try:
        with sync_playwright() as p:
            # Connect to the running Electron app
            browser = p.chromium.connect_over_cdp("http://localhost:9222")
            
            # Usually the first context and first page is the main App window
            default_context = browser.contexts[0]
            page = default_context.pages[0]
            
            print(f"[*] Connected! Current URL: {page.url}")
            print(f"[*] Page Title: {page.title()}")
            
            # Save a screenshot
            screenshot_path = "d:/hermes-agent/scratch/perplexity_recon.png"
            page.screenshot(path=screenshot_path)
            print(f"[+] Saved screenshot to {screenshot_path}")
            
            # Save the DOM HTML
            html_path = "d:/hermes-agent/scratch/perplexity_dom.html"
            with open(html_path, "w", encoding="utf-8") as f:
                f.write(page.content())
            print(f"[+] Saved DOM to {html_path}")
            
            # Let's also do a quick evaluation to find textareas (the input box)
            textareas = page.locator("textarea").count()
            print(f"[*] Found {textareas} <textarea> elements on the page.")
            
            browser.close()
            print("[*] Recon complete.")
    except Exception as e:
        print(f"[!] Error during recon: {e}")

if __name__ == "__main__":
    run_recon()
