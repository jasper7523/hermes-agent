#!/usr/bin/env python3
"""session_save.py — Agent 完成 StepGate 循環後儲存 session 狀態

用法：
    python memory/scripts/session_save.py --agent N7 --summary "..." [--decisions "..."] [--next-steps "..."] [--tags "..."] [--steps 2]

所有參數皆可透過 run_command 傳入。
"""

import argparse
import json
import sys
from pathlib import Path
from datetime import datetime, timezone
from urllib.request import Request, urlopen
from urllib.error import URLError

sys.path.insert(0, str(Path(__file__).parent))
from agent_session_db import get_db_path, init_db, save_session, mark_synced

sys.stdout.reconfigure(encoding='utf-8')

N6_INGEST_URL = "http://127.0.0.1:6060/api/ingest"


def push_to_n6(agent_id: str, session_id: int, summary: str,
               decisions: str, next_steps: str, tags: str) -> bool:
    """Non-blocking push to N6. Returns True if successful."""
    payload = json.dumps({
        "agent_id": agent_id,
        "source": "smpp",
        "source_id": f"{agent_id}_session_{session_id}",
        "content": json.dumps({
            "summary": summary,
            "decisions": decisions,
            "next_steps": next_steps,
        }, ensure_ascii=False),
        "tags": [t.strip() for t in tags.split(",") if t.strip()] + ["smpp", "session"],
        "namespace": "session",
        "channel": "smpp",
    }, ensure_ascii=False).encode("utf-8")

    req = Request(N6_INGEST_URL, data=payload,
                  headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urlopen(req, timeout=5) as resp:
            return resp.status == 200
    except (URLError, OSError, TimeoutError):
        return False


def main():
    parser = argparse.ArgumentParser(description="儲存 Agent session 狀態")
    parser.add_argument("--agent", default="N7", help="Agent ID (預設: N7)")
    parser.add_argument("--summary", required=True, help="本次工作摘要")
    parser.add_argument("--decisions", default="", help="關鍵決策記錄")
    parser.add_argument("--next-steps", default="", help="後續待辦事項")
    parser.add_argument("--tags", default="", help="標籤（逗號分隔）")
    parser.add_argument("--steps", type=int, default=0, help="本次 StepGate 循環數")
    parser.add_argument("--root", default=None, help="Agent 工作區根目錄")
    args = parser.parse_args()

    root = Path(args.root) if args.root else Path(__file__).parent.parent.parent
    db_path = get_db_path(root)
    conn = init_db(db_path)

    session_id = save_session(
        conn=conn,
        agent_id=args.agent,
        summary=args.summary,
        decisions=args.decisions,
        next_steps=args.next_steps,
        tags=args.tags,
        stepgate_count=args.steps,
        session_ts=datetime.now(timezone.utc).isoformat(),
    )

    # ─── Push to N6 (non-blocking) ───
    pushed = push_to_n6(
        agent_id=args.agent,
        session_id=session_id,
        summary=args.summary,
        decisions=args.decisions,
        next_steps=args.next_steps,
        tags=args.tags,
    )
    if pushed:
        mark_synced(conn, session_id)

    conn.close()

    sync_status = "synced" if pushed else "pending (Inspector will harvest)"
    print(f"[SESSION_SAVE] {args.agent} session #{session_id} saved to {db_path}")
    print(f"  Summary: {args.summary[:80]}...")
    print(f"  StepGate count: {args.steps}")
    print(f"  Tags: {args.tags or '(none)'}")
    print(f"  N6 push: {sync_status}")

    # ─── N7-FIX-20260522: IDE 對話 DB 健康維護 ───
    # 在 session 存檔完成後，非阻塞式檢查 Antigravity IDE 的對話 DB
    # 是否因 WAL 碎片膨脹需要壓縮。閾值：50 MB 總大小 + 10 MB 碎片。
    try:
        shared_dir = Path(__file__).parent.parent.parent.parent / ".shared"
        compact_script = shared_dir / "compact_ide_dbs.py"
        if compact_script.exists():
            sys.path.insert(0, str(shared_dir))
            from compact_ide_dbs import scan_and_compact
            results = scan_and_compact(threshold_mb=50, dry_run=False)
            if results:
                total_saved = sum(r["saved_mb"] for r in results if r["success"])
                if total_saved > 0:
                    print(f"  IDE DB compact: saved {total_saved:.1f} MB")
    except Exception as e:
        # 絕不因 DB 維護失敗而阻斷 session 存檔流程
        print(f"  IDE DB compact: skipped ({e})")


if __name__ == "__main__":
    main()

