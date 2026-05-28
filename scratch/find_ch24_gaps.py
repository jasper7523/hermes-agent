"""Find Ch2.4 conversations and all missing conversations - cp950 safe."""
import sqlite3, os, base64, re, pathlib, sys
from datetime import datetime

# Force UTF-8 output
sys.stdout.reconfigure(encoding='utf-8')

# ---- 1. Get current index UUIDs from state.vscdb ----
db_path = os.path.join(os.environ['APPDATA'], 'Antigravity IDE', 'User', 'globalStorage', 'state.vscdb')
conn = sqlite3.connect(f'file:{db_path}?mode=ro', uri=True)
cursor = conn.cursor()
cursor.execute('SELECT value FROM ItemTable WHERE key = ?',
               ('antigravityUnifiedStateSync.trajectorySummaries',))
row = cursor.fetchone()
decoded = base64.b64decode(row[0])
text_decoded = decoded.decode('utf-8', errors='ignore')
db_uuids = set(re.findall(
    r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}', text_decoded))
conn.close()

# ---- 2. Scan ALL brain dirs (both locations) for Ch2.4 ----
print("=" * 70)
print("SEARCHING FOR Ch2.4 RELATED CONVERSATIONS")
print("=" * 70)

locations = {
    "NEW": r"C:\Users\promy\.gemini\antigravity-ide\brain",
    "OLD": r"C:\Users\promy\.gemini\antigravity\brain",
}

ch24_convos = []
seen_uuids = set()

for loc_name, brain_dir in locations.items():
    brain_path = pathlib.Path(brain_dir)
    if not brain_path.exists():
        continue
    for d in brain_path.iterdir():
        if not d.is_dir() or not re.match(r'[0-9a-f]{8}', d.name):
            continue
        if d.name in seen_uuids:
            continue
        transcript = d / ".system_generated" / "logs" / "transcript.jsonl"
        if transcript.exists():
            try:
                content = transcript.read_text(encoding='utf-8', errors='ignore')
                if re.search(r'[Cc]h\.?\s*2[\.\s]*4|[Cc]hapter\s*2\.4', content):
                    mtime = datetime.fromtimestamp(d.stat().st_mtime).strftime('%Y-%m-%d %H:%M')
                    in_index = d.name in db_uuids
                    seen_uuids.add(d.name)
                    ch24_convos.append({
                        'uuid': d.name,
                        'location': loc_name,
                        'mtime': mtime,
                        'in_index': in_index,
                    })
            except:
                pass

ch24_convos.sort(key=lambda x: x['mtime'], reverse=True)

missing_ch24 = [c for c in ch24_convos if not c['in_index']]
found_ch24 = [c for c in ch24_convos if c['in_index']]

print(f"\nTotal Ch2.4-related conversations found: {len(ch24_convos)}")
print(f"  In sidebar index:  {len(found_ch24)}")
print(f"  MISSING from index: {len(missing_ch24)}")

if missing_ch24:
    print(f"\n--- MISSING Ch2.4 conversations ---")
    for c in missing_ch24:
        print(f"  [{c['location']}] {c['mtime']} | {c['uuid']}")

# ---- 3. Show ALL missing from index ----
print("\n" + "=" * 70)
print("ALL CONVERSATIONS ON DISK BUT MISSING FROM SIDEBAR INDEX")
print("=" * 70)

new_brain = pathlib.Path(r"C:\Users\promy\.gemini\antigravity-ide\brain")
conv_dir = pathlib.Path(r"C:\Users\promy\.gemini\antigravity-ide\conversations")
ann_dir = pathlib.Path(r"C:\Users\promy\.gemini\antigravity-ide\annotations")

disk_uuids = set()
for d in new_brain.iterdir():
    if d.is_dir() and re.match(r'[0-9a-f]{8}', d.name):
        disk_uuids.add(d.name)
for f in conv_dir.iterdir():
    base = f.stem
    if re.match(r'[0-9a-f]{8}', base):
        disk_uuids.add(base)

missing = disk_uuids - db_uuids
in_both = disk_uuids & db_uuids
only_index = db_uuids - disk_uuids

print(f"\n  On disk (brain+conv): {len(disk_uuids)}")
print(f"  In sidebar index:    {len(db_uuids)}")
print(f"  In both:             {len(in_both)}")
print(f"  On disk but MISSING: {len(missing)}")
print(f"  In index but no disk: {len(only_index)}")

# Show missing with dates
missing_list = []
for uid in missing:
    brain_d = new_brain / uid
    if brain_d.exists():
        mtime = datetime.fromtimestamp(brain_d.stat().st_mtime).strftime('%Y-%m-%d %H:%M')
    else:
        # Check conversation file
        for ext in ['.pb', '.db']:
            cf = conv_dir / f"{uid}{ext}"
            if cf.exists():
                mtime = datetime.fromtimestamp(cf.stat().st_mtime).strftime('%Y-%m-%d %H:%M')
                break
        else:
            mtime = "unknown"
    
    # Check annotation for title
    title = ""
    ann_file = ann_dir / f"{uid}.pbtxt"
    if ann_file.exists():
        try:
            content = ann_file.read_text(encoding='utf-8', errors='ignore')
            m = re.search(r'title:"([^"]*)"', content)
            if m:
                raw = m.group(1)
                # Clean non-printable
                title = re.sub(r'[^\x20-\x7E\u4e00-\u9fff\u3000-\u303f]', '?', raw)[:80]
        except:
            pass
    
    missing_list.append((mtime, uid, title))

missing_list.sort(reverse=True)
print(f"\n--- Missing conversations (sorted by date desc) ---")
for mtime, uid, title in missing_list:
    t = f" | {title}" if title else ""
    print(f"  {mtime} | {uid}{t}")

# ---- 4. Check OLD brain for conversations NOT in NEW ----
print("\n" + "=" * 70)
print("CONVERSATIONS IN OLD BUT NOT IN NEW BRAIN")
print("=" * 70)
old_brain = pathlib.Path(r"C:\Users\promy\.gemini\antigravity\brain")
old_uuids = set()
for d in old_brain.iterdir():
    if d.is_dir() and re.match(r'[0-9a-f]{8}', d.name):
        old_uuids.add(d.name)

new_brain_uuids = set()
for d in new_brain.iterdir():
    if d.is_dir() and re.match(r'[0-9a-f]{8}', d.name):
        new_brain_uuids.add(d.name)

old_only = old_uuids - new_brain_uuids
print(f"\n  OLD brain dirs: {len(old_uuids)}")
print(f"  NEW brain dirs: {len(new_brain_uuids)}")
print(f"  In OLD only (not in NEW): {len(old_only)}")

if old_only:
    print(f"\n--- OLD-only brain dirs ---")
    for uid in sorted(old_only):
        d = old_brain / uid
        mtime = datetime.fromtimestamp(d.stat().st_mtime).strftime('%Y-%m-%d %H:%M')
        in_idx = uid in db_uuids
        print(f"  {mtime} | {uid} | idx:{in_idx}")
