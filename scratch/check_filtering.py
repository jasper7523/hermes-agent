"""Check what the IDE is actually filtering on - project assignment, workspace filter, etc."""
import sqlite3, os, base64, re, sys
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

db_path = Path(os.environ['APPDATA']) / 'Antigravity IDE' / 'User' / 'globalStorage' / 'state.vscdb'
KEY = 'antigravityUnifiedStateSync.trajectorySummaries'

conn = sqlite3.connect(f'file:{db_path}?mode=ro', uri=True)
cursor = conn.cursor()

# 1. Check trajectorySummaries
cursor.execute('SELECT value FROM ItemTable WHERE key = ?', (KEY,))
row = cursor.fetchone()
decoded = base64.b64decode(row[0])
uuids = set(re.findall(
    r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}',
    decoded.decode('utf-8', errors='ignore')))
print(f"trajectorySummaries UUIDs: {len(uuids)}")

# 2. Check ALL keys that might relate to filtering
print("\n=== Keys containing 'project' or 'filter' or 'workspace' ===")
cursor.execute("SELECT key, length(value) FROM ItemTable WHERE key LIKE '%project%' OR key LIKE '%filter%' OR key LIKE '%workspace%' ORDER BY key")
for r in cursor.fetchall():
    print(f"  {r[0]} ({r[1]} bytes)")

# 3. Check migrate_convos_into_projects related keys
print("\n=== Keys containing 'migrate' ===")
cursor.execute("SELECT key, length(value) FROM ItemTable WHERE key LIKE '%migrate%' ORDER BY key")
for r in cursor.fetchall():
    print(f"  {r[0]} ({r[1]} bytes)")
    cursor2 = conn.cursor()
    cursor2.execute("SELECT value FROM ItemTable WHERE key = ?", (r[0],))
    val = cursor2.fetchone()[0]
    if len(val) < 500:
        print(f"    value: {val}")

# 4. Check sidebar-related keys
print("\n=== Keys containing 'sidebar' ===")
cursor.execute("SELECT key, length(value) FROM ItemTable WHERE key LIKE '%sidebar%' OR key LIKE '%Sidebar%' ORDER BY key")
for r in cursor.fetchall():
    print(f"  {r[0]} ({r[1]} bytes)")

# 5. Check the antigravity_state.pbtxt for migrate status
state_path = Path(os.environ['USERPROFILE']) / '.gemini' / 'antigravity-ide' / 'antigravity_state.pbtxt'
print(f"\n=== antigravity_state.pbtxt ===")
print(state_path.read_text(encoding='utf-8'))

# 6. Check if there's a "selected project" or workspace filter active
print("\n=== Keys containing 'selected' or 'active' ===")
cursor.execute("SELECT key, length(value) FROM ItemTable WHERE key LIKE '%selected%' OR key LIKE '%activeProject%' OR key LIKE '%currentProject%' ORDER BY key")
for r in cursor.fetchall():
    print(f"  {r[0]} ({r[1]} bytes)")
    if r[1] < 500:
        cursor2 = conn.cursor()
        cursor2.execute("SELECT value FROM ItemTable WHERE key = ?", (r[0],))
        val = cursor2.fetchone()[0]
        print(f"    value: {val[:200]}")

conn.close()
