#!/usr/bin/env python3
"""Dry-run: only detect missing .db conversations, don't inject."""
import sqlite3
import base64
import os
import re
import json

GEMINI_DIR = os.path.expanduser(r"~\.gemini\antigravity-ide")
CONVERSATIONS_DIR = os.path.join(GEMINI_DIR, "conversations")
BRAIN_DIR = os.path.join(GEMINI_DIR, "brain")
STATE_DB = os.path.join(os.environ["APPDATA"], "Antigravity IDE", "User", "globalStorage", "state.vscdb")

print("=" * 60)
print("  Dry-run: 偵測缺失的 .db 對話")
print("=" * 60)

# Scan .db conversations
print("\n[1] 掃描 .db 對話...")
db_conversations = {}
for fname in os.listdir(CONVERSATIONS_DIR):
    if fname.endswith(".db"):
        conv_id = fname[:-3]
        db_path = os.path.join(CONVERSATIONS_DIR, fname)
        try:
            conn = sqlite3.connect(db_path)
            cur = conn.cursor()
            cur.execute("SELECT cascade_id FROM trajectory_meta LIMIT 1")
            row = cur.fetchone()
            if row:
                db_conversations[row[0]] = db_path
            conn.close()
        except:
            pass

print(f"  .db 對話: {len(db_conversations)}")
for cid, path in db_conversations.items():
    print(f"    {cid} -> {os.path.basename(path)}")

# Read index
print("\n[2] 讀取 trajectorySummaries...")
conn = sqlite3.connect(STATE_DB)
cur = conn.cursor()
cur.execute("SELECT value FROM ItemTable WHERE key=?", ("antigravityUnifiedStateSync.trajectorySummaries",))
row = cur.fetchone()
conn.close()

decoded = base64.b64decode(row[0])

# Check each
print("\n[3] 比對結果:")
for cid in db_conversations:
    in_index = cid.encode() in decoded
    status = "✅ 已索引" if in_index else "❌ 缺失"
    
    # Get title
    title = ""
    transcript = os.path.join(BRAIN_DIR, cid, ".system_generated", "logs", "transcript.jsonl")
    if os.path.exists(transcript):
        try:
            with open(transcript, 'r', encoding='utf-8') as f:
                for line in f:
                    data = json.loads(line)
                    if data.get("type") == "USER_INPUT" and data.get("content"):
                        content = data["content"]
                        match = re.search(r'<USER_REQUEST>\s*(.*?)(?:\s*</USER_REQUEST>|\n)', content, re.DOTALL)
                        if match:
                            title = match.group(1).strip()[:60]
                            break
        except:
            pass
    
    print(f"  {status} {cid[:8]}... | {title or '(no title)'}")
