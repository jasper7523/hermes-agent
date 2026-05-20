import sqlite3
import os

def inspect_db(path, label):
    print(f"\n{'='*60}")
    print(f"=== {label} ===")
    print(f"Path: {path}")
    print(f"Size: {os.path.getsize(path)} bytes")
    print(f"{'='*60}")
    
    db = sqlite3.connect(path)
    c = db.cursor()
    
    # List tables
    c.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = c.fetchall()
    print(f"\nTables ({len(tables)}):")
    for t in tables:
        tname = t[0]
        c.execute(f"SELECT count(*) FROM [{tname}]")
        count = c.fetchone()[0]
        print(f"  {tname}: {count} rows")
    
    # Search for chat/conversation related keys
    print("\n--- Searching for chat/conversation keys in ItemTable ---")
    try:
        c.execute("SELECT key FROM ItemTable WHERE key LIKE '%chat%' OR key LIKE '%convo%' OR key LIKE '%conversation%' OR key LIKE '%session%' OR key LIKE '%summary%' OR key LIKE '%trajectory%'")
        keys = c.fetchall()
        for k in keys:
            c.execute("SELECT length(value) FROM ItemTable WHERE key=?", (k[0],))
            vlen = c.fetchone()[0]
            print(f"  {k[0]}: value_length={vlen}")
    except Exception as e:
        print(f"  Error: {e}")
    
    db.close()

# Inspect both
old_path = r"C:\Users\promy\AppData\Roaming\Antigravity\User\globalStorage\state.vscdb"
new_path = r"C:\Users\promy\AppData\Roaming\Antigravity IDE\User\globalStorage\state.vscdb"

inspect_db(old_path, "Old Antigravity (standalone)")
inspect_db(new_path, "New Antigravity IDE")
