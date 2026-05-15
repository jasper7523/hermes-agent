#!/usr/bin/env python3
"""session_load.py — Agent 對話開場時載入最近 session 上下文

用法：
    python memory/scripts/session_load.py [--agent N7] [--limit 3]

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


def main():
    parser = argparse.ArgumentParser(description="載入 Agent 最近 session 上下文")
    parser.add_argument("--agent", default="N7", help="Agent ID (預設: N7)")
    parser.add_argument("--limit", type=int, default=3, help="載入筆數 (預設: 3)")
    parser.add_argument("--root", default=None, help="Agent 工作區根目錄")
    args = parser.parse_args()

    root = Path(args.root) if args.root else Path(__file__).parent.parent.parent
    db_path = get_db_path(root)

    if not db_path.exists():
        print(f"[SESSION_LOAD] 尚無 session 記錄 ({db_path})")
        print("[SESSION_LOAD] 這是首次對話，無需恢復上下文。")
        return

    conn = init_db(db_path)
    sessions = load_latest_sessions(conn, args.agent, args.limit)
    stats = get_session_stats(conn, args.agent)
    conn.close()

    if not sessions:
        print(f"[SESSION_LOAD] {args.agent} 尚無 session 記錄。")
        return

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

    print("=== END SESSION MEMORY ===")


if __name__ == "__main__":
    main()
