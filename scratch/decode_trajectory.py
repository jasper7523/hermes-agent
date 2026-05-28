"""Decode the base64-encoded protobuf trajectory summaries from state.vscdb."""
import sqlite3
import os
import base64
import re

db_path = os.path.join(os.environ['APPDATA'], 'Antigravity IDE', 'User', 'globalStorage', 'state.vscdb')
conn = sqlite3.connect(f'file:{db_path}?mode=ro', uri=True)
cursor = conn.cursor()

cursor.execute("SELECT value FROM ItemTable WHERE key = 'antigravityUnifiedStateSync.trajectorySummaries'")
row = cursor.fetchone()
if row:
    val = row[0]
    print(f"Raw value length: {len(val)}")
    
    # The value appears to be base64-encoded protobuf
    # Let's try to decode it
    try:
        decoded = base64.b64decode(val)
        print(f"Decoded binary length: {len(decoded)} bytes")
        
        # Search for UUID patterns in the decoded binary
        text = decoded.decode('utf-8', errors='ignore')
        uuids = re.findall(r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}', text)
        unique_uuids = list(set(uuids))
        print(f"Unique conversation UUIDs: {len(unique_uuids)}")
        
        # Check recent ones
        recent = [
            "ed95ed37-f2bf-450e-9003-e10dbb89ef8c",
            "c37f1bf8-2c7e-4adf-b19b-52d127087508",
            "feb1937f-b12a-43a3-8361-a2834f630815",
            "11091269-dc13-4fe2-9789-4facc17964e5",
            "90863f97-3088-49a8-8708-4e594b0e43e7"
        ]
        print("\nRecent conversation check:")
        for rid in recent:
            found = rid in unique_uuids
            print(f"  {rid}: {'FOUND' if found else 'MISSING'}")
        
        # Show first 500 chars of decoded text to understand format
        print(f"\nDecoded text (first 500 chars):")
        print(text[:500])
        
    except Exception as e:
        print(f"Base64 decode failed: {e}")
        
        # Maybe it's raw protobuf, not base64
        # Try to interpret as raw bytes
        if isinstance(val, bytes):
            text = val.decode('utf-8', errors='ignore')
        else:
            text = val
            
        # Look for embedded base64 chunks
        # The value starts with "Cp" which is base64 for protobuf field 1
        # Try decoding chunks
        chunks = val.split('\n')
        print(f"Chunks: {len(chunks)}")

conn.close()
