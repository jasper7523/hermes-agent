#!/usr/bin/env python3
"""Check the new Antigravity IDE state.vscdb trajectorySummaries for missing conversation IDs."""
import sqlite3, re

db = r"C:\Users\promy\AppData\Roaming\Antigravity IDE\User\globalStorage\state.vscdb"
conn = sqlite3.connect(db)
c = conn.cursor()

# Check trajectorySummaries
key = "antigravityUnifiedStateSync.trajectorySummaries"
c.execute("SELECT value FROM ItemTable WHERE key=?", (key,))
row = c.fetchone()
if row:
    val = row[0]
    if isinstance(val, str):
        val = val.encode()
    print(f"trajectorySummaries: {len(val)} bytes")
    uuids = set(re.findall(rb"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", val))
    print(f"UUIDs in trajectorySummaries: {len(uuids)}")
    for cid in ["a0af2503", "fb9a0c95", "aebe795c"]:
        print(f"  {cid}: {cid.encode() in val}")

# Check ChatSessionStore
key2 = "chat.ChatSessionStore.index"
c.execute("SELECT value FROM ItemTable WHERE key=?", (key2,))
row = c.fetchone()
if row:
    print(f"\nChatSessionStore.index: {repr(row[0])}")

conn.close()
