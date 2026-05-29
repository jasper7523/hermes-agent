#!/usr/bin/env python3
"""session_query.py — 向 N6 全域記憶經紀人查詢歷史紀錄

用法：
    python memory/scripts/session_query.py --query "關鍵字" [--agent N8] [--namespace session] [--limit 5]
"""
import argparse
import json
import sys
import urllib.request
import urllib.parse

sys.stdout.reconfigure(encoding='utf-8')

N6_MEMORIES_URL = "http://127.0.0.1:6060/api/memories"

def query_n6(query=None, agent_id=None, namespace=None, limit=10):
    params = []
    if query:
        params.append(f"q={urllib.parse.quote(query)}")
    if agent_id:
        params.append(f"agent_id={urllib.parse.quote(agent_id)}")
    if namespace:
        params.append(f"namespace={urllib.parse.quote(namespace)}")
    params.append(f"limit={limit}")
    
    url = f"{N6_MEMORIES_URL}?{'&'.join(params)}"
    
    req = urllib.request.Request(url, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            if resp.status == 200:
                return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        print(f"[SESSION_QUERY] 查詢失敗，N6 服務可能未啟動或連線超時。({e})")
        sys.exit(1)
    return {}

def main():
    parser = argparse.ArgumentParser(description="向 N6 查詢歷史記憶")
    parser.add_argument("--query", "-q", default=None, help="搜尋關鍵字")
    parser.add_argument("--agent", "-a", default=None, help="過濾特定 Agent ID")
    parser.add_argument("--namespace", "-ns", default=None, help="過濾命名空間 (預設不過濾)")
    parser.add_argument("--limit", "-l", type=int, default=5, help="回傳最大筆數 (預設: 5)")
    args = parser.parse_args()

    if not args.query and not args.agent and not args.namespace:
        parser.print_help()
        return

    result = query_n6(args.query, args.agent, args.namespace, args.limit)
    memories = result.get("memories", [])
    total = result.get("total", 0)

    print(f"=== N6 全域記憶查詢結果 (共找到 {total} 筆，顯示前 {len(memories)} 筆) ===")
    if not memories:
        print("查無符合的歷史記憶。")
        print("=== END QUERY ===")
        return

    for i, m in enumerate(memories):
        print(f"[{i+1}] ID: {m.get('id')} | 節點: {m.get('agent_id')} | 命名空間: {m.get('namespace')} | 時間: {m.get('created_at', '')[:16]}")
        content_str = m.get("content", "")
        try:
            content_data = json.loads(content_str)
            if isinstance(content_data, dict):
                if content_data.get("summary"):
                    print(f"    摘要: {content_data['summary']}")
                if content_data.get("decisions"):
                    print(f"    決策: {content_data['decisions']}")
                if content_data.get("next_steps"):
                    print(f"    下一步: {content_data['next_steps']}")
            else:
                print(f"    內容: {content_str}")
        except Exception:
            print(f"    內容: {content_str}")
        
        tags = m.get("tags", [])
        if isinstance(tags, str):
            try:
                tags = json.loads(tags)
            except Exception:
                tags = [t.strip().strip("'\"") for t in tags.replace("[", "").replace("]", "").split(",") if t.strip()]
        
        display_tags = [t for t in tags if isinstance(t, str) and not t.startswith("src:")]
        if display_tags:
            print(f"    標籤: {', '.join(display_tags)}")

        print()
    print("=== END QUERY ===")

if __name__ == "__main__":
    main()
