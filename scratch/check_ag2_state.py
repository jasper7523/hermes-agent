#!/usr/bin/env python3
"""Check Antigravity 2's state: conversations, index, and what's missing."""
import sqlite3, base64, os, re, sys, json
sys.stdout.reconfigure(encoding='utf-8')

AG2_GEMINI = os.path.expanduser(r"~\.gemini\antigravity")
AG2_CONVOS = os.path.join(AG2_GEMINI, "conversations")
AG2_BRAIN = os.path.join(AG2_GEMINI, "brain")
AG2_STATE = os.path.join(os.environ["APPDATA"], "Antigravity", "User", "globalStorage", "state.vscdb")
AG2_PB = os.path.join(AG2_GEMINI, "agyhub_summaries_proto.pb")

IDE_GEMINI = os.path.expanduser(r"~\.gemini\antigravity-ide")
IDE_CONVOS = os.path.join(IDE_GEMINI, "conversations")
IDE_BRAIN = os.path.join(IDE_GEMINI, "brain")

print("=" * 60)
print("  Antigravity 2 現狀診斷")
print("=" * 60)

# 1. Check if AG2 is running
import subprocess
result = subprocess.run(
    ["powershell", "-Command", "Get-Process 'Antigravity' -ErrorAction SilentlyContinue | Select-Object -First 1"],
    capture_output=True, text=True
)
is_running = "Antigravity" in result.stdout
print(f"\n[1] Antigravity 2 行程: {'執行中 ⚠️' if is_running else '未執行 ✅'}")

# 2. Conversations in AG2
print(f"\n[2] AG2 conversations/ 目錄:")
if os.path.isdir(AG2_CONVOS):
    pb_files = [f for f in os.listdir(AG2_CONVOS) if f.endswith('.pb')]
    db_files = [f for f in os.listdir(AG2_CONVOS) if f.endswith('.db')]
    print(f"  .pb 檔案: {len(pb_files)}")
    print(f"  .db 檔案: {len(db_files)}")
    for f in db_files:
        print(f"    {f}")
else:
    print("  目錄不存在!")

# 3. Conversations in IDE (the source)
print(f"\n[3] IDE conversations/ 目錄:")
if os.path.isdir(IDE_CONVOS):
    ide_pb = [f for f in os.listdir(IDE_CONVOS) if f.endswith('.pb')]
    ide_db = [f for f in os.listdir(IDE_CONVOS) if f.endswith('.db')]
    print(f"  .pb 檔案: {len(ide_pb)}")
    print(f"  .db 檔案: {len(ide_db)}")
    for f in ide_db:
        print(f"    {f}")

# 4. Check which .db files from IDE are missing in AG2
print(f"\n[4] 需要從 IDE 複製到 AG2 的 .db 檔案:")
ag2_files = set(os.listdir(AG2_CONVOS)) if os.path.isdir(AG2_CONVOS) else set()
ide_files = set(os.listdir(IDE_CONVOS)) if os.path.isdir(IDE_CONVOS) else set()
missing_in_ag2 = []
for f in ide_db:
    if f not in ag2_files:
        missing_in_ag2.append(f)
        print(f"  ❌ {f}")
    else:
        print(f"  ✅ {f} (已存在)")

# 5. Check brain dirs
print(f"\n[5] 需要從 IDE 複製到 AG2 的 brain/ 目錄:")
ag2_brains = set(os.listdir(AG2_BRAIN)) if os.path.isdir(AG2_BRAIN) else set()
for f in ide_db:
    cid = f[:-3]
    if cid not in ag2_brains:
        print(f"  ❌ brain/{cid}/")
    else:
        print(f"  ✅ brain/{cid}/ (已存在)")

# 6. AG2 state.vscdb index
print(f"\n[6] AG2 state.vscdb 索引:")
if os.path.exists(AG2_STATE):
    conn = sqlite3.connect(AG2_STATE)
    cur = conn.cursor()
    
    # trajectorySummaries
    cur.execute("SELECT value FROM ItemTable WHERE key='antigravityUnifiedStateSync.trajectorySummaries'")
    row = cur.fetchone()
    if row and row[0]:
        try:
            decoded = base64.b64decode(row[0])
            uuids = set(re.findall(rb'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}', decoded))
            print(f"  trajectorySummaries: {len(decoded)} bytes, {len(uuids)} UUIDs")
            for cid_short in ['a0af2503', 'fb9a0c95', 'aebe795c']:
                found = any(cid_short.encode() in uid for uid in uuids)
                print(f"    {cid_short}: {'✅' if found else '❌'}")
        except:
            print(f"  trajectorySummaries: {len(row[0])} chars (decode failed)")
    else:
        print(f"  trajectorySummaries: NOT FOUND")
    
    # ChatSessionStore
    cur.execute("SELECT value FROM ItemTable WHERE key='chat.ChatSessionStore.index'")
    row = cur.fetchone()
    if row:
        print(f"  ChatSessionStore.index: {repr(row[0][:100])}")
    
    conn.close()
else:
    print(f"  state.vscdb 不存在!")

# 7. AG2 agyhub_summaries_proto.pb
print(f"\n[7] AG2 agyhub_summaries_proto.pb:")
if os.path.exists(AG2_PB):
    with open(AG2_PB, 'rb') as f:
        data = f.read()
    uuids = set(re.findall(rb'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}', data))
    print(f"  大小: {len(data)} bytes, {len(uuids)} UUIDs")
    for cid_short in ['a0af2503', 'fb9a0c95', 'aebe795c']:
        found = any(cid_short.encode() in uid for uid in uuids)
        print(f"    {cid_short}: {'✅' if found else '❌'}")
else:
    print("  不存在!")
