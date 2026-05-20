#!/usr/bin/env python3
"""Inspect Antigravity IDE conversation .db files."""
import sqlite3
import sys

db_path = sys.argv[1] if len(sys.argv) > 1 else r'C:\Users\promy\.gemini\antigravity-ide\conversations\a0af2503-6528-4691-850e-bea17cc94e66.db'
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

# List tables and their schemas
cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [t['name'] for t in cur.fetchall()]
print(f"=== DB: {db_path} ===")
print(f"Tables: {tables}\n")

for table in tables:
    cur.execute(f"SELECT count(*) as cnt FROM [{table}]")
    count = cur.fetchone()['cnt']
    cur.execute(f"PRAGMA table_info([{table}])")
    cols = [(c['name'], c['type']) for c in cur.fetchall()]
    print(f"--- {table} ({count} rows) ---")
    print(f"  Columns: {cols}")
    
    if count > 0 and count <= 5:
        cur.execute(f"SELECT * FROM [{table}]")
        for row in cur.fetchall():
            d = dict(row)
            # Truncate long values
            for k, v in d.items():
                if isinstance(v, (str, bytes)) and len(str(v)) > 200:
                    d[k] = str(v)[:200] + '...'
            print(f"  ROW: {d}")
    elif count > 5:
        cur.execute(f"SELECT * FROM [{table}] LIMIT 3")
        for row in cur.fetchall():
            d = dict(row)
            for k, v in d.items():
                if isinstance(v, (str, bytes)) and len(str(v)) > 200:
                    d[k] = str(v)[:200] + '...'
            print(f"  ROW: {d}")
        print(f"  ... ({count - 3} more rows)")
    print()

conn.close()
