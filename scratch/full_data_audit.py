"""Deep analysis: compare which conversations are in the state.vscdb trajectorySummaries
vs which exist on disk, to identify the exact gap."""
import sqlite3
import os
import base64
import re

# ---- 1. Get all UUIDs from state.vscdb trajectorySummaries ----
db_path = os.path.join(os.environ['APPDATA'], 'Antigravity IDE', 'User', 'globalStorage', 'state.vscdb')
conn = sqlite3.connect(f'file:{db_path}?mode=ro', uri=True)
cursor = conn.cursor()
cursor.execute("SELECT value FROM ItemTable WHERE key = 'antigravityUnifiedStateSync.trajectorySummaries'")
row = cursor.fetchone()
decoded = base64.b64decode(row[0])
text = decoded.decode('utf-8', errors='ignore')
db_uuids = set(re.findall(r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}', text))
conn.close()

# ---- 2. Get all UUIDs from agyhub_summaries_proto.pb ----
pb_path = r"C:\Users\promy\.gemini\antigravity-ide\agyhub_summaries_proto.pb"
with open(pb_path, 'rb') as f:
    pb_data = f.read()
pb_text = pb_data.decode('utf-8', errors='ignore')
pb_uuids = set(re.findall(r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}', pb_text))

# ---- 3. Get all brain directories ----
brain_dir = r"C:\Users\promy\.gemini\antigravity-ide\brain"
brain_uuids = set()
for name in os.listdir(brain_dir):
    if re.match(r'[0-9a-f]{8}-[0-9a-f]{4}', name):
        brain_uuids.add(name)

# ---- 4. Get all conversation files ----
conv_dir = r"C:\Users\promy\.gemini\antigravity-ide\conversations"
conv_uuids = set()
for name in os.listdir(conv_dir):
    base = os.path.splitext(name)[0]
    if re.match(r'[0-9a-f]{8}-[0-9a-f]{4}', base):
        conv_uuids.add(base)

# ---- 5. Get all annotation files ----
ann_dir = r"C:\Users\promy\.gemini\antigravity-ide\annotations"
ann_uuids = set()
for name in os.listdir(ann_dir):
    base = os.path.splitext(name)[0]
    if re.match(r'[0-9a-f]{8}-[0-9a-f]{4}', base):
        ann_uuids.add(base)

# ---- Report ----
print("=" * 60)
print("ANTIGRAVITY IDE DATA STORES INVENTORY")
print("=" * 60)
print(f"  state.vscdb trajectorySummaries UUIDs: {len(db_uuids)}")
print(f"  agyhub_summaries_proto.pb UUIDs:       {len(pb_uuids)}")
print(f"  brain/ directories:                    {len(brain_uuids)}")
print(f"  conversations/ files:                  {len(conv_uuids)}")
print(f"  annotations/ files:                    {len(ann_uuids)}")

# Cross-reference
all_known = brain_uuids | conv_uuids | ann_uuids | db_uuids | pb_uuids
print(f"\n  Total unique conversations (union):     {len(all_known)}")

# Find conversations missing from the sidebar index (db_uuids = sidebar source)
on_disk_but_not_in_db = (brain_uuids | conv_uuids) - db_uuids
print(f"\n  On disk but NOT in sidebar index:       {len(on_disk_but_not_in_db)}")

# Check which recent ones are missing
print("\n--- Recent conversations (brain dirs sorted by mtime, last 15) ---")
import pathlib
brain_path = pathlib.Path(brain_dir)
recent = sorted(
    [d for d in brain_path.iterdir() if d.is_dir() and re.match(r'[0-9a-f]{8}', d.name)],
    key=lambda d: d.stat().st_mtime,
    reverse=True
)[:15]

for d in recent:
    uid = d.name
    in_db = uid in db_uuids
    in_pb = uid in pb_uuids
    in_ann = uid in ann_uuids
    in_conv = uid in conv_uuids
    from datetime import datetime
    mtime = datetime.fromtimestamp(d.stat().st_mtime).strftime('%Y-%m-%d %H:%M')
    status = "OK VISIBLE" if in_db else "!! INVISIBLE"
    print(f"  {mtime} | {uid[:20]}... | DB:{in_db} PB:{in_pb} Ann:{in_ann} Conv:{in_conv} | {status}")

print("\n--- Summary of invisible conversations ---")
invisible = [(d.name, d.stat().st_mtime) for d in recent if d.name not in db_uuids]
print(f"  {len(invisible)} of last 15 conversations are INVISIBLE in sidebar")
