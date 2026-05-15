"""Agent Session DB — 統一 Schema 模組（Phase 0 PoC）

所有 Agent（N1-N9）共用同一套 SQLite schema，
避免日後 N6 彙整時遇到碎片化問題。

Schema v1：
  - sessions 表：記錄每次對話的摘要、決策、下一步
  - sessions_fts：FTS5 全文搜尋索引
"""

import sqlite3
import json
import os
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional

SCHEMA_VERSION = 1

# ─── DB 路徑解析 ───────────────────────────────────────────────────────────────

def get_db_path(agent_root: Optional[Path] = None) -> Path:
    """取得 state.db 路徑。若未指定 agent_root，使用 cwd。"""
    root = agent_root or Path.cwd()
    db_dir = root / "memory"
    db_dir.mkdir(parents=True, exist_ok=True)
    return db_dir / "session_state.db"


# ─── DB 初始化 ─────────────────────────────────────────────────────────────────

def init_db(db_path: Path) -> sqlite3.Connection:
    """初始化資料庫，建立 schema 和 FTS5 索引。"""
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")

    conn.executescript("""
        CREATE TABLE IF NOT EXISTS schema_version (
            version INTEGER NOT NULL
        );

        CREATE TABLE IF NOT EXISTS sessions (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            agent_id    TEXT NOT NULL,
            session_ts  TEXT NOT NULL,
            stepgate_count INTEGER DEFAULT 0,
            summary     TEXT,
            decisions   TEXT,
            next_steps  TEXT,
            tags        TEXT,
            created_at  TEXT NOT NULL,
            updated_at  TEXT NOT NULL
        );

        CREATE INDEX IF NOT EXISTS idx_sessions_agent
            ON sessions(agent_id, created_at DESC);
    """)

    # FTS5 索引（跳過已存在的情況）
    try:
        conn.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS sessions_fts USING fts5(
                summary, decisions, next_steps,
                content='sessions',
                content_rowid='id'
            )
        """)
    except sqlite3.OperationalError:
        pass  # 已存在

    # Schema version
    ver = conn.execute("SELECT version FROM schema_version").fetchone()
    if not ver:
        conn.execute("INSERT INTO schema_version VALUES (?)", (SCHEMA_VERSION,))
        conn.commit()

    return conn


# ─── 寫入操作 ──────────────────────────────────────────────────────────────────

def save_session(
    conn: sqlite3.Connection,
    agent_id: str,
    summary: str,
    decisions: str = "",
    next_steps: str = "",
    tags: str = "",
    stepgate_count: int = 0,
    session_ts: Optional[str] = None,
) -> int:
    """儲存一筆 session 記錄，回傳 session id。"""
    now = datetime.now(timezone.utc).isoformat()
    ts = session_ts or now

    cur = conn.execute("""
        INSERT INTO sessions
            (agent_id, session_ts, stepgate_count, summary, decisions, next_steps, tags, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (agent_id, ts, stepgate_count, summary, decisions, next_steps, tags, now, now))

    row_id = cur.lastrowid

    # 更新 FTS5 索引
    conn.execute("""
        INSERT INTO sessions_fts(rowid, summary, decisions, next_steps)
        VALUES (?, ?, ?, ?)
    """, (row_id, summary, decisions, next_steps))

    conn.commit()
    return row_id


def update_session(
    conn: sqlite3.Connection,
    session_id: int,
    summary: Optional[str] = None,
    decisions: Optional[str] = None,
    next_steps: Optional[str] = None,
    stepgate_count: Optional[int] = None,
) -> None:
    """更新既有 session 記錄（增量更新）。"""
    updates = []
    params = []
    if summary is not None:
        updates.append("summary = ?")
        params.append(summary)
    if decisions is not None:
        updates.append("decisions = ?")
        params.append(decisions)
    if next_steps is not None:
        updates.append("next_steps = ?")
        params.append(next_steps)
    if stepgate_count is not None:
        updates.append("stepgate_count = ?")
        params.append(stepgate_count)

    if not updates:
        return

    updates.append("updated_at = ?")
    params.append(datetime.now(timezone.utc).isoformat())
    params.append(session_id)

    conn.execute(
        f"UPDATE sessions SET {', '.join(updates)} WHERE id = ?",
        params
    )

    # 重建 FTS5 索引
    row = conn.execute("SELECT summary, decisions, next_steps FROM sessions WHERE id = ?", (session_id,)).fetchone()
    if row:
        conn.execute("DELETE FROM sessions_fts WHERE rowid = ?", (session_id,))
        conn.execute(
            "INSERT INTO sessions_fts(rowid, summary, decisions, next_steps) VALUES (?, ?, ?, ?)",
            (session_id, row["summary"], row["decisions"], row["next_steps"])
        )

    conn.commit()


# ─── 讀取操作 ──────────────────────────────────────────────────────────────────

def load_latest_sessions(
    conn: sqlite3.Connection,
    agent_id: str,
    limit: int = 3,
) -> list[dict]:
    """載入指定 Agent 最近 N 筆 session。"""
    rows = conn.execute("""
        SELECT id, agent_id, session_ts, stepgate_count,
               summary, decisions, next_steps, tags, created_at
        FROM sessions
        WHERE agent_id = ?
        ORDER BY created_at DESC
        LIMIT ?
    """, (agent_id, limit)).fetchall()

    return [dict(r) for r in rows]


def search_sessions(
    conn: sqlite3.Connection,
    query: str,
    agent_id: Optional[str] = None,
    limit: int = 5,
) -> list[dict]:
    """用 FTS5 搜尋 session 記錄。"""
    if agent_id:
        rows = conn.execute("""
            SELECT s.id, s.agent_id, s.summary, s.decisions, s.next_steps, s.created_at
            FROM sessions s
            JOIN sessions_fts f ON s.id = f.rowid
            WHERE sessions_fts MATCH ? AND s.agent_id = ?
            ORDER BY rank
            LIMIT ?
        """, (query, agent_id, limit)).fetchall()
    else:
        rows = conn.execute("""
            SELECT s.id, s.agent_id, s.summary, s.decisions, s.next_steps, s.created_at
            FROM sessions s
            JOIN sessions_fts f ON s.id = f.rowid
            WHERE sessions_fts MATCH ?
            ORDER BY rank
            LIMIT ?
        """, (query, limit)).fetchall()

    return [dict(r) for r in rows]


def get_session_stats(conn: sqlite3.Connection, agent_id: str) -> dict:
    """取得 Agent 的 session 統計資訊。"""
    row = conn.execute("""
        SELECT COUNT(*) as total,
               MAX(created_at) as latest,
               SUM(stepgate_count) as total_steps
        FROM sessions WHERE agent_id = ?
    """, (agent_id,)).fetchone()
    return dict(row) if row else {}
