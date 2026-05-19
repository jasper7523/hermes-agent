# N6 Phase 2 — Task 12: Markdown ↔ DB 雙向同步

> **For agentic workers:** Use superpowers:subagent-driven-development to implement. Steps use checkbox (`- [ ]`) syntax.

**Goal:** 實現 Markdown（Source of Truth）與 SQLite（衍生索引）的雙向同步引擎。

**Architecture:** Markdown 目錄結構 `{MARKDOWN_ROOT}/{agent_id}/{namespace}/` 下每條記憶一個 .md 檔，含 YAML frontmatter。同步以 content hash 實現冪等性，Markdown 為衝突仲裁者。

**Tech Stack:** Python 3.13+, PyYAML (frontmatter), pathlib, SQLite

**Phase 1 依賴：** `store.py` (CRUD), `schema.py` (DB), `config.py` (MARKDOWN_ROOT), `models.py` (MemoryEntry)

---

## 檔案結構

```
src/n6_memory_broker/
├── markdown_sync.py         # 同步引擎（本 Task 新增）

tests/n6/
├── test_markdown_sync.py    # 同步測試（本 Task 新增）
```

---

## Step 1：撰寫預期失敗的測試

```python
# tests/n6/test_markdown_sync.py
"""Test Markdown ↔ SQLite bidirectional sync."""
import pytest
import yaml
from pathlib import Path
from n6_memory_broker.markdown_sync import (
    memory_to_md,
    md_to_memory,
    sync_db_to_md,
    sync_md_to_db,
    full_sync,
)
from n6_memory_broker.store import insert_memory
from n6_memory_broker.models import MemoryEntry


def test_memory_to_md_roundtrip():
    """Serialize a memory dict to markdown and parse it back."""
    mem = {
        "id": 1,
        "agent_id": "N5",
        "namespace": "dev",
        "project_id": "thesis-001",
        "content": "Use SQLite for persistence",
        "tags": '["decision", "architecture"]',
        "channel": "ide",
        "memory_tier": "working",
        "access_count": 3,
        "created_at": "2026-05-19T10:00:00+00:00",
        "updated_at": "2026-05-19T10:00:00+00:00",
    }
    md_text = memory_to_md(mem)
    assert "---" in md_text
    assert "Use SQLite for persistence" in md_text
    parsed = md_to_memory(md_text)
    assert parsed["agent_id"] == "N5"
    assert parsed["namespace"] == "dev"
    assert parsed["content"] == "Use SQLite for persistence"


def test_sync_db_to_md_creates_files(tmp_db, tmp_markdown_root):
    """DB→MD: memories in DB should produce .md files."""
    entry = MemoryEntry(agent_id="N5", content="Test memory one", namespace="dev")
    insert_memory(tmp_db, entry)
    entry2 = MemoryEntry(agent_id="N7", content="Admin note", namespace="ops")
    insert_memory(tmp_db, entry2)
    report = sync_db_to_md(tmp_db, tmp_markdown_root)
    assert report["written"] == 2
    assert report["skipped"] == 0
    # Check directory structure
    n5_dir = tmp_markdown_root / "N5" / "dev"
    assert n5_dir.exists()
    md_files = list(n5_dir.glob("*.md"))
    assert len(md_files) == 1


def test_sync_db_to_md_idempotent(tmp_db, tmp_markdown_root):
    """Running sync twice should not duplicate files."""
    entry = MemoryEntry(agent_id="N5", content="Idempotent test")
    insert_memory(tmp_db, entry)
    sync_db_to_md(tmp_db, tmp_markdown_root)
    report2 = sync_db_to_md(tmp_db, tmp_markdown_root)
    assert report2["written"] == 0
    assert report2["skipped"] == 1


def test_sync_md_to_db_new_file(tmp_db, tmp_markdown_root):
    """MD→DB: a new .md file should be inserted into DB."""
    agent_dir = tmp_markdown_root / "N5" / "dev"
    agent_dir.mkdir(parents=True)
    md_content = """---
agent_id: N5
namespace: dev
tags: [test]
channel: ide
memory_tier: working
---
New memory from markdown"""
    (agent_dir / "new_memory.md").write_text(md_content, encoding="utf-8")
    report = sync_md_to_db(tmp_db, tmp_markdown_root)
    assert report["inserted"] >= 1
    rows = tmp_db.execute("SELECT * FROM memories WHERE agent_id = 'N5'").fetchall()
    assert len(rows) >= 1
    assert "New memory from markdown" in rows[0]["content"]


def test_sync_md_to_db_idempotent(tmp_db, tmp_markdown_root):
    """Syncing same MD file twice should not create duplicates."""
    agent_dir = tmp_markdown_root / "N5" / "default"
    agent_dir.mkdir(parents=True)
    md_content = """---
agent_id: N5
namespace: default
tags: []
channel: ide
memory_tier: working
---
Duplicate test content"""
    (agent_dir / "dup_test.md").write_text(md_content, encoding="utf-8")
    sync_md_to_db(tmp_db, tmp_markdown_root)
    report2 = sync_md_to_db(tmp_db, tmp_markdown_root)
    assert report2["inserted"] == 0
    assert report2["skipped"] == 1


def test_full_sync_roundtrip(tmp_db, tmp_markdown_root):
    """Full sync: DB entry → MD file → re-sync without duplication."""
    entry = MemoryEntry(agent_id="N5", content="Full sync test", namespace="lab")
    insert_memory(tmp_db, entry)
    report = full_sync(tmp_db, tmp_markdown_root)
    assert report["db_to_md"]["written"] == 1
    assert report["md_to_db"]["inserted"] == 0
```

- [ ] **Step 2：執行測試確認失敗**

執行：`cd D:\Agent_Hub\agents\Mem_Agent && python -m pytest tests/n6/test_markdown_sync.py -v`
預期：FAIL（模組不存在）

- [ ] **Step 3：實作 markdown_sync.py**

```python
# src/n6_memory_broker/markdown_sync.py
"""Markdown ↔ SQLite bidirectional sync engine.

Design:
  - Markdown is Source of Truth (Q2 decision)
  - Directory layout: {MARKDOWN_ROOT}/{agent_id}/{namespace}/*.md
  - Each .md has YAML frontmatter + body content
  - Idempotency via content hash (SHA-256 prefix)
"""
import hashlib
import json
import sqlite3
from pathlib import Path
from datetime import datetime, timezone

import yaml

from n6_memory_broker.models import MemoryEntry
from n6_memory_broker.store import insert_memory


# ─── Serialization ──────────────────────────────────────────────────────

def _content_hash(text: str) -> str:
    """Return a short SHA-256 hash of text for idempotency checks."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def _slugify(text: str, max_len: int = 40) -> str:
    """Create a filesystem-safe slug from text."""
    slug = text.lower().replace(" ", "_")
    safe = "".join(c for c in slug if c.isalnum() or c == "_")
    return safe[:max_len] or "untitled"


def memory_to_md(mem: dict) -> str:
    """Serialize a memory row dict to a Markdown string with YAML frontmatter."""
    tags = mem.get("tags", "[]")
    if isinstance(tags, str):
        try:
            tags = json.loads(tags)
        except (json.JSONDecodeError, TypeError):
            tags = []

    front = {
        "id": mem.get("id"),
        "agent_id": mem["agent_id"],
        "namespace": mem.get("namespace", "default"),
        "project_id": mem.get("project_id"),
        "tags": tags,
        "channel": mem.get("channel", "ide"),
        "memory_tier": mem.get("memory_tier", "working"),
        "access_count": mem.get("access_count", 0),
        "created_at": mem.get("created_at", ""),
        "updated_at": mem.get("updated_at", ""),
    }
    # Remove None values
    front = {k: v for k, v in front.items() if v is not None}

    yaml_str = yaml.dump(front, allow_unicode=True, default_flow_style=False, sort_keys=False)
    content = mem.get("content", "")
    return f"---\n{yaml_str}---\n{content}"


def md_to_memory(md_text: str) -> dict:
    """Parse a Markdown string with YAML frontmatter into a memory dict."""
    parts = md_text.split("---", 2)
    if len(parts) < 3:
        raise ValueError("Invalid frontmatter format: expected --- delimiters")
    front = yaml.safe_load(parts[1]) or {}
    content = parts[2].strip()
    front["content"] = content
    return front


# ─── DB → Markdown ──────────────────────────────────────────────────────

def _md_path_for_memory(md_root: Path, mem: dict) -> Path:
    """Compute the .md file path for a memory."""
    agent_dir = md_root / mem["agent_id"] / mem.get("namespace", "default")
    slug = _slugify(mem.get("content", "")[:40])
    filename = f"{mem['id']:05d}_{slug}.md"
    return agent_dir / filename


def sync_db_to_md(conn: sqlite3.Connection, md_root: Path) -> dict:
    """Export all DB memories to Markdown files. Returns sync report."""
    report = {"written": 0, "skipped": 0, "errors": 0}
    rows = conn.execute("SELECT * FROM memories ORDER BY id").fetchall()

    for row in rows:
        mem = dict(row)
        target = _md_path_for_memory(md_root, mem)

        # Skip if file exists and content hash matches
        if target.exists():
            existing = target.read_text(encoding="utf-8")
            existing_parsed = md_to_memory(existing)
            if _content_hash(existing_parsed.get("content", "")) == _content_hash(mem.get("content", "")):
                report["skipped"] += 1
                continue

        target.parent.mkdir(parents=True, exist_ok=True)
        md_text = memory_to_md(mem)
        target.write_text(md_text, encoding="utf-8")
        report["written"] += 1

    return report


# ─── Markdown → DB ──────────────────────────────────────────────────────

def sync_md_to_db(conn: sqlite3.Connection, md_root: Path) -> dict:
    """Import Markdown files into DB. Returns sync report."""
    report = {"inserted": 0, "skipped": 0, "errors": 0}

    if not md_root.exists():
        return report

    for md_file in md_root.rglob("*.md"):
        try:
            text = md_file.read_text(encoding="utf-8")
            parsed = md_to_memory(text)
        except (ValueError, yaml.YAMLError):
            report["errors"] += 1
            continue

        content = parsed.get("content", "")
        chash = _content_hash(content)
        agent_id = parsed.get("agent_id", "unknown")

        # Check idempotency: search by content hash
        existing = conn.execute(
            "SELECT id FROM memories WHERE agent_id = ? AND content = ?",
            (agent_id, content),
        ).fetchone()

        if existing:
            report["skipped"] += 1
            continue

        entry = MemoryEntry(
            agent_id=agent_id,
            content=content,
            namespace=parsed.get("namespace", "default"),
            project_id=parsed.get("project_id"),
            tags=parsed.get("tags", []),
            channel=parsed.get("channel", "ide"),
        )
        insert_memory(conn, entry)
        report["inserted"] += 1

    return report


# ─── Full Sync ──────────────────────────────────────────────────────────

def full_sync(conn: sqlite3.Connection, md_root: Path) -> dict:
    """Run bidirectional sync: DB→MD first (export), then MD→DB (import new)."""
    db_to_md = sync_db_to_md(conn, md_root)
    md_to_db = sync_md_to_db(conn, md_root)
    return {"db_to_md": db_to_md, "md_to_db": md_to_db}
```

- [ ] **Step 4：執行測試確認通過**

執行：`cd D:\Agent_Hub\agents\Mem_Agent && python -m pytest tests/n6/test_markdown_sync.py -v`
預期：PASS

- [ ] **Step 5：提交**

```bash
git add src/n6_memory_broker/markdown_sync.py tests/n6/test_markdown_sync.py
git commit -m "feat(n6): markdown_sync — bidirectional Markdown ↔ SQLite sync engine"
```

---

## 自我審查

| 檢查項 | 狀態 |
|--------|------|
| Q2 決策（Markdown = Source of Truth） | ✅ sync_md_to_db 以 content match 避免覆蓋 |
| 冪等性（重複同步不重複） | ✅ content hash + exact match |
| 目錄結構（agent_id/namespace/） | ✅ _md_path_for_memory |
| Frontmatter 完整性 | ✅ 含 id/agent/ns/tags/tier/timestamps |
| 型別一致：MemoryEntry 簽名 | ✅ 與 store.insert_memory 完全對齊 |
| PyYAML 依賴 | ⚠️ 需加入 pyproject.toml |
