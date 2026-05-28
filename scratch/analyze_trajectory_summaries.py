"""Analyze the trajectorySummaries key in state.vscdb - the main sidebar index."""
import sqlite3
import os
import json

db_path = os.path.join(os.environ['APPDATA'], 'Antigravity IDE', 'User', 'globalStorage', 'state.vscdb')
conn = sqlite3.connect(f'file:{db_path}?mode=ro', uri=True)
cursor = conn.cursor()

# Get the trajectorySummaries value
cursor.execute("SELECT value FROM ItemTable WHERE key = 'antigravityUnifiedStateSync.trajectorySummaries'")
row = cursor.fetchone()
if row:
    val = row[0]
    print(f"Value type: {type(val)}")
    print(f"Value length: {len(val)} bytes")
    
    # Try to parse as JSON
    try:
        data = json.loads(val)
        print(f"JSON type: {type(data)}")
        if isinstance(data, dict):
            print(f"Keys: {list(data.keys())[:20]}")
            # Check if it's a list of summaries
            for k, v in list(data.items())[:3]:
                print(f"\n  Key: {k}")
                print(f"  Value type: {type(v)}")
                if isinstance(v, dict):
                    print(f"  Sub-keys: {list(v.keys())[:10]}")
                elif isinstance(v, str):
                    print(f"  Value (first 200): {v[:200]}")
        elif isinstance(data, list):
            print(f"List length: {len(data)}")
            for item in data[:3]:
                print(f"\n  Item type: {type(item)}")
                if isinstance(item, dict):
                    print(f"  Keys: {list(item.keys())[:10]}")
                    if 'id' in item or 'conversationId' in item:
                        print(f"  ID: {item.get('id', item.get('conversationId', 'N/A'))}")
    except json.JSONDecodeError:
        # It might be binary/protobuf
        print(f"Not JSON. First 200 bytes: {val[:200]}")
        # Try to find UUID patterns
        import re
        uuids = re.findall(r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}', val if isinstance(val, str) else val.decode('utf-8', errors='ignore'))
        unique_uuids = list(set(uuids))
        print(f"\nUnique UUIDs found: {len(unique_uuids)}")
        for uid in sorted(unique_uuids)[:10]:
            print(f"  {uid}")

# Also check sidebarWorkspaces
cursor.execute("SELECT value FROM ItemTable WHERE key = 'antigravityUnifiedStateSync.sidebarWorkspaces'")
row = cursor.fetchone()
if row:
    print(f"\n=== sidebarWorkspaces ===")
    try:
        data = json.loads(row[0])
        print(json.dumps(data, indent=2, ensure_ascii=False)[:1000])
    except:
        print(f"Raw (first 500): {row[0][:500]}")

conn.close()
