#!/usr/bin/env python3
"""N7 診斷：檢查 hermes_state.py SessionDB 在 Antigravity 中的運作狀態"""
import sqlite3
import sys
import os
from pathlib import Path
from datetime import datetime

sys.stdout.reconfigure(encoding='utf-8')

db_path = Path.home() / ".hermes" / "state.db"
print(f"=== hermes_state.py SessionDB 診斷 ===")
print(f"DB 路徑: {db_path}")
print(f"存在: {db_path.exists()}")

if not db_path.exists():
    print("❌ state.db 不存在，SessionDB 未運作")
    sys.exit(1)

stat = db_path.stat()
print(f"大小: {stat.st_size:,} bytes")
print(f"最後修改: {datetime.fromtimestamp(stat.st_mtime).isoformat()}")

# 檢查 WAL 文件
wal_path = db_path.with_suffix(".db-wal")
shm_path = db_path.with_suffix(".db-shm")
print(f"WAL 檔案: {'存在' if wal_path.exists() else '不存在'} ({wal_path.stat().st_size if wal_path.exists() else 0} bytes)")
print(f"SHM 檔案: {'存在' if shm_path.exists() else '不存在'}")

conn = sqlite3.connect(str(db_path))
conn.row_factory = sqlite3.Row

# Schema version
try:
    ver = conn.execute("SELECT version FROM schema_version").fetchone()
    print(f"Schema 版本: {ver[0] if ver else '未知'}")
except:
    print("Schema 版本: 表不存在")

# 總 session 數
try:
    count = conn.execute("SELECT COUNT(*) FROM sessions").fetchone()[0]
    print(f"\n=== Sessions 統計 ===")
    print(f"總 session 數: {count}")
except Exception as e:
    print(f"❌ sessions 表查詢失敗: {e}")
    conn.close()
    sys.exit(1)

if count == 0:
    print("⚠️ sessions 表為空 — SessionDB 從未被寫入")
    conn.close()
    sys.exit(0)

# 各 source 統計
sources = conn.execute("SELECT source, COUNT(*) as cnt FROM sessions GROUP BY source ORDER BY cnt DESC").fetchall()
print(f"來源分布:")
for s in sources:
    print(f"  {s['source']}: {s['cnt']} 筆")

# 最近 5 筆 session
print(f"\n=== 最近 5 筆 Sessions ===")
recent = conn.execute("""
    SELECT id, source, model, title, started_at, ended_at, message_count, 
           tool_call_count, input_tokens, output_tokens
    FROM sessions 
    ORDER BY started_at DESC 
    LIMIT 5
""").fetchall()

for r in recent:
    started = datetime.fromtimestamp(r['started_at']).strftime('%Y-%m-%d %H:%M') if r['started_at'] else '?'
    ended = datetime.fromtimestamp(r['ended_at']).strftime('%Y-%m-%d %H:%M') if r['ended_at'] else '進行中'
    title = (r['title'] or '(無標題)')[:60]
    print(f"  [{started}~{ended}] {r['source']:8s} | {r['model'] or '?':20s} | msgs={r['message_count']:3d} | tools={r['tool_call_count']:3d} | {title}")

# 最近一筆 session 的時間戳
latest = conn.execute("SELECT MAX(started_at) FROM sessions").fetchone()[0]
latest_dt = datetime.fromtimestamp(latest) if latest else None
print(f"\n最新 session 建立時間: {latest_dt.isoformat() if latest_dt else '無'}")

# 檢查是否有「今天」的 session
today_count = conn.execute("""
    SELECT COUNT(*) FROM sessions 
    WHERE date(started_at, 'unixepoch', 'localtime') = date('now', 'localtime')
""").fetchone()[0]
print(f"今日 session 數: {today_count}")

# Messages 統計
msg_count = conn.execute("SELECT COUNT(*) FROM messages").fetchone()[0]
print(f"\n=== Messages 統計 ===")
print(f"總訊息數: {msg_count:,}")

if msg_count > 0:
    latest_msg = conn.execute("SELECT MAX(timestamp) FROM messages").fetchone()[0]
    latest_msg_dt = datetime.fromtimestamp(latest_msg) if latest_msg else None
    print(f"最新訊息時間: {latest_msg_dt.isoformat() if latest_msg_dt else '無'}")

# FTS5 表是否存在
try:
    fts_count = conn.execute("SELECT COUNT(*) FROM messages_fts").fetchone()[0]
    print(f"FTS5 索引筆數: {fts_count:,}")
except:
    print("FTS5 索引: 不存在")

# 檢查 journal_mode
journal = conn.execute("PRAGMA journal_mode").fetchone()[0]
print(f"\nJournal 模式: {journal}")

conn.close()

# === 結論 ===
print(f"\n{'='*50}")
now = datetime.now()
if latest_dt:
    delta = now - latest_dt
    if delta.days == 0:
        print(f"✅ SessionDB 今日有活動 — 正在運作中")
    elif delta.days < 7:
        print(f"⚠️ SessionDB {delta.days} 天前最後活動 — 可能未在當前環境使用")
    else:
        print(f"❌ SessionDB {delta.days} 天前最後活動 — 目前未在 Antigravity 環境中運作")
        print(f"   說明: hermes_state.py 是 Hermes CLI/Gateway 的狀態儲存")
        print(f"   在 Antigravity IDE 中操作 N7 時，Antigravity 使用自己的 Session 機制")
        print(f"   hermes_state.py 的 SessionDB 不會被觸發")
else:
    print(f"❌ SessionDB 為空 — 從未運作")
