import asyncio
import websockets
import json
import urllib.request

async def check_status():
    req = urllib.request.urlopen("http://127.0.0.1:9222/json")
    targets = json.loads(req.read().decode('utf-8'))
    ws_url = None
    for t in targets:
        if "perplexity.ai" in t.get("url", "") and t.get("type") == "page":
            ws_url = t["webSocketDebuggerUrl"]
            break
    
    async with websockets.connect(ws_url) as ws:
        check_js = """
        (() => {
            let btn = Array.from(document.querySelectorAll('button')).find(b => b.innerText.includes('深入研究'));
            if (btn) {
                return {
                    text: btn.innerText,
                    classes: btn.className,
                    checked: btn.getAttribute('aria-checked'),
                    style: window.getComputedStyle(btn).backgroundColor
                };
            }
            return "Not Found";
        })()
        """
        await ws.send(json.dumps({"id": 1, "method": "Runtime.evaluate", "params": {"expression": check_js, "returnByValue": True}}))
        resp = await ws.recv()
        print(resp)

if __name__ == "__main__":
    asyncio.run(check_status())
