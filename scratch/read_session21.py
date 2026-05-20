import sqlite3
import sys

sys.stdout.reconfigure(encoding='utf-8')

conn = sqlite3.connect(r'd:\hermes-agent\memory\session_state.db')
cursor = conn.cursor()
cursor.execute('SELECT id, agent_id, session_ts, summary, decisions, next_steps, tags FROM sessions WHERE id=21')
row = cursor.fetchone()

if row:
    print(f"ID: {row[0]}")
    print(f"Agent: {row[1]}")
    print(f"Session TS: {row[2]}")
    print(f"\n=== SUMMARY ===")
    print(row[3])
    print(f"\n=== DECISIONS ===")
    print(row[4])
    print(f"\n=== NEXT STEPS ===")
    print(row[5])
    print(f"\n=== TAGS ===")
    print(row[6])
else:
    print("Session 21 not found")

conn.close()
