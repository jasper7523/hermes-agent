import urllib.request
import json
import asyncio
import websockets
import time
import pyperclip

class PerplexityCDP:
    def __init__(self, port=9222):
        self.port = port
        self.ws_url = None
        self.ws = None
        self.msg_id = 1
        self.pending_requests = {}

    async def connect(self):
        req = urllib.request.urlopen(f"http://127.0.0.1:{self.port}/json")
        targets = json.loads(req.read().decode('utf-8'))
        
        # [N7 Infrastructure Fix]: Look for Perplexity tab specifically
        target_page = None
        for t in targets:
            if t.get("type") == "page" and "perplexity.ai" in t.get("url", ""):
                target_page = t
                break
        
        if not target_page:
            # If no Perplexity tab, use the first available regular page
            for t in targets:
                if t.get("type") == "page" and not t.get("url", "").startswith("chrome-extension://"):
                    target_page = t
                    break
        
        if not target_page:
            raise Exception("No suitable browser page found on CDP port.")
            
        self.ws_url = target_page["webSocketDebuggerUrl"]
        self.ws = await websockets.connect(self.ws_url, ping_interval=None)
        asyncio.create_task(self._receive_loop())

        # If we are not on perplexity.ai, navigate there
        current_url = target_page.get("url", "")
        if "perplexity.ai" not in current_url:
            await self.send_command("Page.navigate", {"url": "https://www.perplexity.ai/"})
            # Wait for navigation and initial load
            await asyncio.sleep(5)

    async def _receive_loop(self):
        try:
            async for message in self.ws:
                data = json.loads(message)
                if "id" in data and data["id"] in self.pending_requests:
                    self.pending_requests[data["id"]].set_result(data)
        except Exception:
            pass

    async def send_command(self, method, params=None):
        if params is None:
            params = {}
        msg_id = self.msg_id
        self.msg_id += 1
        
        future = asyncio.get_running_loop().create_future()
        self.pending_requests[msg_id] = future
        
        req_msg = {
            "id": msg_id,
            "method": method,
            "params": params
        }
        await self.ws.send(json.dumps(req_msg))
        return await future

    async def execute_js(self, js_code):
        resp = await self.send_command("Runtime.evaluate", {
            "expression": js_code,
            "awaitPromise": True,
            "returnByValue": True
        })
        return resp.get("result", {}).get("result", {}).get("value")

    async def search(self, query: str):
        await self.connect()
        
        # [N5 Fix Upstreamed]: Force 'New Thread' via Ctrl+I to reset DOM state 
        # Prevents race conditions where old '.prose' elements satisfy the polling prematurely
        await self.send_command("Input.dispatchKeyEvent", {
            "type": "keyDown",
            "modifiers": 2, # Ctrl
            "windowsVirtualKeyCode": 73, # I
            "text": "i"
        })
        await self.send_command("Input.dispatchKeyEvent", {
            "type": "keyUp",
            "modifiers": 2,
            "windowsVirtualKeyCode": 73
        })
        # Wait for the new thread UI to initialize
        await asyncio.sleep(1.5)
        
        # Ensure we are focused on the input. Try multiple selectors.
        focus_js = """
        (() => {
            let input = document.getElementById('ask-input') || 
                        document.querySelector('textarea') || 
                        document.querySelector('input[type="text"]');
            if (input) {
                input.focus();
                return true;
            }
            return false;
        })()
        """
        if not await self.execute_js(focus_js):
            await self.ws.close()
            return "錯誤：找不到輸入框 (ask-input)。"
            
        await self.send_command("Input.insertText", {"text": query})
        
        # [N5 Enhancement]: 自動檢測並啟動「深入研究」模式
        # 等待 UI 對輸入內容產生反應
        await asyncio.sleep(1.0)
        click_deep_research_js = """
        (() => {
            // 尋找包含「深入研究」字樣的按鈕
            let btn = Array.from(document.querySelectorAll('button')).find(b => 
                b.innerText.includes('深入研究') || 
                (b.getAttribute('aria-label') && b.getAttribute('aria-label').includes('深入研究'))
            );
            if (btn) {
                btn.click();
                return true;
            }
            return false;
        })()
        """
        triggered_deep = await self.execute_js(click_deep_research_js)
        
        if not triggered_deep:
            # 若沒偵測到深入研究按鈕，則執行標準 Enter 提交
            await self.send_command("Input.dispatchKeyEvent", {
                "type": "keyDown",
                "windowsVirtualKeyCode": 13,
                "text": "\r"
            })
            await self.send_command("Input.dispatchKeyEvent", {
                "type": "keyUp",
                "windowsVirtualKeyCode": 13
            })
        
        # Wait for generation to start
        await asyncio.sleep(3)
        
        last_length = 0
        stable_count = 0
        
        poll_js = """
        (() => {
            // 嘗試多種回答區塊選擇器
            const selectors = [
                '.prose',
                '[data-testid="answer-content"]',
                '.markdown-body',
                '.answer-content',
                '.default.font-sans'
            ];
            for (let s of selectors) {
                let els = document.querySelectorAll(s);
                if (els.length > 0) return els[els.length - 1].innerText;
            }
            // 備援：抓取包含大量文字的容器
            let main = document.querySelector('main');
            if (main) return main.innerText;
            return null;
        })()
        """
        
        for _ in range(60):
            text = await self.execute_js(poll_js)
            if text:
                current_length = len(text)
                if current_length == last_length and current_length > 10:
                    stable_count += 1
                else:
                    stable_count = 0
                
                last_length = current_length
                
                if stable_count >= 3:
                    break
            await asyncio.sleep(1)
            
        # Generation is complete. Now click the copy button.
        click_js = """
        (() => {
            // 嘗試多種可能的選擇器 (包含 SVG 圖標偵測)
            const selectors = [
                'button[aria-label="Copy"]', 
                'button[aria-label="複製"]', 
                'button[aria-label="复制"]',
                'button:has(svg[data-icon="copy"])',
                'button:has(svg path[d*="M16"])', // 典型的複製圖標路徑片段
                '.prose + div button' // prose 區塊下方的按鈕群
            ];
            
            let copyBtn = null;
            for (let s of selectors) {
                let btns = document.querySelectorAll(s);
                if (btns.length > 0) {
                    copyBtn = btns[btns.length - 1];
                    break;
                }
            }
            
            if (!copyBtn) {
                // 最後手段：尋找所有按鈕，檢查其 title 或 innerText
                let allBtns = Array.from(document.querySelectorAll('button'));
                copyBtn = allBtns.reverse().find(b => 
                    (b.title && (b.title.includes('Copy') || b.title.includes('複製'))) ||
                    (b.innerText && (b.innerText.includes('Copy') || b.innerText.includes('複製')))
                );
            }

            if (copyBtn) {
                copyBtn.scrollIntoView();
                // 模擬懸停以觸發某些 UI 組件顯示
                copyBtn.dispatchEvent(new MouseEvent('mouseover', { bubbles: true }));
                copyBtn.click();
                return true;
            }
            return false;
        })()
        """
        
        # Save old clipboard
        old_cb = pyperclip.paste()
        # Clear clipboard to detect when copy finishes
        pyperclip.copy("PENDING_COPY")
        
        clicked = False
        # Retry clicking for 3 seconds (sometimes the UI takes a moment to render the buttons)
        for _ in range(6):
            clicked = await self.execute_js(click_js)
            if clicked: break
            await asyncio.sleep(0.5)

        if not clicked:
            # Fallback: 如果真的找不到複製按鈕，直接抓取內容回傳 (雖然不是 Markdown 但總比錯誤好)
            fallback_text = await self.execute_js(poll_js)
            await self.ws.close()
            if fallback_text:
                return f"注意：無法點擊複製按鈕，已採樣直接提取內容。\n\n{fallback_text}"
            return "錯誤：找不到複製按鈕，且直接提取內容失敗。"
            
        # Poll OS clipboard for up to 3 seconds
        new_cb = "PENDING_COPY"
        for _ in range(30):
            new_cb = pyperclip.paste()
            if new_cb != "PENDING_COPY":
                break
            await asyncio.sleep(0.1)
            
        # Restore old clipboard
        pyperclip.copy(old_cb)
        
        if new_cb == "PENDING_COPY":
            return "錯誤：擷取 Markdown 失敗或超時。"
            
        return new_cb

def perplexity_search(query: str) -> str:
    client = PerplexityCDP()
    return asyncio.run(client.search(query))

if __name__ == "__main__":
    import sys
    query = "請簡述臺灣2026年企業法遵趨勢，務必附上參考網址" if len(sys.argv) == 1 else sys.argv[1]
    print(f"[*] 啟動查詢: {query}".encode('cp950', 'replace').decode('cp950'))
    res = perplexity_search(query)
    print("\n" + "="*40 + "\n")
    print(res.encode('cp950', 'replace').decode('cp950'))
