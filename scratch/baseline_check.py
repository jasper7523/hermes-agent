"""Pre-fix baseline snapshot of state.vscdb."""
import sqlite3, os, base64, re
from datetime import datetime

db_path = os.path.join(os.environ['APPDATA'], 'Antigravity IDE', 'User', 'globalStorage', 'state.vscdb')
conn = sqlite3.connect(f'file:{db_path}?mode=ro', uri=True)
cursor = conn.cursor()

cursor.execute('SELECT value FROM ItemTable WHERE key = ?',
               ('antigravityUnifiedStateSync.trajectorySummaries',))
row = cursor.fetchone()
decoded = base64.b64decode(row[0])
text = decoded.decode('utf-8', errors='ignore')
db_uuids = set(re.findall(
    r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}', text))

now = datetime.now().strftime("%H:%M:%S")
mtime = datetime.fromtimestamp(os.path.getmtime(db_path)).strftime("%Y-%m-%d %H:%M:%S")

print(f"[BASELINE] {now}")
print(f"  trajectorySummaries UUIDs: {len(db_uuids)}")
print(f"  state.vscdb size: {os.path.getsize(db_path)} bytes")
print(f"  state.vscdb mtime: {mtime}")

recent = [
    'ed95ed37-f2bf-450e-9003-e10dbb89ef8c',
    'c37f1bf8-2c7e-4adf-b19b-52d127087508',
    'feb1937f-b12a-43a3-8361-a2834f630815',
    '11091269-dc13-4fe2-9789-4facc17964e5',
]
print("  Recent conversations in index:")
for rid in recent:
    status = "YES" if rid in db_uuids else "NO"
    print(f"    {rid[:20]}... : {status}")

conn.close()
