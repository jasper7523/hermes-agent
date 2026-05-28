"""
Antigravity IDE Sidebar Index Repair Script
============================================
Repairs the sidebar conversation index by injecting the complete
agyhub_summaries_proto.pb into state.vscdb's trajectorySummaries key.

Safety: Creates timestamped backup before any modification.
"""
import sqlite3
import os
import sys
import base64
import re
import shutil
from datetime import datetime
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

# ============================================================
# Configuration
# ============================================================
STATE_DB = Path(os.environ['APPDATA']) / 'Antigravity IDE' / 'User' / 'globalStorage' / 'state.vscdb'
PB_INDEX = Path(os.environ['USERPROFILE']) / '.gemini' / 'antigravity-ide' / 'agyhub_summaries_proto.pb'
KEY = 'antigravityUnifiedStateSync.trajectorySummaries'

timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

def count_uuids(data_bytes):
    """Count unique conversation UUIDs in binary data."""
    text = data_bytes.decode('utf-8', errors='ignore')
    return set(re.findall(
        r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}', text))

def check_ide_running():
    """Check if Antigravity IDE is running."""
    import subprocess
    result = subprocess.run(
        ['powershell', '-Command',
         'Get-Process -Name "Antigravity IDE" -ErrorAction SilentlyContinue | Measure-Object | Select-Object -ExpandProperty Count'],
        capture_output=True, text=True
    )
    count = int(result.stdout.strip()) if result.stdout.strip().isdigit() else 0
    return count > 0

# ============================================================
# Pre-flight checks
# ============================================================
print("=" * 60)
print("ANTIGRAVITY IDE SIDEBAR INDEX REPAIR")
print("=" * 60)

# Check IDE is not running
if check_ide_running():
    print("\n[ERROR] Antigravity IDE is still running!")
    print("Please close it completely (Ctrl+Q) before running this script.")
    print("Then run this script again.")
    sys.exit(1)

print("\n[OK] Antigravity IDE is not running.")

# Verify files exist
if not STATE_DB.exists():
    print(f"\n[ERROR] state.vscdb not found: {STATE_DB}")
    sys.exit(1)
if not PB_INDEX.exists():
    print(f"\n[ERROR] PB index not found: {PB_INDEX}")
    sys.exit(1)

print(f"[OK] state.vscdb found: {STATE_DB}")
print(f"[OK] PB index found: {PB_INDEX}")

# ============================================================
# Step 1: Read current state (BEFORE)
# ============================================================
print(f"\n--- BEFORE REPAIR ---")

conn = sqlite3.connect(str(STATE_DB))
cursor = conn.cursor()
cursor.execute('SELECT value FROM ItemTable WHERE key = ?', (KEY,))
row = cursor.fetchone()

if row:
    old_value = row[0]
    old_decoded = base64.b64decode(old_value)
    old_uuids = count_uuids(old_decoded)
    print(f"  Current trajectorySummaries: {len(old_value)} chars (Base64)")
    print(f"  Decoded size: {len(old_decoded)} bytes")
    print(f"  Conversation UUIDs: {len(old_uuids)}")
else:
    old_uuids = set()
    print("  trajectorySummaries key NOT FOUND (will be created)")

conn.close()

# Read PB index
pb_bytes = PB_INDEX.read_bytes()
pb_uuids = count_uuids(pb_bytes)
print(f"\n  PB index file size: {len(pb_bytes)} bytes")
print(f"  PB conversation UUIDs: {len(pb_uuids)}")

new_entries = pb_uuids - old_uuids
print(f"\n  New entries to add: {len(new_entries)}")
print(f"  Entries that will be recovered: {len(new_entries)}")

# ============================================================
# Step 2: Backup
# ============================================================
backup_path = STATE_DB.parent / f"state.vscdb.pre_sidebar_fix_{timestamp}"
shutil.copy2(STATE_DB, backup_path)
print(f"\n[BACKUP] Created: {backup_path.name}")

# ============================================================
# Step 3: Write PB index as Base64 into state.vscdb
# ============================================================
print(f"\n--- REPAIRING ---")

# Base64 encode the PB file
new_value = base64.b64encode(pb_bytes).decode('ascii')
print(f"  New Base64 value: {len(new_value)} chars")

# Write to database
conn = sqlite3.connect(str(STATE_DB))
cursor = conn.cursor()

if row:
    cursor.execute('UPDATE ItemTable SET value = ? WHERE key = ?', (new_value, KEY))
else:
    cursor.execute('INSERT INTO ItemTable (key, value) VALUES (?, ?)', (KEY, new_value))

conn.commit()
conn.close()

print(f"  [DONE] Written to state.vscdb")

# ============================================================
# Step 4: Verify
# ============================================================
print(f"\n--- AFTER REPAIR ---")

conn = sqlite3.connect(f'file:{STATE_DB}?mode=ro', uri=True)
cursor = conn.cursor()
cursor.execute('SELECT value FROM ItemTable WHERE key = ?', (KEY,))
row = cursor.fetchone()

if row:
    new_decoded = base64.b64decode(row[0])
    new_uuids = count_uuids(new_decoded)
    print(f"  trajectorySummaries: {len(row[0])} chars (Base64)")
    print(f"  Decoded size: {len(new_decoded)} bytes")
    print(f"  Conversation UUIDs: {len(new_uuids)}")
    
    # Check key conversations
    targets = {
        '36d4ad44-13d7-4757-9b5c-cae6c7d1bd42': 'Ch2.4 writing',
        '109f4717-2847-417d-9273-38f2b51bf165': 'Ch2.4 architecture',
        'eee5e032-71af-41c9-8ca6-bf7535805caf': 'N7 Token',
        '06fbd505-3856-4d0d-8897-6e9bf84a1fe9': 'Ch2.5 architecture',
    }
    print(f"\n  Key conversation recovery check:")
    for uid, label in targets.items():
        before = uid in old_uuids
        after = uid in new_uuids
        status = "RECOVERED" if (not before and after) else ("already OK" if before else "STILL MISSING")
        print(f"    {label:25s} : {status}")

conn.close()

print(f"\n{'=' * 60}")
print("REPAIR COMPLETE")
print(f"{'=' * 60}")
print(f"\nNext steps:")
print(f"  1. Start Antigravity IDE")
print(f"  2. Check Past Conversations sidebar")
print(f"  3. If something goes wrong, restore backup:")
print(f"     copy \"{backup_path}\" \"{STATE_DB}\"")
