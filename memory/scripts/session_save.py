#!/usr/bin/env python3
"""session_save.py — Agent 完成 StepGate 循環後儲存 session 狀態

用法：
    python memory/scripts/session_save.py --agent N7 --summary "..." [--decisions "..."] [--next-steps "..."] [--tags "..."] [--steps 2]

所有參數皆可透過 run_command 傳入。
"""

import argparse
import sys
from pathlib import Path
from datetime import datetime, timezone

sys.path.insert(0, str(Path(__file__).parent))
from agent_session_db import get_db_path, init_db, save_session

sys.stdout.reconfigure(encoding='utf-8')


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

    conn.close()

    print(f"[SESSION_SAVE] {args.agent} session #{session_id} saved to {db_path}")
    print(f"  Summary: {args.summary[:80]}...")
    print(f"  StepGate count: {args.steps}")
    print(f"  Tags: {args.tags or '(none)'}")


if __name__ == "__main__":
    main()
