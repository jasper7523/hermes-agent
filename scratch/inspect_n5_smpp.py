import sqlite3, sys, os
os.environ["PYTHONIOENCODING"] = "utf-8"

DB = r"D:\Agent_Hub\agents\Book_Writer_Agent\memory\session_state.db"
conn = sqlite3.connect(DB)
cur = conn.cursor()

# Session #17
cur.execute("SELECT * FROM sessions WHERE id=17")
row = cur.fetchone()
col_names = [d[0] for d in cur.description]
lines = []
for cn, val in zip(col_names, row):
    v = str(val).replace('\u26a0', '[!]')
    lines.append(f"{cn}: {v}")

# Ch2.3 related sessions
cur.execute("SELECT id, session_ts, summary FROM sessions WHERE summary LIKE '%2.3%' OR tags LIKE '%ch2.3%' ORDER BY id")
rows = cur.fetchall()
lines.append("\n=== Ch2.3 Related Sessions ===")
for r in rows:
    s = str(r[2]).replace('\u26a0', '[!]')[:150]
    lines.append(f"  Session #{r[0]} ({r[1]}): {s}...")

# All session timeline
cur.execute("SELECT id, session_ts, stepgate_count, tags FROM sessions ORDER BY id")
all_rows = cur.fetchall()
lines.append("\n=== Full Session Timeline ===")
for r in all_rows:
    lines.append(f"  #{r[0]} | {r[1]} | StepGate={r[2]} | {r[3]}")

conn.close()

out = r"d:\hermes-agent\scratch\n5_smpp_dump.txt"
with open(out, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
print(f"Written to {out}")
