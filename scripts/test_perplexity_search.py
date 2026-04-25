import urllib.request
import json
import asyncio
import websockets

class PerplexityCDP:
    def __init__(self, port=9222):
        self.port = port
        self.ws_url = None
        self.ws = None

    async def connect(self):
        req = urllib.request.urlopen(f"http://127.0.0.1:{self.port}/json")
        targets = json.loads(req.read().decode('utf-8'))
        
        for t in targets:
            if t.get("type") == "page" and "webSocketDebuggerUrl" in t:
                # We want the main UI page. Sometimes Electron reports it with empty URL or perplexity URL
                if "service-worker" not in t.get("url", ""):
                    self.ws_url = t["webSocketDebuggerUrl"]
                    break
                    
        if not self.ws_url:
            raise Exception("Perplexity App main page not found on CDP port.")
            
        self.ws = await websockets.connect(self.ws_url, ping_interval=None)

    async def execute_js(self, js_code):
        req_msg = {
            "id": 1,
            "method": "Runtime.evaluate",
            "params": {
                "expression": js_code,
                "awaitPromise": True,
                "returnByValue": True
            }
        }
        await self.ws.send(json.dumps(req_msg))
        
        # We might receive other CDP events (like network events), so we loop until we get id=1
        while True:
            resp_str = await self.ws.recv()
            resp = json.loads(resp_str)
            if resp.get("id") == 1:
                return resp.get("result", {}).get("result", {}).get("value")

    async def search(self, query: str):
        await self.connect()
        
        js = f"""
        (async () => {{
            let box = document.querySelector('textarea');
            if(!box) return 'Error: textarea not found';
            
            box.focus();
            let nativeInputValueSetter = Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype, "value").set;
            nativeInputValueSetter.call(box, {json.dumps(query)});
            box.dispatchEvent(new Event('input', {{ bubbles: true }}));
            
            // Wait a tiny bit for React state
            await new Promise(r => setTimeout(r, 100));
            
            // Press Enter
            box.dispatchEvent(new KeyboardEvent('keydown', {{key: 'Enter', code: 'Enter', keyCode: 13, which: 13, bubbles: true}}));
            return 'Submitted';
        }})()
        """
        result = await self.execute_js(js)
        print(f"[+] Query Submission: {result}")
        
        if "Error" in result:
            await self.ws.close()
            return "Failed to submit"
            
        print("[*] Waiting 10 seconds for AI generation...")
        await asyncio.sleep(10)
        
        poll_js = """
        (() => {
            // Usually the answers are in elements with specific classes, often starting with 'prose' for tailwind
            let answers = document.querySelectorAll('.prose');
            if(answers.length > 0) {
                // Return the text of the last answer
                return answers[answers.length - 1].innerText;
            }
            return 'Answer container not found';
        })()
        """
        answer = await self.execute_js(poll_js)
        await self.ws.close()
        return answer

if __name__ == "__main__":
    client = PerplexityCDP()
    try:
        result = asyncio.run(client.search("請簡述 2026 年企業法遵的三大重點"))
        print("\n=== AI RESPONSE ===")
        print(result)
    except Exception as e:
        print(f"Error: {e}")
