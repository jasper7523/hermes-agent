# N6 Phase 2 — Task 13: Inspector 巡檢引擎

> **For agentic workers:** Use superpowers:subagent-driven-development to implement.

**Goal:** 實現週期性巡檢引擎，整合 γ-decay 晉升、歸檔候選偵測、FTS5 完整性、Markdown 同步。

**Architecture:** 單次巡檢函式 `run_inspection()` + CLI 入口支援 `--once`（外部 cron）和 `--daemon`（asyncio loop）。巡檢結果寫入 DB（namespace=system）。

**依賴：** `decay.py`, `markdown_sync.py` (Task 12), `store.py`, `config.py`

---

## 檔案結構

```
src/n6_memory_broker/
├── inspector.py           # 巡檢引擎（本 Task 新增）

tests/n6/
├── test_inspector.py      # 巡檢測試（本 Task 新增）
```

---

## Step 1：撰寫預期失敗的測試

```python
# tests/n6/test_inspector.py
"""Test Inspector — periodic inspection engine."""
import pytest
from n6_memory_broker.inspector import run_inspection, InspectionReport
from n6_memory_broker.store import insert_memory
from n6_memory_broker.models import MemoryEntry


def test_run_inspection_empty_db(tmp_db, tmp_markdown_root):
    """Inspection on empty DB should return zeros report."""
    report = run_inspection(tmp_db, tmp_markdown_root)
    assert isinstance(report, InspectionReport)
    assert report.promoted_count == 0
    assert report.archive_candidate_count == 0
    assert report.fts_ok is True


def test_run_inspection_with_data(tmp_db, tmp_markdown_root):
    """Inspection with data should report sync stats."""
    entry = MemoryEntry(agent_id="N5", content="Inspector test mem")
    insert_memory(tmp_db, entry)
    report = run_inspection(tmp_db, tmp_markdown_root)
    assert report.sync_report is not None
    assert report.sync_report["db_to_md"]["written"] == 1
    assert report.memory_count == 1


def test_run_inspection_fts_integrity(tmp_db, tmp_markdown_root):
    """FTS5 integrity check should pass on healthy DB."""
    report = run_inspection(tmp_db, tmp_markdown_root)
    assert report.fts_ok is True


def test_inspection_report_to_dict(tmp_db, tmp_markdown_root):
    """InspectionReport should serialize to dict."""
    report = run_inspection(tmp_db, tmp_markdown_root)
    d = report.to_dict()
    assert "timestamp" in d
    assert "promoted_count" in d
    assert "fts_ok" in d
```

- [ ] **Step 2：執行測試確認失敗**

執行：`cd D:\Agent_Hub\agents\Mem_Agent && python -m pytest tests/n6/test_inspector.py -v`

- [ ] **Step 3：實作 inspector.py**

```python
# src/n6_memory_broker/inspector.py
"""Inspector — periodic inspection engine for N6 Memory Broker.

Usage:
    python -m n6_memory_broker.inspector --once       # single run
    python -m n6_memory_broker.inspector --daemon      # 2h loop
"""
import argparse
import asyncio
import sqlite3
import sys
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path

from n6_memory_broker.decay import promote_tiers, find_archive_candidates
from n6_memory_broker.markdown_sync import full_sync
from n6_memory_broker.store import insert_memory
from n6_memory_broker.models import MemoryEntry

INSPECTION_INTERVAL_HOURS = 2


@dataclass
class InspectionReport:
    timestamp: str = ""
    memory_count: int = 0
    promoted_count: int = 0
    archive_candidate_count: int = 0
    fts_ok: bool = True
    sync_report: dict = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> dict:
        return asdict(self)


def _check_fts_integrity(conn: sqlite3.Connection) -> bool:
    """Run FTS5 integrity-check. Returns True if OK."""
    try:
        conn.execute("INSERT INTO memories_fts(memories_fts) VALUES('integrity-check')")
        return True
    except sqlite3.DatabaseError:
        return False


def run_inspection(
    conn: sqlite3.Connection,
    md_root: Path | None = None,
) -> InspectionReport:
    """Execute a single inspection cycle."""
    report = InspectionReport()

    # 1. Memory count
    row = conn.execute("SELECT COUNT(*) as cnt FROM memories").fetchone()
    report.memory_count = row["cnt"] if row else 0

    # 2. Tier promotion
    report.promoted_count = promote_tiers(conn)

    # 3. Archive candidates (report only, no action)
    candidates = find_archive_candidates(conn)
    report.archive_candidate_count = len(candidates)

    # 4. FTS5 integrity
    report.fts_ok = _check_fts_integrity(conn)

    # 5. Markdown sync (if root provided)
    if md_root and md_root.exists():
        report.sync_report = full_sync(conn, md_root)

    return report


def _save_report_to_db(conn: sqlite3.Connection, report: InspectionReport) -> None:
    """Persist inspection report as a system memory."""
    import json
    entry = MemoryEntry(
        agent_id="N6",
        content=json.dumps(report.to_dict(), ensure_ascii=False, indent=2),
        namespace="system",
        tags=["inspection", "auto"],
        channel="inspector",
    )
    insert_memory(conn, entry)


async def daemon_loop(db_path: Path, md_root: Path | None = None) -> None:
    """Run inspections every INSPECTION_INTERVAL_HOURS."""
    from n6_memory_broker.schema import init_db
    while True:
        conn = init_db(db_path)
        try:
            report = run_inspection(conn, md_root)
            _save_report_to_db(conn, report)
            print(f"[INSPECTOR] {report.timestamp}: "
                  f"mems={report.memory_count} promoted={report.promoted_count} "
                  f"archive_candidates={report.archive_candidate_count} "
                  f"fts_ok={report.fts_ok}")
        finally:
            conn.close()
        await asyncio.sleep(INSPECTION_INTERVAL_HOURS * 3600)


def main():
    parser = argparse.ArgumentParser(description="N6 Inspector")
    parser.add_argument("--once", action="store_true", help="Run once and exit")
    parser.add_argument("--daemon", action="store_true", help="Run as daemon")
    parser.add_argument("--db", default=None, help="DB path")
    parser.add_argument("--md-root", default=None, help="Markdown root")
    args = parser.parse_args()

    from n6_memory_broker.config import N6_ROOT, DB_PATH
    db_path = Path(args.db) if args.db else DB_PATH
    md_root = Path(args.md_root) if args.md_root else N6_ROOT / "memories"

    if args.once:
        from n6_memory_broker.schema import init_db
        conn = init_db(db_path)
        report = run_inspection(conn, md_root)
        _save_report_to_db(conn, report)
        conn.close()
        import json
        print(json.dumps(report.to_dict(), ensure_ascii=False, indent=2))
    elif args.daemon:
        asyncio.run(daemon_loop(db_path, md_root))
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
```

- [ ] **Step 4：執行測試確認通過**

執行：`cd D:\Agent_Hub\agents\Mem_Agent && python -m pytest tests/n6/test_inspector.py -v`

- [ ] **Step 5：提交**

```bash
git add src/n6_memory_broker/inspector.py tests/n6/test_inspector.py
git commit -m "feat(n6): inspector — periodic inspection engine with CLI"
```
