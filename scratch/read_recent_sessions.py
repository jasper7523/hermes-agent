import sqlite3
import sys

sys.stdout.reconfigure(encoding='utf-8')

conn = sqlite3.connect(r'd:\hermes-agent\memory\session_state.db')
cursor = conn.cursor()
cursor.execute('SELECT id, agent_id, session_ts, summary, tags FROM sessions ORDER BY id DESC LIMIT 5')
rows = cursor.fetchall()

for row in rows:
    print(f"--- Session #{row[0]} | Agent: {row[1]} | TS: {row[2]} ---")
    print(f"Summary: {row[3]}")
    print(f"Tags: {row[4]}")
    print()

conn.close()
