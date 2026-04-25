import urllib.request
import json
import asyncio
import websockets

async def get_dom():
    print("[*] Fetching CDP targets...")
    req = urllib.request.urlopen("http://127.0.0.1:9222/json")
    targets = json.loads(req.read().decode('utf-8'))
    
    # Find the main page target
    page_target = None
    for t in targets:
        if t.get("type") == "page" and "webSocketDebuggerUrl" in t:
            # Skip background/empty pages if possible, though Electron might hide the URL
            if not t.get("url", "").startswith("devtools://"):
                page_target = t
                break
                
    if not page_target:
        print("[!] Could not find a valid page target.")
        return
        
    ws_url = page_target["webSocketDebuggerUrl"]
    print(f"[*] Connecting to {ws_url}")
    
    async with websockets.connect(ws_url) as ws:
        # Send a Runtime.evaluate command to get the document outerHTML
        req_msg = {
            "id": 1,
            "method": "Runtime.evaluate",
            "params": {
                "expression": "document.documentElement.outerHTML"
            }
        }
        await ws.send(json.dumps(req_msg))
        
        # Wait for the response
        resp = await ws.recv()
        resp_data = json.loads(resp)
        
        if "result" in resp_data and "result" in resp_data["result"]:
            html_content = resp_data["result"]["result"].get("value", "")
            
            out_path = "d:/hermes-agent/scratch/perplexity_dom.html"
            with open(out_path, "w", encoding="utf-8") as f:
                f.write(html_content)
                
            print(f"[+] Successfully saved {len(html_content)} bytes of HTML to {out_path}")
        else:
            print(f"[!] Failed to get HTML: {resp_data}")

if __name__ == "__main__":
    asyncio.run(get_dom())
