#!/usr/bin/env python3
"""session_load.py — N5 對話開場時載入最近 session 上下文

用法：
    python D:/Agent_Hub/agents/Book_Writer_Agent/memory/scripts/session_load.py [--agent N5] [--limit 3]

輸出：
    將最近 N 筆 session 的摘要、決策、下一步以結構化文本輸出到 stdout，
    供 Agent 的 context window 直接消費。
"""

import argparse
import sys
from pathlib import Path

# 確保可以 import 同目錄的模組
sys.path.insert(0, str(Path(__file__).parent))
from agent_session_db import get_db_path, init_db, load_latest_sessions, get_session_stats

sys.stdout.reconfigure(encoding='utf-8')


def fetch_n6_recent_global(exclude_agent: str, limit: int = 3) -> list:
    """從 N6 Web API 獲取最近其他 Agent 的 session 記錄"""
    import urllib.request
    import json
    
    url = f"http://127.0.0.1:6060/api/memories?namespace=session&limit={limit * 3}"
    req = urllib.request.Request(url, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=2) as resp:
            if resp.status == 200:
                data = json.loads(resp.read().decode("utf-8"))
                memories = data.get("memories", [])
                
                global_sessions = []
                for m in memories:
                    if m.get("agent_id") == exclude_agent:
                        continue
                    
                    content_str = m.get("content", "")
                    try:
                        content_data = json.loads(content_str)
                    except Exception:
                        content_data = {"summary": content_str}
                        
                    global_sessions.append({
                        "agent_id": m.get("agent_id"),
                        "created_at": m.get("created_at", ""),
                        "summary": content_data.get("summary", ""),
                        "decisions": content_data.get("decisions", ""),
                        "next_steps": content_data.get("next_steps", ""),
                        "tags": m.get("tags", [])
                    })
                    
                    if len(global_sessions) >= limit:
                        break
                return global_sessions
    except Exception:
        pass
    return []


def main():
    parser = argparse.ArgumentParser(description="載入 Agent 最近 session 上下文")
    parser.add_argument("--agent", default="N5", help="Agent ID (預設: N5)")
    parser.add_argument("--limit", type=int, default=3, help="載入筆數 (預設: 3)")
    parser.add_argument("--root", default=None, help="Agent 工作區根目錄")
    args = parser.parse_args()

    root = Path(args.root) if args.root else Path(__file__).parent.parent.parent
    db_path = get_db_path(root)

    if not db_path.exists():
        print(f"[SESSION_LOAD] 尚無 session 記錄 ({db_path})")
        print("[SESSION_LOAD] 這是首次對話，無需恢復上下文。")
    else:
        conn = init_db(db_path)
        sessions = load_latest_sessions(conn, args.agent, args.limit)
        stats = get_session_stats(conn, args.agent)
        conn.close()

        if sessions:
            # ─── N3 I-3 修正：載入 ACTIVE Policies ───
            try:
                import os
                _hub_root = Path(os.environ.get("AGENT_HUB_ROOT", r"D:\Agent_Hub"))
                shared_dir = _hub_root / "agents" / ".shared"
                if str(shared_dir) not in sys.path:
                    sys.path.insert(0, str(shared_dir))
                from learning.policy_loader import load_active_policies
                
                policies_md = load_active_policies(db_path)
                if policies_md:
                    print(policies_md)
            except Exception as e:
                print(f"<!-- Failed to load policies: {e} -->\n")

            # 輸出結構化上下文
            print(f"=== {args.agent} Session Memory ===")
            print(f"歷史 session 總數: {stats.get('total', 0)}")
            print(f"累計 StepGate 步數: {stats.get('total_steps', 0)}")
            print()

            for i, s in enumerate(sessions):
                label = "【最近一次】" if i == 0 else f"【前 {i+1} 次】"
                print(f"--- {label} {s['session_ts'][:16]} (StepGate×{s['stepgate_count']}) ---")
                if s.get('summary'):
                    print(f"摘要: {s['summary']}")
                if s.get('decisions'):
                    print(f"決策: {s['decisions']}")
                if s.get('next_steps'):
                    print(f"下一步: {s['next_steps']}")
                if s.get('tags'):
                    print(f"標籤: {s['tags']}")
                print()

    # ─── N6 全域記憶載入 (跨節點近期動態) ───
    try:
        global_mems = fetch_n6_recent_global(exclude_agent=args.agent, limit=3)
        if global_mems:
            print("=== N6 全域共享記憶 (跨節點近期動態) ===")
            for gm in global_mems:
                time_str = gm['created_at'][:16] if gm.get('created_at') else "未知時間"
                print(f"--- 節點: {gm['agent_id']} | 時間: {time_str} ---")
                if gm.get('summary'):
                    print(f"  摘要: {gm['summary']}")
                if gm.get('decisions'):
                    print(f"  決策: {gm['decisions']}")
                if gm.get('next_steps'):
                    print(f"  下一步: {gm['next_steps']}")
                print()
            print("=== END N6 GLOBAL MEMORY ===")
            print()
    except Exception:
        pass

    # ─── N7-FIX-20260529: Auto-read Post-Compaction Anchor ───
    checkpoint_path = root / "memory" / ".checkpoint"
    if checkpoint_path.exists():
        try:
            ckpt_text = checkpoint_path.read_text(encoding="utf-8").strip()
            print("--- 【PCA Checkpoint (壓縮後錨定)】 ---")
            for line in ckpt_text.splitlines():
                print(f"  {line}")
            print()
        except Exception:
            print("--- 【PCA Checkpoint】讀取失敗，請手動 type checkpoint ---")
            print()


    # --- Agent Tasks (Lv1 Postman) ---
    try:
        shared_learning_path = str(root.parent / ".shared" / "learning") if root.parent.name == "agents" else r"D:\Agent_Hubgents\.shared\learning"
        if shared_learning_path not in sys.path:
            sys.path.insert(0, shared_learning_path)
        import agent_tasks
        tasks = agent_tasks.claim_tasks(args.agent)
        if tasks:
            print("=== PENDING AGENT TASKS (Lv1 Postman) ===")
            for t in tasks:
                print(f"[{t['type'].upper()}] From: {t['source']} | Priority: {t['priority']}")
                print(f"Payload: {t['payload']}")
                print("---")
            print("=================================================")
            print()
    except Exception as e:
        print(f"[Warning] Failed to claim agent tasks: {e}")


# --- L3 World Model Injection ---
    try:
        import sqlite3
        with sqlite3.connect(db_path) as conn:
            conn.row_factory = sqlite3.Row
            # Load the latest World Model (if any)
            wm_rows = conn.execute("SELECT * FROM world_models ORDER BY version DESC LIMIT 1").fetchall()
            if wm_rows:
                print("=== 🌐 MACRO COGNITION (L3 World Model) ===")
                for wm in wm_rows:
                    print(f"Domain: {wm['domain']} | Version: {wm['version']}")
                    
                    # L-3: Hard truncation to prevent LLM hallucinating beyond token budget
                    # 1000 tokens is roughly 1500 CJK chars or 3000 English chars.
                    content = wm['structure']
                    if len(content) > 2000:
                        content = content[:2000] + "
...[TRUNCATED DUE TO L3 TOKEN BUDGET]..."
                    
                    print(content)
                    print("---")
                print("=================================================")
                print()
    except Exception as e:
        # DB table might not exist yet or other errors
        pass

    print("=== END SESSION MEMORY ===")


if __name__ == "__main__":
    main()

