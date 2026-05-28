"""Final index integrity check."""
import sqlite3, os, base64, re, sys, pathlib
sys.stdout.reconfigure(encoding='utf-8')

db_path = os.path.join(os.environ['APPDATA'], 'Antigravity IDE', 'User', 'globalStorage', 'state.vscdb')
conn = sqlite3.connect(f'file:{db_path}?mode=ro', uri=True)
cursor = conn.cursor()
cursor.execute('SELECT value FROM ItemTable WHERE key = ?', ('antigravityUnifiedStateSync.trajectorySummaries',))
row = cursor.fetchone()
decoded = base64.b64decode(row[0])
text = decoded.decode('utf-8', errors='ignore')
db_uuids = set(re.findall(r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}', text))
conn.close()

conv_dir = pathlib.Path(os.environ['USERPROFILE']) / '.gemini' / 'antigravity-ide' / 'conversations'
disk_uuids = set()
for f in conv_dir.iterdir():
    if re.match(r'[0-9a-f]{8}', f.stem):
        disk_uuids.add(f.stem)

missing = disk_uuids - db_uuids
covered = len(disk_uuids) - len(missing)
pct = 100 * covered / len(disk_uuids) if disk_uuids else 0

targets = {
    '36d4ad44-13d7-4757-9b5c-cae6c7d1bd42': 'Ch2.4 writing',
    '109f4717-2847-417d-9273-38f2b51bf165': 'Ch2.4 architecture',
    '06fbd505-3856-4d0d-8897-6e9bf84a1fe9': 'Ch2.5 architecture',
    'ed95ed37-f2bf-450e-9003-e10dbb89ef8c': 'Current conversation',
    'c37f1bf8-2c7e-4adf-b19b-52d127087508': 'Previous research',
}

print('=== INDEX INTEGRITY FINAL CHECK ===')
print(f'  Index UUIDs:    {len(db_uuids)}')
print(f'  On-disk convos: {len(disk_uuids)}')
print(f'  Missing:        {len(missing)}')
print(f'  Coverage:       {covered}/{len(disk_uuids)} ({pct:.1f}%)')
print()
print('Key conversations:')
for uid, label in targets.items():
    status = 'OK' if uid in db_uuids else 'MISSING'
    print(f'  {label:25s}: {status}')
print()
if len(missing) == 0:
    print('STATUS: COMPLETE - all on-disk conversations are indexed')
else:
    print(f'STATUS: {len(missing)} gaps remain')
    for uid in sorted(missing):
        print(f'  {uid}')
