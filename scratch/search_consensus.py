import sys
from pathlib import Path

# 確保可以 import 同目錄的模組
sys.path.insert(0, str(Path("d:/hermes-agent/memory/scripts")))
from agent_session_db import get_db_path, init_db, search_sessions, load_latest_sessions

sys.stdout.reconfigure(encoding='utf-8')


def main():
    root = Path("d:/hermes-agent")
    db_path = get_db_path(root)
    if not db_path.exists():
        print("資料庫不存在")
        return
        
    conn = init_db(db_path)
    
    print("--- 搜尋包含 'consensus' 的 session 記錄 ---")
    results = search_sessions(conn, "consensus", limit=20)
    for s in results:
        print(f"ID: {s['id']} | Agent: {s['agent_id']} | Created: {s['created_at']}")
        print(f"Summary: {s['summary']}")
        print(f"Decisions: {s['decisions']}")
        print(f"Next: {s['next_steps']}")
        print("-" * 50)
        
    print("\n--- 搜尋包含 'mcp' 的 session 記錄 ---")
    results_mcp = search_sessions(conn, "mcp", limit=20)
    for s in results_mcp:
        print(f"ID: {s['id']} | Agent: {s['agent_id']} | Created: {s['created_at']}")
        print(f"Summary: {s['summary']}")
        print(f"Decisions: {s['decisions']}")
        print(f"Next: {s['next_steps']}")
        print("-" * 50)

    conn.close()

if __name__ == "__main__":
    main()
