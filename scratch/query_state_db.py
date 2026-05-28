"""Query state.vscdb for conversation-related keys."""
import sqlite3
import os

db_path = os.path.join(os.environ['APPDATA'], 'Antigravity IDE', 'User', 'globalStorage', 'state.vscdb')
conn = sqlite3.connect(f'file:{db_path}?mode=ro', uri=True)
cursor = conn.cursor()

# Find conversation/summary related keys
patterns = ['%summar%', '%trajectory%', '%conver%', '%history%', '%external%', '%sidebar%', '%chat%']
for pat in patterns:
    cursor.execute("SELECT key FROM ItemTable WHERE key LIKE ? LIMIT 10", (pat,))
    rows = cursor.fetchall()
    if rows:
        print(f"\n=== Pattern: {pat} ===")
        for row in rows:
            val = cursor.execute("SELECT length(value) FROM ItemTable WHERE key = ?", (row[0],)).fetchone()
            print(f"  {row[0]} (value length: {val[0]})")

# Also check all keys to find the relevant ones
print("\n=== ALL KEYS (first 50) ===")
cursor.execute("SELECT key, length(value) FROM ItemTable ORDER BY key LIMIT 50")
for row in cursor.fetchall():
    print(f"  {row[0]} ({row[1]} bytes)")

conn.close()
