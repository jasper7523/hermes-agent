import urllib.request
import json
import asyncio
import websockets
import time

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
        # Start a background task to receive messages
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
        
        # 1. Focus the input box
        focus_js = "document.getElementById('ask-input').focus();"
        await self.execute_js(focus_js)
        
        # 2. Insert text directly via CDP (Bypasses React event issues)
        await self.send_command("Input.insertText", {"text": query})
        
        # 3. Press Enter
        await self.send_command("Input.dispatchKeyEvent", {
            "type": "keyDown",
            "windowsVirtualKeyCode": 13, # Enter
            "text": "\r"
        })
        await self.send_command("Input.dispatchKeyEvent", {
            "type": "keyUp",
            "windowsVirtualKeyCode": 13
        })
        
        print("[*] 查詢已送出，等待 AI 生成中...")
        
        # 4. Wait for answer to generate
        # Wait a bit for the UI to transition
        await asyncio.sleep(3)
        
        # Polling loop
        last_length = 0
        stable_count = 0
        answer_html = ""
        
        poll_js = """
        (() => {
            let answers = document.querySelectorAll('.prose');
            if(answers.length > 0) {
                return answers[answers.length - 1].innerText; // Grab raw text to check stability
            }
            return null;
        })()
        """
        
        extract_js = """
        (() => {
            let answers = document.querySelectorAll('.prose');
            if(answers.length > 0) {
                return answers[answers.length - 1].innerHTML; // Grab HTML to preserve Markdown/links
            }
            return null;
        })()
        """

        for _ in range(60): # Max 60 seconds
            text = await self.execute_js(poll_js)
            if text:
                current_length = len(text)
                if current_length == last_length and current_length > 10:
                    stable_count += 1
                else:
                    stable_count = 0
                
                last_length = current_length
                
                # If length hasn't changed for 3 seconds, assume generation is complete
                if stable_count >= 3:
                    answer_html = await self.execute_js(extract_js)
                    break
            
            await asyncio.sleep(1)
            
        await self.ws.close()
        
        if not answer_html:
            return "錯誤：生成超時或找不到輸出容器。"
            
        # We can use markdownify or bs4 here to convert HTML back to clean markdown,
        # but for the raw tool returning HTML is also fine if N2 parses it.
        # Let's just return the raw text + HTML for now.
        return answer_html

def perplexity_search(query: str) -> str:
    """
    N2 Tool interface.
    """
    client = PerplexityCDP()
    return asyncio.run(client.search(query))

if __name__ == "__main__":
    import sys
    query = "2026年企業法遵趨勢" if len(sys.argv) == 1 else sys.argv[1]
    print(f"[*] 啟動查詢: {query}".encode('cp950', 'replace').decode('cp950'))
    res = perplexity_search(query)
    print("\n" + "="*40 + "\n")
    # Avoid cp950 console errors by replacing unmappable characters
    print(res.encode('cp950', 'replace').decode('cp950'))
