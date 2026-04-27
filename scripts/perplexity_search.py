import urllib.request
import json
import asyncio
import websockets
import time
import pyperclip

# [N7 Security Restore]: Reverting to pure Python CDP (WebSockets) to maintain stealth
# This avoids Playwright/Puppeteer detection fingerprints used by Perplexity.
class PerplexityCDP:
    def __init__(self, port=9222):
        self.port = port
        self.ws_url = None
        self.ws = None
        self.msg_id = 1
        self.pending_requests = {}

    async def connect(self):
        try:
            req = urllib.request.urlopen(f"http://127.0.0.1:{self.port}/json", timeout=2)
            targets = json.loads(req.read().decode('utf-8'))
        except Exception:
            raise Exception(f"無法連線至 Chrome CDP 埠 {self.port}。請確保已執行桌面捷徑啟動 Oracle。")
            
        target_page = None
        # 優先尋找已開啟的 Perplexity 標籤
        for t in targets:
            if t.get("type") == "page" and "perplexity.ai" in t.get("url", ""):
                target_page = t
                break
        
        if not target_page:
            for t in targets:
                if t.get("type") == "page" and not t.get("url", "").startswith("chrome-extension://"):
                    target_page = t
                    break
        
        if not target_page:
            raise Exception("No suitable browser page found on CDP port.")
            
        self.ws_url = target_page["webSocketDebuggerUrl"]
        print(f"[*] Connecting to WebSocket: {self.ws_url}")
        self.ws = await websockets.connect(self.ws_url, ping_interval=None)
        print("[*] WebSocket Connected.")
        asyncio.create_task(self._receive_loop())

        if "perplexity.ai" not in target_page.get("url", ""):
            print("[*] Navigating to Perplexity...")
            await self.send_command("Page.navigate", {"url": "https://www.perplexity.ai/"})
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
        if params is None: params = {}
        if not self.ws or self.ws.state.name == "CLOSED":
            print("[!] Connection lost, attempting to reconnect...")
            await self.connect()
            
        msg_id = self.msg_id
        self.msg_id += 1
        future = asyncio.get_running_loop().create_future()
        self.pending_requests[msg_id] = future
        try:
            await self.ws.send(json.dumps({"id": msg_id, "method": method, "params": params}))
            return await future
        except Exception as e:
            print(f"[!] Send failed: {e}")
            return {}

    async def execute_js(self, js_code):
        resp = await self.send_command("Runtime.evaluate", {"expression": js_code, "awaitPromise": True, "returnByValue": True})
        return resp.get("result", {}).get("result", {}).get("value")

    async def search(self, query: str):
        print(f"[*] Starting search for: {query}")
        await self.connect()
        
        # 1. 強制重置線程 (Ctrl+I)
        print("[*] Resetting thread (Ctrl+I)...")
        await self.send_command("Input.dispatchKeyEvent", {"type": "keyDown", "modifiers": 2, "windowsVirtualKeyCode": 73, "text": "i"})
        await self.send_command("Input.dispatchKeyEvent", {"type": "keyUp", "modifiers": 2, "windowsVirtualKeyCode": 73})
        await asyncio.sleep(2.0)
        
        # 2. 聚焦輸入框 (強效版 JS)
        print("[*] Focusing input...")
        focus_js = """
        (() => {
            let input = document.getElementById('ask-input') || 
                        document.querySelector('textarea') || 
                        document.querySelector('input[type="text"]');
            if (input) {
                input.click(); // 先點擊觸發 React 狀態
                input.focus();
                return true;
            }
            return false;
        })()
        """
        if not await self.execute_js(focus_js):
            return "錯誤：無法聚焦輸入框。"

        # 3. 填入文字
        print("[*] Inserting text...")
        await self.send_command("Input.insertText", {"text": query})
        await asyncio.sleep(1.0)
        
        # 4. 發送 Enter
        print("[*] Sending Enter...")
        await self.send_command("Input.dispatchKeyEvent", {"type": "keyDown", "windowsVirtualKeyCode": 13, "text": "\r"})
        await self.send_command("Input.dispatchKeyEvent", {"type": "keyUp", "windowsVirtualKeyCode": 13})
        
        # 5. 等待內容生成 (強化過濾 Demo 文字)
        print("[*] Polling for response (Wait 5s initial)...")
        await asyncio.sleep(5.0) # 給 AI 一點時間
        
        last_length = 0
        stable_count = 0
        for i in range(40):
            try:
                text = await self.execute_js(poll_js)
                if text:
                    curr_len = len(text)
                    if curr_len > 100 and curr_len == last_length:
                        stable_count += 1
                    else:
                        stable_count = 0
                    last_length = curr_len
                    if stable_count >= 3: 
                        print(f"[*] Content stabilized at {curr_len} chars.")
                        break
                print(f"[*] Polling... ({i+1}/40) - Current length: {len(text) if text else 0}")
                await asyncio.sleep(2.0)
            except Exception as e:
                print(f"[!] Polling error: {e}")
                await asyncio.sleep(1.0)

        # 6. 點擊複製
        click_js = """
        (() => {
            const selectors = ['button[aria-label*="Copy"]', 'button[aria-label*="複製"]', 'button:has(svg[data-icon="copy"])'];
            for (let s of selectors) {
                let btns = document.querySelectorAll(s);
                if (btns.length > 0) {
                    btns[btns.length - 1].click();
                    return true;
                }
            }
            return false;
        })()
        """
        
        old_cb = pyperclip.paste()
        pyperclip.copy("PENDING")
        clicked = await self.execute_js(click_js)
        
        if clicked:
            for _ in range(30):
                new_cb = pyperclip.paste()
                if new_cb != "PENDING":
                    pyperclip.copy(old_cb)
                    await self.ws.close()
                    return new_cb
                await asyncio.sleep(0.1)
        
        await self.ws.close()
        if last_length > 50:
            return f"注意：複製失敗，已採樣直接提取內容。\n\n{text}"
        return "錯誤：擷取失敗或內容過短。"

def perplexity_search(query: str) -> str:
    client = PerplexityCDP()
    return asyncio.run(client.search(query))

if __name__ == "__main__":
    import sys
    query = "FCPA history summary" if len(sys.argv) == 1 else sys.argv[1]
    print(perplexity_search(query))
