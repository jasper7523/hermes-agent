"""Search for 5/19 era conversations - Ch2.4 architecture setup."""
import pathlib, re, sys, os
from datetime import datetime

sys.stdout.reconfigure(encoding='utf-8')

# Check backup from 2.0 migration
backup_dir = pathlib.Path(r'C:\Users\promy\.gemini\antigravity-ide\backup_20260520')
if backup_dir.exists():
    print('=== BACKUP DIR (from 2.0 migration date) ===')
    for f in backup_dir.iterdir():
        print(f'  {f.name} ({f.stat().st_size} bytes)')

# Search OLD annotations for Ch2.4 architecture titles
old_ann = pathlib.Path(r'C:\Users\promy\.gemini\antigravity\annotations')
new_ann = pathlib.Path(r'C:\Users\promy\.gemini\antigravity-ide\annotations')

print('\n=== ANNOTATIONS MENTIONING Ch2.4 OR ARCHITECTURE ===')
for loc, adir in [('NEW', new_ann), ('OLD', old_ann)]:
    if not adir.exists():
        continue
    for f in sorted(adir.glob('*.pbtxt')):
        try:
            content = f.read_text(encoding='utf-8', errors='ignore')
            if re.search(r'2\.4|架構|三道防線|Three Lines|chapter_init', content, re.IGNORECASE):
                mt = datetime.fromtimestamp(f.stat().st_mtime).strftime('%m-%d %H:%M')
                # Clean up title
                m = re.search(r'title:"([^"]*)"', content)
                title = m.group(1)[:80] if m else "(no title)"
                print(f'  [{loc}] {mt} | {f.stem} | {title}')
        except:
            pass

# Search ALL brain dirs for Ch2.4 architecture specifically, focusing on 5/18-5/20
print('\n=== BRAIN DIRS FROM 5/18-5/20 CONTAINING Ch2.4/ARCHITECTURE ===')
locations = [
    ('NEW', pathlib.Path(r'C:\Users\promy\.gemini\antigravity-ide\brain')),
    ('OLD', pathlib.Path(r'C:\Users\promy\.gemini\antigravity\brain')),
]

for loc, bdir in locations:
    for d in sorted(bdir.iterdir()):
        if not d.is_dir() or not re.match(r'[0-9a-f]{8}', d.name):
            continue
        mt = datetime.fromtimestamp(d.stat().st_mtime)
        # Only look at 5/18-5/20 timeframe
        if not (mt.month == 5 and 18 <= mt.day <= 20):
            continue
        
        transcript = d / ".system_generated" / "logs" / "transcript.jsonl"
        if transcript.exists():
            try:
                content = transcript.read_text(encoding='utf-8', errors='ignore')[:5000]
                if re.search(r'2\.4|架構|三道防線|chapter_init|Three Lines', content):
                    # Get first user message
                    first_msg = ""
                    for line in content.split('\n')[:20]:
                        if 'USER_INPUT' in line:
                            m2 = re.search(r'"content"\s*:\s*"(.{0,150})', line)
                            if m2:
                                first_msg = re.sub(r'\\[rn]', ' ', m2.group(1))[:100]
                            break
                    print(f'  [{loc}] {mt.strftime("%m-%d %H:%M")} | {d.name} | {first_msg}')
            except:
                pass

# Also check if there are brain dirs from 5/19 with NO transcript
print('\n=== ALL BRAIN DIRS FROM 5/18-5/19 ===')
for loc, bdir in locations:
    for d in sorted(bdir.iterdir()):
        if not d.is_dir() or not re.match(r'[0-9a-f]{8}', d.name):
            continue
        ct = datetime.fromtimestamp(d.stat().st_ctime)
        mt = datetime.fromtimestamp(d.stat().st_mtime)
        if mt.month == 5 and mt.day in [18, 19]:
            has_transcript = (d / ".system_generated" / "logs" / "transcript.jsonl").exists()
            print(f'  [{loc}] {d.name} | created: {ct.strftime("%m-%d %H:%M")} | modified: {mt.strftime("%m-%d %H:%M")} | transcript: {has_transcript}')

# Check if PB backup from migration date has different content
print('\n=== PB BACKUP FILES SIZE COMPARISON ===')
pb_files = [
    r"C:\Users\promy\.gemini\antigravity-ide\agyhub_summaries_proto.pb",
    r"C:\Users\promy\.gemini\antigravity-ide\agyhub_summaries_proto.pb.pre_dbfix_1779292550",
    r"C:\Users\promy\.gemini\antigravity-ide\backup_20260520\agyhub_summaries_proto.pb",
    r"C:\Users\promy\.gemini\antigravity\agyhub_summaries_proto.pb",
    r"C:\Users\promy\.gemini\antigravity\agyhub_summaries_proto.pb.pre_dbfix_1779291824",
]
for p in pb_files:
    pp = pathlib.Path(p)
    if pp.exists():
        mt = datetime.fromtimestamp(pp.stat().st_mtime).strftime('%m-%d %H:%M')
        # Count UUIDs inside
        data = pp.read_bytes().decode('utf-8', errors='ignore')
        uuids = set(re.findall(r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}', data))
        print(f'  {pp.name:50s} | {pp.stat().st_size:>7} bytes | {mt} | {len(uuids)} UUIDs')
    else:
        print(f'  {pp.name:50s} | NOT FOUND')
