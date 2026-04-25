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
        
        for t in targets:
            if t.get("type") == "page" and "webSocketDebuggerUrl" in t:
                if "service-worker" not in t.get("url", ""):
                    self.ws_url = t["webSocketDebuggerUrl"]
                    break
                    
        if not self.ws_url:
            raise Exception("Perplexity App main page not found on CDP port.")
            
        self.ws = await websockets.connect(self.ws_url, ping_interval=None)
        asyncio.create_task(self._receive_loop())

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
        
        focus_js = "document.getElementById('ask-input').focus();"
        await self.execute_js(focus_js)
        
        await self.send_command("Input.insertText", {"text": query})
        
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
            let answers = document.querySelectorAll('.prose');
            if(answers.length > 0) {
                return answers[answers.length - 1].innerText;
            }
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
            let copyBtns = document.querySelectorAll('button[aria-label="Copy"], button[aria-label="複製"], button[aria-label="复制"]');
            if(copyBtns.length === 0) return false;
            let copyBtn = copyBtns[copyBtns.length - 1];
            copyBtn.click();
            return true;
        })()
        """
        
        # Save old clipboard
        old_cb = pyperclip.paste()
        # Clear clipboard to detect when copy finishes
        pyperclip.copy("PENDING_COPY")
        
        clicked = await self.execute_js(click_js)
        await self.ws.close()
        
        if not clicked:
            return "錯誤：找不到複製按鈕。"
            
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
