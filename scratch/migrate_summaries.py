import sqlite3
import shutil
import os
from datetime import datetime

# Paths
old_db = r"C:\Users\promy\AppData\Roaming\Antigravity\User\globalStorage\state.vscdb"
new_db = r"C:\Users\promy\AppData\Roaming\Antigravity IDE\User\globalStorage\state.vscdb"
backup_db = r"C:\Users\promy\AppData\Roaming\Antigravity IDE\User\globalStorage\state.vscdb.pre_migration_backup"

print("Step 1: Backup new IDE state.vscdb...")
shutil.copy2(new_db, backup_db)
print(f"  Backed up to: {backup_db}")

print("\nStep 2: Read trajectorySummaries from old Antigravity...")
old_conn = sqlite3.connect(old_db)
old_c = old_conn.cursor()
old_c.execute("SELECT value FROM ItemTable WHERE key='antigravityUnifiedStateSync.trajectorySummaries'")
row = old_c.fetchone()
if not row:
    print("  ERROR: trajectorySummaries not found in old DB!")
    old_conn.close()
    exit(1)

summaries_value = row[0]
print(f"  Found trajectorySummaries: {len(summaries_value)} bytes")

# Also grab any other antigravity-specific keys that might be needed
old_c.execute("SELECT key, value FROM ItemTable WHERE key LIKE 'antigravity%'")
ag_keys = old_c.fetchall()
print(f"  Found {len(ag_keys)} antigravity-related keys:")
for k, v in ag_keys:
    vlen = len(v) if isinstance(v, (str, bytes)) else str(v)
    print(f"    {k}: {vlen} bytes")

old_conn.close()

print("\nStep 3: Inject trajectorySummaries into new IDE state.vscdb...")
new_conn = sqlite3.connect(new_db)
new_c = new_conn.cursor()

# Insert or replace all antigravity keys
for key, value in ag_keys:
    new_c.execute("INSERT OR REPLACE INTO ItemTable (key, value) VALUES (?, ?)", (key, value))
    print(f"  Injected: {key}")

new_conn.commit()

# Verify
new_c.execute("SELECT key, length(value) FROM ItemTable WHERE key LIKE 'antigravity%'")
verify = new_c.fetchall()
print(f"\nStep 4: Verification - {len(verify)} keys in new DB:")
for k, vlen in verify:
    print(f"  {k}: {vlen} bytes")

new_conn.close()
print("\nDone! Please restart Antigravity IDE to check.")
