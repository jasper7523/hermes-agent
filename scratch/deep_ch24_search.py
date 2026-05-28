"""Deep search for Ch2.4 writing & architecture conversations across ALL locations."""
import sqlite3, os, base64, re, pathlib, sys, json
from datetime import datetime

sys.stdout.reconfigure(encoding='utf-8')

# Get current sidebar index
db_path = os.path.join(os.environ['APPDATA'], 'Antigravity IDE', 'User', 'globalStorage', 'state.vscdb')
conn = sqlite3.connect(f'file:{db_path}?mode=ro', uri=True)
cursor = conn.cursor()
cursor.execute('SELECT value FROM ItemTable WHERE key = ?',
               ('antigravityUnifiedStateSync.trajectorySummaries',))
row = cursor.fetchone()
decoded = base64.b64decode(row[0])
text_dec = decoded.decode('utf-8', errors='ignore')
l4_uuids = set(re.findall(r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}', text_dec))
conn.close()

# PB indexes
def get_pb_uuids(path):
    with open(path, 'rb') as f:
        data = f.read()
    text = data.decode('utf-8', errors='ignore')
    return set(re.findall(r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}', text))

new_pb = get_pb_uuids(r"C:\Users\promy\.gemini\antigravity-ide\agyhub_summaries_proto.pb")
old_pb = get_pb_uuids(r"C:\Users\promy\.gemini\antigravity\agyhub_summaries_proto.pb")

# Annotations
ann_dir = pathlib.Path(r"C:\Users\promy\.gemini\antigravity-ide\annotations")
old_ann_dir = pathlib.Path(r"C:\Users\promy\.gemini\antigravity\annotations")

print("=" * 80)
print("DEEP SEARCH: Ch2.4 WRITING & ARCHITECTURE CONVERSATIONS")
print("=" * 80)

# Search ALL brain dirs (both locations) for Ch2.4 specific patterns
patterns = [
    (r'[Cc]h\s*2\.4', 'Ch2.4 general'),
    (r'撰寫.*2\.4|2\.4.*撰寫|寫.*[Cc]h\s*2\.4', 'Ch2.4 writing'),
    (r'架構.*2\.4|2\.4.*架構|設計.*2\.4', 'Ch2.4 architecture'),
    (r'三道防線|Three Lines|three lines', 'Three Lines Model'),
    (r'2\.4.*文獻|文獻.*2\.4', 'Ch2.4 literature'),
]

locations = [
    ("NEW", pathlib.Path(r"C:\Users\promy\.gemini\antigravity-ide\brain")),
    ("OLD", pathlib.Path(r"C:\Users\promy\.gemini\antigravity\brain")),
]

# Also check OLD conversations directory
old_conv_dir = pathlib.Path(r"C:\Users\promy\.gemini\antigravity\conversations")
new_conv_dir = pathlib.Path(r"C:\Users\promy\.gemini\antigravity-ide\conversations")

results = {}  # uuid -> info

for loc_name, brain_path in locations:
    if not brain_path.exists():
        continue
    for d in brain_path.iterdir():
        if not d.is_dir() or not re.match(r'[0-9a-f]{8}', d.name):
            continue
        
        uid = d.name
        if uid in results:
            continue
        
        transcript = d / ".system_generated" / "logs" / "transcript.jsonl"
        if not transcript.exists():
            continue
        
        try:
            content = transcript.read_text(encoding='utf-8', errors='ignore')
        except:
            continue
        
        matched_patterns = []
        for pat, label in patterns:
            if re.search(pat, content):
                matched_patterns.append(label)
        
        if not matched_patterns:
            continue
        
        # Get creation time from transcript
        create_time = "unknown"
        first_user_msg = ""
        try:
            for line in content.split('\n')[:50]:
                if not line.strip():
                    continue
                obj = json.loads(line)
                if 'content' in obj and obj.get('type') == 'USER_INPUT':
                    raw = obj.get('content', '')[:150]
                    first_user_msg = re.sub(r'<[^>]+>', '', raw)[:120]
                    break
                # Try to get timestamp
                if 'timestamp' in str(obj):
                    pass
        except:
            pass
        
        mtime = datetime.fromtimestamp(d.stat().st_mtime).strftime('%Y-%m-%d %H:%M')
        
        # Check creation time from the transcript file creation
        try:
            ctime = datetime.fromtimestamp(transcript.stat().st_ctime).strftime('%Y-%m-%d %H:%M')
        except:
            ctime = "unknown"
        
        in_sidebar = uid in l4_uuids
        in_new_pb = uid in new_pb
        in_old_pb = uid in old_pb
        
        # Check annotations
        has_ann = (ann_dir / f"{uid}.pbtxt").exists()
        has_old_ann = (old_ann_dir / f"{uid}.pbtxt").exists() if old_ann_dir.exists() else False
        
        # Check conversation files
        has_new_conv = any((new_conv_dir / f"{uid}{ext}").exists() for ext in ['.pb', '.db'])
        has_old_conv = any((old_conv_dir / f"{uid}{ext}").exists() for ext in ['.pb', '.db'])
        
        ann_title = ""
        for ad in [ann_dir, old_ann_dir]:
            af = ad / f"{uid}.pbtxt"
            if af.exists():
                try:
                    ac = af.read_text(encoding='utf-8', errors='ignore')
                    m = re.search(r'title:"([^"]*)"', ac)
                    if m:
                        ann_title = m.group(1)[:80]
                except:
                    pass
                break
        
        results[uid] = {
            'location': loc_name,
            'mtime': mtime,
            'ctime': ctime,
            'patterns': matched_patterns,
            'in_sidebar': in_sidebar,
            'in_new_pb': in_new_pb,
            'in_old_pb': in_old_pb,
            'has_ann': has_ann,
            'has_old_ann': has_old_ann,
            'has_new_conv': has_new_conv,
            'has_old_conv': has_old_conv,
            'ann_title': ann_title,
            'first_msg': first_user_msg,
        }

# Sort by mtime
sorted_results = sorted(results.items(), key=lambda x: x[1]['mtime'], reverse=True)

# Filter to show ones matching writing/architecture patterns or in the 5/19-5/24 window
print(f"\nTotal Ch2.4-related conversations: {len(results)}")

# Show ALL with full diagnostic info
for uid, info in sorted_results:
    sidebar_status = "VISIBLE" if info['in_sidebar'] else "!! MISSING"
    title_display = info['ann_title'] or info['first_msg'][:60] or "(no title)"
    
    print(f"\n  [{info['location']}] {info['mtime']} (created: {info['ctime']}) | {sidebar_status}")
    print(f"  UUID: {uid}")
    print(f"  Title: {title_display}")
    print(f"  Patterns: {', '.join(info['patterns'])}")
    print(f"  Indexes: sidebar={info['in_sidebar']} new_pb={info['in_new_pb']} old_pb={info['in_old_pb']}")
    print(f"  Files:   new_ann={info['has_ann']} old_ann={info['has_old_ann']} new_conv={info['has_new_conv']} old_conv={info['has_old_conv']}")

# Focused summary on missing ones
print(f"\n{'=' * 80}")
print("MISSING CH2.4 CONVERSATIONS SUMMARY")
print(f"{'=' * 80}")
missing_ch24 = [(uid, info) for uid, info in sorted_results if not info['in_sidebar']]
print(f"\n  Missing from sidebar: {len(missing_ch24)}")
for uid, info in missing_ch24:
    title = info['ann_title'] or info['first_msg'][:80] or "(no title)"
    recovery = []
    if info['in_new_pb']: recovery.append("new_pb")
    if info['in_old_pb']: recovery.append("old_pb")
    if info['has_new_conv']: recovery.append("new_conv")
    if info['has_old_conv']: recovery.append("old_conv")
    print(f"  {info['mtime']} | {uid[:20]}...")
    print(f"    Title: {title}")
    print(f"    Recovery sources: {', '.join(recovery) if recovery else 'NONE'}")
