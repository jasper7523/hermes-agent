#!/usr/bin/env python3
"""
N7 驗證腳本：確認 Antigravity IDE 中 Python + SQLite + FTS5 的完整能力
"""
import sqlite3
import json
import os
import sys
from pathlib import Path
from datetime import datetime

results = {}

# === Test 1: Python 基礎 ===
results["python_version"] = sys.version
results["python_executable"] = sys.executable
results["platform"] = sys.platform

# === Test 2: SQLite 基礎 ===
results["sqlite_version"] = sqlite3.sqlite_version
results["sqlite_api_version"] = sqlite3.version

# === Test 3: SQLite compile options (FTS5 check) ===
conn = sqlite3.connect(":memory:")
opts = [row[0] for row in conn.execute("PRAGMA compile_options").fetchall()]
results["fts5_enabled"] = "ENABLE_FTS5" in opts
results["json_enabled"] = "ENABLE_JSON1" in opts
results["compile_options"] = opts

# === Test 4: 持久化 SQLite 檔案寫入 ===
test_db_path = Path(__file__).parent / "scratch" / "test_session.db"
test_db_path.parent.mkdir(parents=True, exist_ok=True)

conn2 = sqlite3.connect(str(test_db_path))
conn2.execute("PRAGMA journal_mode=WAL")
conn2.execute("""
    CREATE TABLE IF NOT EXISTS agent_sessions (
        id TEXT PRIMARY KEY,
        agent_id TEXT NOT NULL,
        started_at TEXT NOT NULL,
        summary TEXT,
        decisions TEXT,
        next_steps TEXT
    )
""")
conn2.execute("""
    INSERT OR REPLACE INTO agent_sessions VALUES (?, ?, ?, ?, ?, ?)
""", (
    "test-001",
    "N5",
    datetime.now().isoformat(),
    "文獻處理到 Task 11，下次從 Task 12 開始",
    json.dumps({"batch_size": 5, "encoding": "utf-8"}, ensure_ascii=False),
    "繼續 ch2.2 文獻綜合"
))
conn2.commit()

# 驗證讀取
row = conn2.execute("SELECT * FROM agent_sessions WHERE id='test-001'").fetchone()
results["persistent_db_write"] = row is not None
results["persistent_db_path"] = str(test_db_path)
results["persistent_db_read_back"] = {
    "id": row[0], "agent_id": row[1], "summary": row[3]
} if row else None

# === Test 5: FTS5 全文搜尋 ===
try:
    conn2.execute("""
        CREATE VIRTUAL TABLE IF NOT EXISTS sessions_fts USING fts5(
            summary, decisions, next_steps
        )
    """)
    conn2.execute("""
        INSERT INTO sessions_fts VALUES (?, ?, ?)
    """, ("文獻處理到 Task 11", '{"batch_size": 5}', "繼續 ch2.2"))
    
    fts_result = conn2.execute(
        "SELECT * FROM sessions_fts WHERE sessions_fts MATCH '文獻'"
    ).fetchall()
    results["fts5_search_works"] = len(fts_result) > 0
    results["fts5_chinese_search"] = len(fts_result) > 0
except Exception as e:
    results["fts5_error"] = str(e)

conn2.close()

# === Test 6: 檔案 I/O 能力 ===
test_md_path = Path(__file__).parent / "scratch" / "test_session_index.md"
test_md_path.write_text(
    "# N5 Session Index\n\n"
    f"- 最後更新：{datetime.now().isoformat()}\n"
    "- 當前進度：Task 11 完成\n"
    "- 下次待辦：Task 12\n",
    encoding="utf-8"
)
results["markdown_write"] = test_md_path.exists()

# === Test 7: pip 可用性 ===
import subprocess
pip_result = subprocess.run(
    [sys.executable, "-m", "pip", "--version"],
    capture_output=True, text=True
)
results["pip_available"] = pip_result.returncode == 0
results["pip_version"] = pip_result.stdout.strip() if pip_result.returncode == 0 else pip_result.stderr

# === 輸出結果 ===
print("=" * 60)
print("N7 Antigravity Python/SQLite 能力驗證報告")
print("=" * 60)
for key, value in results.items():
    if key == "compile_options":
        print(f"\n{key}:")
        for opt in value:
            print(f"  - {opt}")
    else:
        print(f"{key}: {value}")

print("\n" + "=" * 60)
print("結論：", end="")
critical = [
    results.get("fts5_enabled"),
    results.get("persistent_db_write"),
    results.get("fts5_search_works"),
    results.get("markdown_write"),
    results.get("pip_available"),
]
if all(critical):
    print("✅ 所有關鍵能力均可用 — Antigravity IDE 完整支援 Python + SQLite + FTS5")
else:
    failed = [k for k, v in zip(
        ["FTS5", "DB持久化", "FTS5搜尋", "Markdown寫入", "pip"],
        critical
    ) if not v]
    print(f"⚠️ 以下能力不可用：{', '.join(failed)}")
