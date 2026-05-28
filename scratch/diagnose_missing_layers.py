"""Analyze the missing conversations pattern and check what index source they are in."""
import sqlite3, os, base64, re, pathlib, sys
from datetime import datetime

sys.stdout.reconfigure(encoding='utf-8')

# Get all index sources
db_path = os.path.join(os.environ['APPDATA'], 'Antigravity IDE', 'User', 'globalStorage', 'state.vscdb')
conn = sqlite3.connect(f'file:{db_path}?mode=ro', uri=True)
cursor = conn.cursor()

# L4: state.vscdb trajectorySummaries
cursor.execute('SELECT value FROM ItemTable WHERE key = ?',
               ('antigravityUnifiedStateSync.trajectorySummaries',))
row = cursor.fetchone()
decoded = base64.b64decode(row[0])
text_dec = decoded.decode('utf-8', errors='ignore')
l4_uuids = set(re.findall(r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}', text_dec))
conn.close()

# L3a: agyhub_summaries_proto.pb
pb_path = r"C:\Users\promy\.gemini\antigravity-ide\agyhub_summaries_proto.pb"
with open(pb_path, 'rb') as f:
    pb_data = f.read()
pb_text = pb_data.decode('utf-8', errors='ignore')
l3a_uuids = set(re.findall(r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}', pb_text))

# L3b: annotations
ann_dir = pathlib.Path(r"C:\Users\promy\.gemini\antigravity-ide\annotations")
l3b_uuids = set(f.stem for f in ann_dir.glob("*.pbtxt"))

# L2: conversations on disk
conv_dir = pathlib.Path(r"C:\Users\promy\.gemini\antigravity-ide\conversations")
l2_uuids = set()
for f in conv_dir.iterdir():
    base = f.stem
    if re.match(r'[0-9a-f]{8}', base):
        l2_uuids.add(base)

# The 55 missing from sidebar
missing = l2_uuids - l4_uuids

print("=" * 70)
print("MISSING CONVERSATIONS: LAYER-BY-LAYER DIAGNOSIS")
print("=" * 70)
print(f"\nTotal missing from sidebar (L4): {len(missing)}")
print()

# Categorize the missing
cat_a = []  # In L3a (PB) but not L4 (statedb) - should be recoverable
cat_b = []  # In L3b (annotations) but not L4 - should be recoverable
cat_c = []  # Only on disk (L2), not in any index - need to rebuild entry
cat_d = []  # In OLD PB but not NEW indexes

# Also check OLD PB
old_pb_path = r"C:\Users\promy\.gemini\antigravity\agyhub_summaries_proto.pb"
with open(old_pb_path, 'rb') as f:
    old_pb_data = f.read()
old_pb_text = old_pb_data.decode('utf-8', errors='ignore')
old_pb_uuids = set(re.findall(r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}', old_pb_text))

for uid in sorted(missing):
    in_pb = uid in l3a_uuids
    in_ann = uid in l3b_uuids
    in_old_pb = uid in old_pb_uuids
    
    if in_pb:
        cat_a.append(uid)
    elif in_ann:
        cat_b.append(uid)
    elif in_old_pb:
        cat_d.append(uid)
    else:
        cat_c.append(uid)

print(f"Category A: In NEW PB but not sidebar    -> {len(cat_a)} (PB index has data, vscdb doesn't)")
print(f"Category B: In annotations but not sidebar -> {len(cat_b)} (annotation metadata exists)")  
print(f"Category C: Only on disk, no index at all  -> {len(cat_c)} (need full rebuild)")
print(f"Category D: In OLD PB only                 -> {len(cat_d)} (data in old Antigravity)")

print(f"\n--- Category A (in PB, recoverable): {len(cat_a)} ---")
for uid in cat_a:
    print(f"  {uid}")

print(f"\n--- Category C (no index, need rebuild): {len(cat_c)} ---")
for uid in cat_c:
    ann_file = ann_dir / f"{uid}.pbtxt"
    title = ""
    if ann_file.exists():
        try:
            content = ann_file.read_text(encoding='utf-8', errors='ignore')
            m = re.search(r'title:"([^"]*)"', content)
            if m:
                title = m.group(1)[:60]
        except:
            pass
    t = f" | {title}" if title else ""
    print(f"  {uid}{t}")

print(f"\n--- Category D (in OLD PB only): {len(cat_d)} ---")
for uid in cat_d:
    print(f"  {uid}")

# Summary
print(f"\n{'=' * 70}")
print(f"RECOVERY STRATEGY")
print(f"{'=' * 70}")
print(f"  Category A ({len(cat_a)}): PB has summary data -> can be synced to sidebar")
print(f"  Category B ({len(cat_b)}): Annotation has metadata -> partial recovery possible")
print(f"  Category C ({len(cat_c)}): No index data -> IDE must rescan conversations/ dir")
print(f"  Category D ({len(cat_d)}): In OLD Antigravity PB -> need cross-location merge")
print(f"  Total recoverable: {len(cat_a) + len(cat_b) + len(cat_c) + len(cat_d)} of {len(missing)}")
