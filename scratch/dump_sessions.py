#!/usr/bin/env python3
"""Dump all sessions from the SMPP database."""
import sqlite3
import sys

sys.stdout.reconfigure(encoding='utf-8')

db_path = r'd:\hermes-agent\memory\session_state.db'
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
c = conn.cursor()

# List tables
c.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [r[0] for r in c.fetchall()]
print(f"Tables: {tables}")
print()

# Dump all sessions
for table in tables:
    c.execute(f"SELECT * FROM [{table}] ORDER BY rowid")
    rows = c.fetchall()
    if rows:
        cols = rows[0].keys()
        print(f"=== {table} ({len(rows)} rows) ===")
        print(f"Columns: {list(cols)}")
        for i, r in enumerate(rows):
            print(f"\n--- Row {i} ---")
            for col in cols:
                val = r[col]
                if val is not None:
                    # Truncate long values for readability
                    s = str(val)
                    if len(s) > 300:
                        s = s[:300] + "..."
                    print(f"  {col}: {s}")
        print()

conn.close()
