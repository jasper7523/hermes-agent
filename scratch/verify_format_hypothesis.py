"""Verify hypothesis: are the 55 missing conversations ALL .db format files?
If yes, the IDE only indexes .pb files and skips .db files on restart."""
import sqlite3, os, base64, re, pathlib, sys
from datetime import datetime

sys.stdout.reconfigure(encoding='utf-8')

# Get sidebar index
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

conv_dir = pathlib.Path(r"C:\Users\promy\.gemini\antigravity-ide\conversations")

# Categorize ALL conversation files
pb_only = set()   # UUID has .pb but no .db
db_only = set()   # UUID has .db but no .pb
both = set()      # UUID has both .pb and .db

all_uuids = set()
for f in conv_dir.iterdir():
    base = f.stem
    if not re.match(r'[0-9a-f]{8}', base):
        continue
    # Skip WAL/SHM files
    if f.suffix in ['.db-wal', '.db-shm']:
        continue
    all_uuids.add(base)

for uid in all_uuids:
    has_pb = (conv_dir / f"{uid}.pb").exists()
    has_db = (conv_dir / f"{uid}.db").exists()
    if has_pb and has_db:
        both.add(uid)
    elif has_pb:
        pb_only.add(uid)
    elif has_db:
        db_only.add(uid)

print("=" * 60)
print("CONVERSATION FORMAT ANALYSIS")
print("=" * 60)
print(f"  .pb only:  {len(pb_only)}")
print(f"  .db only:  {len(db_only)}")
print(f"  Both:      {len(both)}")
print(f"  Total:     {len(all_uuids)}")

# Now check: of the 106 indexed conversations, what format are they?
indexed_pb = len(l4_uuids & (pb_only | both))
indexed_db = len(l4_uuids & db_only)
print(f"\n  Indexed conversations with .pb: {indexed_pb}")
print(f"  Indexed conversations .db only: {indexed_db}")

# Of the missing ones, what format?
missing = all_uuids - l4_uuids
missing_pb = len(missing & pb_only)
missing_db = len(missing & db_only)
missing_both = len(missing & both)
print(f"\n  Missing conversations .pb only: {missing_pb}")
print(f"  Missing conversations .db only: {missing_db}")
print(f"  Missing conversations both:     {missing_both}")

print(f"\n{'=' * 60}")
if missing_db == len(missing) or (missing_db + missing_both) == len(missing):
    print("HYPOTHESIS CONFIRMED: ALL missing conversations are .db format!")
    print("The IDE only indexes .pb files on restart.")
elif missing_pb == 0:
    print("HYPOTHESIS CONFIRMED: No .pb-only files are missing!")
else:
    print(f"HYPOTHESIS PARTIALLY CONFIRMED: {missing_db} of {len(missing)} missing are .db-only")

# Show the missing .db-only files with details
print(f"\n--- Missing .db-only conversations ---")
for uid in sorted(missing & db_only):
    db_file = conv_dir / f"{uid}.db"
    mt = datetime.fromtimestamp(db_file.stat().st_mtime).strftime('%Y-%m-%d %H:%M')
    print(f"  {mt} | {uid} | {db_file.stat().st_size:>8} bytes")

print(f"\n--- Missing .pb-only conversations ---")
for uid in sorted(missing & pb_only):
    pb_file = conv_dir / f"{uid}.pb"
    mt = datetime.fromtimestamp(pb_file.stat().st_mtime).strftime('%Y-%m-%d %H:%M')
    print(f"  {mt} | {uid} | {pb_file.stat().st_size:>8} bytes")

print(f"\n--- Missing 'both' format conversations ---")
for uid in sorted(missing & both):
    print(f"  {uid}")
