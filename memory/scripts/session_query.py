#!/usr/bin/env python3
"""session_query.py — 向 N6 全域記憶經紀人查詢歷史紀錄（三軌制）

三種查詢模式：
  1. FTS5 文字檢索 (預設):  --query "關鍵字"
  2. GraphRAG 語意推理:      --graph "為什麼做了這個決策？"
  3. 圖譜鄰居探索:           --neighbors "node_id"

用法：
    python memory/scripts/session_query.py --query "關鍵字" [--agent N8] [--limit 5]
    python memory/scripts/session_query.py --graph "法遵科技與 CCO 角色有什麼關聯？"
    python memory/scripts/session_query.py --neighbors "node_id" [--depth 2]
"""
import argparse
import json
import sys
import urllib.request
import urllib.parse

sys.stdout.reconfigure(encoding='utf-8')

N6_BASE_URL = "http://127.0.0.1:6060"
N6_MEMORIES_URL = f"{N6_BASE_URL}/api/memories"
N6_GRAPH_SEARCH_URL = f"{N6_BASE_URL}/api/graph/search"
N6_GRAPH_NEIGHBORS_URL = f"{N6_BASE_URL}/api/graph/neighbors"
N6_GRAPH_STATS_URL = f"{N6_BASE_URL}/api/graph/stats"


def query_n6_fts(query=None, agent_id=None, namespace=None, limit=10):
    """第一軌：FTS5 文字檢索"""
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
        print(f"[SESSION_QUERY] FTS5 查詢失敗，N6 服務可能未啟動。({e})")
        sys.exit(1)
    return {}


def query_n6_graph_search(question: str):
    """第三軌：GraphRAG 語意推理（Map-Reduce over community summaries）"""
    payload = json.dumps({"question": question}, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        N6_GRAPH_SEARCH_URL, data=payload,
        headers={"Content-Type": "application/json"}, method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            if resp.status == 200:
                return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        print(f"[SESSION_QUERY] GraphRAG 查詢失敗。({e})")
        sys.exit(1)
    return {}


def query_n6_neighbors(node_id: str, depth: int = 1):
    """圖譜鄰居探索"""
    url = f"{N6_GRAPH_NEIGHBORS_URL}/{urllib.parse.quote(node_id)}?depth={depth}"
    req = urllib.request.Request(url, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            if resp.status == 200:
                return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        print(f"[SESSION_QUERY] 圖譜鄰居查詢失敗。({e})")
        sys.exit(1)
    return {}


def display_fts_results(result):
    """顯示 FTS5 文字檢索結果"""
    memories = result.get("memories", [])
    total = result.get("total", 0)

    print(f"=== N6 全域記憶查詢結果 [FTS5] (共 {total} 筆，顯示前 {len(memories)} 筆) ===")
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


def display_graph_search_result(result):
    """顯示 GraphRAG 語意推理結果"""
    print("=== N6 GraphRAG 語意推理結果 ===")
    status = result.get("status", "error")
    if status == "disabled":
        print("[GraphRAG] 圖譜功能未啟用。請在 N6 config 中設定 GRAPH_ENABLED=true。")
    elif status == "error":
        print(f"[GraphRAG] 查詢失敗：{result.get('message', '未知錯誤')}")
    else:
        answer = result.get("answer", "(無回應)")
        communities = result.get("communities_searched", 0)
        print(f"[搜尋範圍] {communities} 個社群摘要")
        print(f"[回答]\n{answer}")
    print("=== END GRAPH SEARCH ===")


def display_neighbors_result(result, node_id):
    """顯示圖譜鄰居結果"""
    print(f"=== N6 圖譜鄰居探索: {node_id} ===")
    subgraph = result.get("subgraph", {})
    if isinstance(subgraph, dict) and "error" in subgraph:
        print(f"[錯誤] {subgraph['error']}")
    else:
        nodes = subgraph.get("nodes", [])
        edges = subgraph.get("edges", [])
        print(f"[節點數] {len(nodes)}  [邊數] {len(edges)}")
        for n in nodes[:20]:
            if isinstance(n, dict):
                print(f"  - [{n.get('node_type', '?')}] {n.get('id', '?')}: {n.get('label', '')[:60]}")
            else:
                print(f"  - {n}")
        if edges:
            print("[關係]")
            for e in edges[:20]:
                if isinstance(e, dict):
                    print(f"  {e.get('source', '?')} -[{e.get('relation', '?')}]-> {e.get('target', '?')}")
    print("=== END NEIGHBORS ===")


def main():
    parser = argparse.ArgumentParser(description="向 N6 查詢歷史記憶（三軌制）")
    parser.add_argument("--query", "-q", default=None, help="[第一軌] FTS5 文字檢索關鍵字")
    parser.add_argument("--graph", "-g", default=None, help="[第三軌] GraphRAG 語意推理問題")
    parser.add_argument("--neighbors", "-n", default=None, help="圖譜鄰居探索：指定 node_id")
    parser.add_argument("--agent", "-a", default=None, help="過濾特定 Agent ID (僅 FTS5)")
    parser.add_argument("--namespace", "-ns", default=None, help="過濾命名空間 (僅 FTS5)")
    parser.add_argument("--limit", "-l", type=int, default=5, help="回傳最大筆數 (預設: 5)")
    parser.add_argument("--depth", "-d", type=int, default=1, help="鄰居探索深度 (預設: 1)")
    args = parser.parse_args()

    if args.graph:
        # 第三軌：GraphRAG
        result = query_n6_graph_search(args.graph)
        display_graph_search_result(result)
    elif args.neighbors:
        # 圖譜鄰居
        result = query_n6_neighbors(args.neighbors, args.depth)
        display_neighbors_result(result, args.neighbors)
    elif args.query or args.agent or args.namespace:
        # 第一軌：FTS5
        result = query_n6_fts(args.query, args.agent, args.namespace, args.limit)
        display_fts_results(result)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
