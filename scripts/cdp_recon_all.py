import urllib.request
import json
import asyncio
import websockets

async def dump_target(t):
    ws_url = t["webSocketDebuggerUrl"]
    print(f"[*] Connecting to {t.get('title', 'Unknown')} ({ws_url})")
    
    try:
        async with websockets.connect(ws_url, ping_interval=None) as ws:
            req_msg = {
                "id": 1,
                "method": "Runtime.evaluate",
                "params": {
                    "expression": "document.documentElement.outerHTML"
                }
            }
            await ws.send(json.dumps(req_msg))
            resp = await ws.recv()
            resp_data = json.loads(resp)
            
            if "result" in resp_data and "result" in resp_data["result"]:
                html = resp_data["result"]["result"].get("value", "")
                name = t['id']
                out = f"d:/hermes-agent/scratch/dom_{name}.html"
                with open(out, "w", encoding="utf-8") as f:
                    f.write(html)
                print(f"[+] Saved {len(html)} bytes to {out}")
    except Exception as e:
        print(f"[!] Error on {t['id']}: {e}")

async def main():
    req = urllib.request.urlopen("http://127.0.0.1:9222/json")
    targets = json.loads(req.read().decode('utf-8'))
    
    tasks = []
    for t in targets:
        if t.get("type") == "page" and "webSocketDebuggerUrl" in t:
            tasks.append(dump_target(t))
            
    await asyncio.gather(*tasks)

if __name__ == "__main__":
    asyncio.run(main())
