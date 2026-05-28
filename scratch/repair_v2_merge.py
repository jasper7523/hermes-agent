"""
Antigravity IDE Sidebar Index MERGE Repair v2
==============================================
FIXES the v1 mistake: v1 REPLACED the index; v2 MERGES both sources.

Strategy:
  1. Read the BACKUP state.vscdb (pre_sidebar_fix) to get original 106 entries
  2. Read agyhub_summaries_proto.pb for the 55 missing entries
  3. CONCATENATE both protobuf blobs (protobuf repeated fields support concat)
  4. Base64-encode the merged blob
  5. Write merged result to current state.vscdb
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
APPDATA = Path(os.environ['APPDATA'])
GLOBALSTORE = APPDATA / 'Antigravity IDE' / 'User' / 'globalStorage'
STATE_DB = GLOBALSTORE / 'state.vscdb'
BACKUP_DB = GLOBALSTORE / 'state.vscdb.pre_sidebar_fix_20260528_144054'
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
         'Get-Process | Where-Object {$_.MainWindowTitle -like "*Antigravity*" -or $_.ProcessName -like "*Antigravity*"} | Measure-Object | Select-Object -ExpandProperty Count'],
        capture_output=True, text=True
    )
    count = int(result.stdout.strip()) if result.stdout.strip().isdigit() else 0
    return count > 0

# ============================================================
# Pre-flight
# ============================================================
print("=" * 70)
print("ANTIGRAVITY IDE SIDEBAR INDEX MERGE REPAIR v2")
print("=" * 70)

if check_ide_running():
    print("\n[ERROR] Antigravity IDE is still running!")
    print("Close it completely (Ctrl+Q), then run this script again.")
    sys.exit(1)

print("\n[OK] Antigravity IDE is not running.")

for label, path in [("state.vscdb", STATE_DB), ("backup", BACKUP_DB), ("PB index", PB_INDEX)]:
    if not path.exists():
        print(f"[ERROR] {label} not found: {path}")
        sys.exit(1)
    print(f"[OK] {label}: {path.name} ({path.stat().st_size} bytes)")

# ============================================================
# Step 1: Read ORIGINAL trajectorySummaries from BACKUP
# ============================================================
print(f"\n--- Step 1: Read ORIGINAL index from backup ---")

conn_backup = sqlite3.connect(f'file:{BACKUP_DB}?mode=ro', uri=True)
cursor = conn_backup.cursor()
cursor.execute('SELECT value FROM ItemTable WHERE key = ?', (KEY,))
row = cursor.fetchone()
conn_backup.close()

if not row:
    print("[ERROR] No trajectorySummaries found in backup!")
    sys.exit(1)

original_b64 = row[0]
original_bytes = base64.b64decode(original_b64)
original_uuids = count_uuids(original_bytes)
print(f"  Original index: {len(original_bytes)} bytes, {len(original_uuids)} UUIDs")

# ============================================================
# Step 2: Read PB index
# ============================================================
print(f"\n--- Step 2: Read PB index ---")

pb_bytes = PB_INDEX.read_bytes()
pb_uuids = count_uuids(pb_bytes)
print(f"  PB index: {len(pb_bytes)} bytes, {len(pb_uuids)} UUIDs")

# Calculate what we're adding
only_in_pb = pb_uuids - original_uuids
only_in_original = original_uuids - pb_uuids
overlap = original_uuids & pb_uuids

print(f"\n  Overlap (in both):      {len(overlap)}")
print(f"  Only in original:       {len(only_in_original)}")
print(f"  Only in PB (to add):    {len(only_in_pb)}")
print(f"  Expected total after:   {len(original_uuids | pb_uuids)}")

# ============================================================
# Step 3: Backup current (broken) state
# ============================================================
v2_backup = GLOBALSTORE / f"state.vscdb.pre_merge_v2_{timestamp}"
shutil.copy2(STATE_DB, v2_backup)
print(f"\n[BACKUP] Saved current (broken) state: {v2_backup.name}")

# ============================================================
# Step 4: MERGE by protobuf concatenation
# ============================================================
print(f"\n--- Step 4: MERGE protobuf blobs ---")

# Protobuf repeated fields: concatenation = merge
# original_bytes (from state.vscdb backup) + pb_bytes (from PB file)
merged_bytes = original_bytes + pb_bytes
merged_uuids = count_uuids(merged_bytes)
print(f"  Merged blob: {len(merged_bytes)} bytes, {len(merged_uuids)} UUIDs")

merged_b64 = base64.b64encode(merged_bytes).decode('ascii')

# ============================================================
# Step 5: Write merged result to state.vscdb
# ============================================================
print(f"\n--- Step 5: Write merged index ---")

conn = sqlite3.connect(str(STATE_DB))
cursor = conn.cursor()
cursor.execute('UPDATE ItemTable SET value = ? WHERE key = ?', (merged_b64, KEY))
if cursor.rowcount == 0:
    cursor.execute('INSERT INTO ItemTable (key, value) VALUES (?, ?)', (KEY, merged_b64))
conn.commit()
conn.close()

print(f"  [DONE] Written to state.vscdb")

# ============================================================
# Step 6: Verify
# ============================================================
print(f"\n--- VERIFICATION ---")

conn = sqlite3.connect(f'file:{STATE_DB}?mode=ro', uri=True)
cursor = conn.cursor()
cursor.execute('SELECT value FROM ItemTable WHERE key = ?', (KEY,))
row = cursor.fetchone()

if row:
    verify_bytes = base64.b64decode(row[0])
    verify_uuids = count_uuids(verify_bytes)
    print(f"  Final index: {len(verify_bytes)} bytes, {len(verify_uuids)} UUIDs")

    # Check key conversations
    targets = {
        '36d4ad44-13d7-4757-9b5c-cae6c7d1bd42': 'Ch2.4 撰寫 (三道防線)',
        '109f4717-2847-417d-9273-38f2b51bf165': 'Ch2.4 架構建立',
        'eee5e032-71af-41c9-8ca6-bf7535805caf': 'N7 Token 精簡',
        '06fbd505-3856-4d0d-8897-6e9bf84a1fe9': 'Ch2.5 架構設計',
    }
    print(f"\n  Key conversations:")
    all_ok = True
    for uid, label in targets.items():
        present = uid in verify_uuids
        was_in_original = uid in original_uuids
        marker = "✓" if present else "✗"
        source = "(was original)" if was_in_original else "(from PB)"
        print(f"    {marker} {label:30s} {source}")
        if not present:
            all_ok = False

    # Also verify some originally-visible ones are still there
    print(f"\n  Original conversations preserved: ", end="")
    preserved = len(original_uuids & verify_uuids)
    print(f"{preserved}/{len(original_uuids)}")

    if preserved == len(original_uuids) and all_ok:
        print(f"\n  ✅ ALL GOOD — originals preserved + missing recovered!")
    else:
        print(f"\n  ⚠️  Check needed — some entries may be missing")

conn.close()

print(f"\n{'=' * 70}")
print("MERGE REPAIR v2 COMPLETE")
print(f"{'=' * 70}")
print(f"\nNext steps:")
print(f"  1. Start Antigravity IDE")
print(f"  2. Check Past Conversations — BOTH old and new should appear")
print(f"  3. If wrong, restore backup:")
print(f"     copy \"{BACKUP_DB}\" \"{STATE_DB}\"")
