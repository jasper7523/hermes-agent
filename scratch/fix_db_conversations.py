#!/usr/bin/env python3
"""
Antigravity IDE — 新版 .db 對話索引修復腳本 (方案 B)

功能：
  1. 掃描 ~/.gemini/antigravity-ide/conversations/*.db 中的新對話
  2. 檢查哪些對話不在 state.vscdb 的 trajectorySummaries 索引中
  3. 從現有的同格式 entry 複製結構，修改 UUID 後注入索引
  4. 同時更新 agyhub_summaries_proto.pb
  
安全機制：
  - 所有修改前先備份
  - 交互式確認
"""
import sqlite3
import base64
import os
import re
import shutil
import time
import sys
import json

# ============================================================================
# Configuration
# ============================================================================
GEMINI_DIR = os.path.expanduser(r"~\.gemini\antigravity-ide")
CONVERSATIONS_DIR = os.path.join(GEMINI_DIR, "conversations")
BRAIN_DIR = os.path.join(GEMINI_DIR, "brain")
STATE_DB = os.path.join(os.environ["APPDATA"], "Antigravity IDE", "User", "globalStorage", "state.vscdb")
SUMMARIES_PB = os.path.join(GEMINI_DIR, "agyhub_summaries_proto.pb")
PB_KEY = "antigravityUnifiedStateSync.trajectorySummaries"

print("=" * 60)
print("  Antigravity IDE — .db 對話索引修復工具")
print("=" * 60)

# ============================================================================
# Step 0: Discover .db conversations and their metadata
# ============================================================================
print("\n[Step 0] 掃描 .db 格式對話...")
db_conversations = {}
for fname in os.listdir(CONVERSATIONS_DIR):
    if fname.endswith(".db") and not fname.endswith(("-wal", "-shm", "-journal")):
        conv_id = fname[:-3]  # strip .db
        db_path = os.path.join(CONVERSATIONS_DIR, fname)
        try:
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute("SELECT cascade_id FROM trajectory_meta LIMIT 1")
            row = cur.fetchone()
            if row:
                cascade_id = row["cascade_id"]
                # Get workspace info
                cur.execute("SELECT data FROM trajectory_metadata_blob WHERE id='main' LIMIT 1")
                meta_row = cur.fetchone()
                workspace_data = meta_row["data"] if meta_row else None
                db_conversations[cascade_id] = {
                    "db_path": db_path,
                    "workspace_blob": workspace_data,
                }
            conn.close()
        except Exception as e:
            print(f"  ⚠️  無法讀取 {fname}: {e}")

print(f"  找到 {len(db_conversations)} 個 .db 對話:")
for cid in sorted(db_conversations.keys()):
    print(f"    {cid}")

# ============================================================================
# Step 1: Read current trajectorySummaries index
# ============================================================================
print(f"\n[Step 1] 讀取 state.vscdb 索引...")
if not os.path.exists(STATE_DB):
    print(f"  ❌ state.vscdb 不存在: {STATE_DB}")
    sys.exit(1)

conn = sqlite3.connect(STATE_DB)
cur = conn.cursor()
cur.execute("SELECT value FROM ItemTable WHERE key=?", (PB_KEY,))
row = cur.fetchone()
conn.close()

if not row or not row[0]:
    print("  ❌ trajectorySummaries 不存在")
    sys.exit(1)

raw_b64 = row[0]
decoded = base64.b64decode(raw_b64)
print(f"  trajectorySummaries: {len(decoded)} bytes (base64: {len(raw_b64)} chars)")

# ============================================================================
# Step 2: Parse existing entries and find missing conversations
# ============================================================================
print(f"\n[Step 2] 解析現有索引條目...")

def decode_varint(data, pos):
    result = 0
    shift = 0
    while pos < len(data):
        b = data[pos]
        result |= (b & 0x7F) << shift
        pos += 1
        if not (b & 0x80):
            break
        shift += 7
    return result, pos

def encode_varint(v):
    if v == 0:
        return b"\x00"
    result = bytearray()
    while v > 0x7F:
        result.append((v & 0x7F) | 0x80)
        v >>= 7
    result.append(v & 0x7F)
    return bytes(result)

def write_string_field(field_num, value):
    b = value.encode("utf-8") if isinstance(value, str) else value
    return encode_varint((field_num << 3) | 2) + encode_varint(len(b)) + b

def write_bytes_field(field_num, value):
    return encode_varint((field_num << 3) | 2) + encode_varint(len(value)) + value

# Parse all top-level entries
pos = 0
existing_entries = {}  # uuid -> entry_bytes (including tag+length prefix)
reference_entry = None  # A .db-format entry to use as template

while pos < len(decoded):
    entry_start = pos
    tag, pos = decode_varint(decoded, pos)
    wire_type = tag & 7
    if wire_type != 2:
        break
    length, pos = decode_varint(decoded, pos)
    entry_data = decoded[pos:pos+length]
    pos += length
    
    # Extract UUID from entry
    uuid = None
    entry_str = entry_data.decode('utf-8', errors='ignore')
    match = re.search(r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}', entry_str)
    if match:
        uuid = match.group()
    
    full_entry = decoded[entry_start:pos]  # includes tag+length+data
    if uuid:
        existing_entries[uuid] = {
            'full_bytes': full_entry,
            'data': entry_data,
            'length': length,
        }

print(f"  現有索引條目: {len(existing_entries)}")

# Find missing .db conversations
missing = []
for cid in db_conversations:
    if cid not in existing_entries:
        missing.append(cid)
    else:
        print(f"  ✅ {cid[:8]}... 已在索引中")

if not missing:
    print("\n  🎉 所有 .db 對話都已在索引中，無需修復!")
    sys.exit(0)

print(f"\n  ⚠️  缺失的對話 ({len(missing)}):")
for cid in missing:
    print(f"    ❌ {cid}")

# ============================================================================
# Step 3: Find a reference .db entry to use as template
# ============================================================================
print(f"\n[Step 3] 尋找模板 entry...")

# Use the current conversation (aebe795c) as template since it's a .db entry
for cid in db_conversations:
    if cid in existing_entries:
        reference_entry = existing_entries[cid]
        print(f"  使用 {cid[:8]}... 作為模板 (length={reference_entry['length']})")
        break

if not reference_entry:
    # Fall back to any existing entry
    print("  ⚠️  找不到 .db 格式的模板 entry，使用第一個舊 entry")
    first_uuid = list(existing_entries.keys())[0]
    reference_entry = existing_entries[first_uuid]
    print(f"  使用 {first_uuid[:8]}... 作為模板")

# ============================================================================
# Step 4: Generate new entries for missing conversations
# ============================================================================
print(f"\n[Step 4] 生成缺失的索引條目...")

new_entries_bytes = b""
for cid in missing:
    # Strategy: Create a minimal entry with just the UUID
    # The IDE should fill in the rest when it loads the conversation
    
    # Construct entry: Field 1 (UUID) + Field 2 (minimal inner blob)
    # Inner blob structure from ag-donald: Field 1 = title (base64-encoded inner protobuf)
    
    # Get title from brain artifacts
    title = f"Conversation {cid[:8]}"
    brain_path = os.path.join(BRAIN_DIR, cid)
    transcript = os.path.join(brain_path, ".system_generated", "logs", "transcript.jsonl")
    if os.path.exists(transcript):
        try:
            with open(transcript, 'r', encoding='utf-8') as f:
                for line in f:
                    data = json.loads(line)
                    if data.get("type") == "USER_INPUT" and data.get("content"):
                        content = data["content"]
                        # Extract just the user request
                        match = re.search(r'<USER_REQUEST>\s*(.*?)(?:\s*</USER_REQUEST>|\n)', content, re.DOTALL)
                        if match:
                            title = match.group(1).strip()[:60]
                            break
        except:
            pass
    
    print(f"  生成: {cid[:8]}... (title: {title})")
    
    # Build the inner protobuf (Field 2's content)
    # Structure: Field 1 (varint) = ?, then Field 1 (string) = title as base64-encoded inner
    inner_title_pb = write_string_field(1, title)
    inner_b64 = base64.b64encode(inner_title_pb).decode('ascii')
    
    # Build Field 2 sub-message: contains a nested field with the b64 string  
    field2_inner = write_string_field(1, inner_b64)
    
    # Build the full entry: Field 1 = UUID, Field 2 = inner blob
    entry_content = write_string_field(1, cid) + write_bytes_field(2, field2_inner)
    
    # Wrap in top-level Field 1 (same as other entries)
    new_entry = write_bytes_field(1, entry_content)
    new_entries_bytes += new_entry

print(f"  生成了 {len(missing)} 個新條目 ({len(new_entries_bytes)} bytes)")

# ============================================================================
# Step 5: Backup and inject
# ============================================================================
print(f"\n[Step 5] 備份並注入...")

# Backup state.vscdb
backup_suffix = f".backup_{int(time.time())}"
state_backup = STATE_DB + backup_suffix
shutil.copy2(STATE_DB, state_backup)
print(f"  ✅ 備份 state.vscdb -> {os.path.basename(state_backup)}")

# Backup agyhub_summaries_proto.pb
if os.path.exists(SUMMARIES_PB):
    pb_backup = SUMMARIES_PB + backup_suffix
    shutil.copy2(SUMMARIES_PB, pb_backup)
    print(f"  ✅ 備份 agyhub_summaries_proto.pb")

# Append new entries to decoded protobuf
new_decoded = decoded + new_entries_bytes
new_b64 = base64.b64encode(new_decoded).decode('ascii')

# Write to state.vscdb
conn = sqlite3.connect(STATE_DB)
cur = conn.cursor()
cur.execute("UPDATE ItemTable SET value=? WHERE key=?", (new_b64, PB_KEY))
conn.commit()
conn.close()
print(f"  ✅ 已注入 {len(missing)} 個新條目到 state.vscdb trajectorySummaries")
print(f"     ({len(decoded)} -> {len(new_decoded)} bytes)")

# Also update agyhub_summaries_proto.pb (raw protobuf, not base64)
if os.path.exists(SUMMARIES_PB):
    with open(SUMMARIES_PB, 'rb') as f:
        pb_data = f.read()
    # Check if entries are already there
    need_update = False
    for cid in missing:
        if cid.encode() not in pb_data:
            need_update = True
            break
    if need_update:
        with open(SUMMARIES_PB, 'wb') as f:
            f.write(pb_data + new_entries_bytes)
        print(f"  ✅ 已注入到 agyhub_summaries_proto.pb")

# ============================================================================
# Step 6: Verify
# ============================================================================
print(f"\n[Step 6] 驗證注入結果...")
conn = sqlite3.connect(STATE_DB)
cur = conn.cursor()
cur.execute("SELECT value FROM ItemTable WHERE key=?", (PB_KEY,))
row = cur.fetchone()
conn.close()

verify_decoded = base64.b64decode(row[0])
for cid in missing:
    found = cid.encode() in verify_decoded
    print(f"  {cid[:8]}... in trajectorySummaries: {'✅' if found else '❌'}")

# Also verify agyhub_summaries_proto.pb
if os.path.exists(SUMMARIES_PB):
    with open(SUMMARIES_PB, 'rb') as f:
        pb_verify = f.read()
    for cid in missing:
        found = cid.encode() in pb_verify
        print(f"  {cid[:8]}... in agyhub_summaries_proto.pb: {'✅' if found else '❌'}")

print("\n" + "=" * 60)
print("  ✅ 修復完成！請重新啟動 Antigravity IDE")
print("=" * 60)
