import asyncio
import json
import logging
import sys
import httpx

import os
from pathlib import Path
from dotenv import load_dotenv

# 確保輸出為 utf-8
sys.stdout.reconfigure(encoding='utf-8')

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("test-consensus-mcp")

async def test_mcp():
    load_dotenv(dotenv_path=Path("D:/Agent_Hub/.env"))
    cookie_str = os.getenv("CONSENSUS_COOKIE", "").strip()
    
    url = "https://mcp.consensus.app/mcp"
    headers = {
        "Accept": "text/event-stream",
    }
    
    if cookie_str:
        headers["Cookie"] = cookie_str
        # 嘗試從 cookie 提取 __session 作為 Bearer token
        session_token = None
        for pair in cookie_str.split(";"):
            pair = pair.strip()
            if pair.startswith("__session="):
                session_token = pair.partition("=")[2]
                break
        if session_token:
            headers["Authorization"] = f"Bearer {session_token}"
            logger.info("Extracted __session token, adding Authorization header")
    
    logger.info("Connecting to Consensus MCP SSE at %s with headers...", url)

    async with httpx.AsyncClient(timeout=30.0) as client:
        # 發送 GET 請求以啟動 SSE 連線
        async with client.stream("GET", url, headers=headers) as response:
            if response.status_code != 200:
                logger.error("Failed to connect: HTTP %d", response.status_code)
                return
                
            post_url = None
            # 讀取 SSE stream 直到拿到 endpoint
            async for line in response.iter_lines():
                if line.startswith("event: endpoint"):
                    # 接下來的 line 通常是 data: ...
                    pass
                elif line.startswith("data:"):
                    data_val = line[5:].strip()
                    # 判斷是否為絕對路徑或相對路徑
                    if data_val.startswith("http"):
                        post_url = data_val
                    else:
                        # 拼接相對路徑
                        from urllib.parse import urljoin
                        post_url = urljoin(url, data_val)
                    logger.info("Found POST endpoint: %s", post_url)
                    break
            
            if not post_url:
                logger.error("Could not find POST endpoint from SSE stream.")
                return

            # 2. 發送 initialize 請求
            logger.info("Sending JSON-RPC 'initialize'...")
            init_payload = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {
                        "name": "phoenix-test-client",
                        "version": "1.0.0"
                    }
                }
            }
            
            init_resp = await client.post(post_url, json=init_payload)
            logger.info("Initialize HTTP status: %d", init_resp.status_code)
            logger.info("Initialize Response: %s", init_resp.text)
            
            # 3. 發送 initialized 通知
            logger.info("Sending 'initialized' notification...")
            initialized_payload = {
                "jsonrpc": "2.0",
                "method": "notifications/initialized"
            }
            await client.post(post_url, json=initialized_payload)
            
            # 4. 呼叫 search 工具
            logger.info("Calling tool 'search'...")
            call_payload = {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/call",
                "params": {
                    "name": "search",
                    "arguments": {
                        "query": "artificial intelligence legal compliance",
                        "year_min": 2020
                    }
                }
            }
            
            call_resp = await client.post(post_url, json=call_payload)
            logger.info("Tool Call HTTP status: %d", call_resp.status_code)
            try:
                result_json = call_resp.json()
                print("\n=== Search Results ===")
                print(json.dumps(result_json, indent=2, ensure_ascii=False))
                print("======================\n")
            except Exception as e:
                logger.error("Failed to parse tool call response as JSON: %s", e)
                logger.error("Raw response: %s", call_resp.text)

if __name__ == "__main__":
    asyncio.run(test_mcp())
