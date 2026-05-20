#!/usr/bin/env python3
"""Check the new Antigravity IDE's state.vscdb for conversation index state."""
import sqlite3
import os
import json

# Check both old and new state.vscdb
paths = {
    "Old (Antigravity)": r"C:\Users\promy\AppData\Roaming\Antigravity\User\globalStorage\state.vscdb",
    "New (Antigravity IDE)": r"C:\Users\promy\AppData\Roaming\Antigravity IDE\User\globalStorage\state.vscdb",
}

for label, db_path in paths.items():
    print(f"\n{'='*60}")
    print(f"  {label}")
    print(f"  Path: {db_path}")
    print(f"  Exists: {os.path.exists(db_path)}")
    if not os.path.exists(db_path):
        continue
    
    print(f"  Size: {os.path.getsize(db_path)} bytes")
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    # Check key conversation-related entries
    keys_to_check = [
        "antigravityUnifiedStateSync.trajectorySummaries",
        "chat.ChatSessionStore.index",
    ]
    
    for key in keys_to_check:
        c.execute("SELECT length(value) FROM ItemTable WHERE key=?", (key,))
        row = c.fetchone()
        if row:
            print(f"\n  Key: {key}")
            print(f"    Size: {row[0]} bytes")
            
            # For JSON keys, try to parse and count entries
            c.execute("SELECT value FROM ItemTable WHERE key=?", (key,))
            val = c.fetchone()[0]
            if isinstance(val, str) and val.startswith('{'):
                try:
                    data = json.loads(val)
                    if 'entries' in data:
                        print(f"    Entries: {len(data['entries'])}")
                    else:
                        print(f"    Keys: {list(data.keys())[:10]}")
                except:
                    print(f"    (not parseable JSON)")
            elif isinstance(val, bytes):
                # Count UUIDs in protobuf
                import re
                uuids = set(re.findall(rb'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}', val))
                print(f"    UUIDs found: {len(uuids)}")
                # Check for the missing conversation IDs
                for check_id in ['a0af2503', 'fb9a0c95', 'aebe795c']:
                    found = check_id.encode() in val
                    print(f"    Contains {check_id}: {found}")
        else:
            print(f"\n  Key: {key}")
            print(f"    ❌ NOT FOUND")
    
    # Check for any other antigravity-related keys
    c.execute("SELECT key, length(value) FROM ItemTable WHERE key LIKE '%antigravity%' OR key LIKE '%trajectory%' OR key LIKE '%chat%' ORDER BY key")
    rows = c.fetchall()
    print(f"\n  All related keys:")
    for key, size in rows:
        print(f"    {key}: {size} bytes")
    
    conn.close()
