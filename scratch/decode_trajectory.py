#!/usr/bin/env python3
"""Decode and analyze the trajectorySummaries from Antigravity IDE state.vscdb."""
import sqlite3
import base64
import re

db = r"C:\Users\promy\AppData\Roaming\Antigravity IDE\User\globalStorage\state.vscdb"
conn = sqlite3.connect(db)
c = conn.cursor()

key = "antigravityUnifiedStateSync.trajectorySummaries"
c.execute("SELECT value FROM ItemTable WHERE key=?", (key,))
row = c.fetchone()

if not row:
    print("trajectorySummaries NOT FOUND")
    exit(1)

val = row[0]
print(f"Raw value type: {type(val)}")
print(f"Raw value length: {len(val)}")
print(f"First 200 chars: {repr(val[:200])}")

# Try base64 decode
try:
    decoded = base64.b64decode(val)
    print(f"\nBase64 decoded: {len(decoded)} bytes")
    print(f"First 100 bytes hex: {decoded[:100].hex()}")
    
    # Search for UUIDs in decoded
    uuids = set(re.findall(rb"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", decoded))
    print(f"UUIDs found in decoded: {len(uuids)}")
    
    # Check for our missing IDs
    for cid in ["a0af2503", "fb9a0c95", "aebe795c"]:
        print(f"  {cid}: {cid.encode() in decoded}")
    
    # Show a few found UUIDs
    for uid in sorted(list(uuids))[:5]:
        print(f"  Found: {uid.decode()}")
    
except Exception as e:
    print(f"Base64 decode failed: {e}")
    # Try treating as raw bytes
    if isinstance(val, bytes):
        uuids = set(re.findall(rb"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", val))
        print(f"UUIDs in raw bytes: {len(uuids)}")

conn.close()
