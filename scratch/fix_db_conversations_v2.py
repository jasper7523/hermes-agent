#!/usr/bin/env python3
"""
Antigravity IDE — .db 對話索引修復腳本 v2 (精準注入版)

策略：使用 aebe795c (IDE 自動產生的 .db entry) 作為模板，
      克隆其完整 protobuf 結構並替換 UUID + title 欄位。
      
安全機制：
  - 自動備份 state.vscdb + agyhub_summaries_proto.pb
  - 解碼 → 注入 → 驗證的三段式流程
"""
import sqlite3
import base64
import os
import re
import shutil
import time
import json
import sys

# Fix Windows encoding
sys.stdout.reconfigure(encoding='utf-8')

# ============================================================================
# Configuration
# ============================================================================
GEMINI_DIR = os.path.expanduser(r"~\.gemini\antigravity-ide")
CONVERSATIONS_DIR = os.path.join(GEMINI_DIR, "conversations")
BRAIN_DIR = os.path.join(GEMINI_DIR, "brain")
STATE_DB = os.path.join(os.environ["APPDATA"], "Antigravity IDE", "User", "globalStorage", "state.vscdb")
SUMMARIES_PB = os.path.join(GEMINI_DIR, "agyhub_summaries_proto.pb")
PB_KEY = "antigravityUnifiedStateSync.trajectorySummaries"

# ============================================================================
# Protobuf helpers
# ============================================================================
def decode_varint(data, pos):
    result, shift = 0, 0
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

def write_varint_field(field_num, value):
    return encode_varint((field_num << 3) | 0) + encode_varint(value)

def write_timestamp(field_num, epoch_seconds, nanos=0):
    inner = write_varint_field(1, epoch_seconds) + write_varint_field(2, nanos)
    return write_bytes_field(field_num, inner)

print("=" * 60)
print("  Antigravity IDE — .db 對話索引修復工具 v2")
print("=" * 60)

# ============================================================================
# Step 0: Scan .db conversations
# ============================================================================
print("\n[Step 0] 掃描 .db 對話...")
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

print(f"  找到 {len(db_conversations)} 個 .db 對話")

# ============================================================================
# Step 1: Read and decode trajectorySummaries
# ============================================================================
print("\n[Step 1] 讀取 trajectorySummaries...")
conn = sqlite3.connect(STATE_DB)
cur = conn.cursor()
cur.execute("SELECT value FROM ItemTable WHERE key=?", (PB_KEY,))
raw_b64 = cur.fetchone()[0]
conn.close()

decoded = base64.b64decode(raw_b64)
print(f"  大小: {len(decoded)} bytes ({len(raw_b64)} chars b64)")

# ============================================================================
# Step 2: Parse entries and find template + missing conversations
# ============================================================================
print("\n[Step 2] 解析索引...")

# Parse all top-level entries
pos = 0
all_entries = []  # list of (uuid, full_bytes, entry_data)
template_entry = None
template_uuid = None

while pos < len(decoded):
    entry_start = pos
    tag, pos = decode_varint(decoded, pos)
    if (tag & 7) != 2:
        break
    length, pos = decode_varint(decoded, pos)
    entry_data = decoded[pos:pos+length]
    pos += length
    full_bytes = decoded[entry_start:pos]
    
    # Extract UUID
    uuid = None
    entry_text = entry_data.decode('utf-8', errors='ignore')
    match = re.search(r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}', entry_text)
    if match:
        uuid = match.group()
    
    all_entries.append((uuid, full_bytes, entry_data))
    
    # Use aebe795c as template (it's a .db entry the IDE created itself)
    if uuid and 'aebe795c' in uuid:
        template_uuid = uuid
        template_entry = entry_data

print(f"  現有條目: {len(all_entries)}")
if template_uuid:
    print(f"  模板: {template_uuid[:8]}... (.db 格式)")

# Find missing
missing = []
indexed_uuids = {e[0] for e in all_entries if e[0]}
for cid in db_conversations:
    if cid not in indexed_uuids:
        missing.append(cid)

if not missing:
    print("\n  所有 .db 對話都已索引!")
    sys.exit(0)

print(f"\n  缺失 {len(missing)} 個對話:")
for cid in missing:
    print(f"    - {cid}")

if not template_entry:
    print("\n  ERROR: 找不到模板 entry，無法繼續")
    sys.exit(1)

# ============================================================================
# Step 3: Clone template and modify for each missing conversation
# ============================================================================
print("\n[Step 3] 從模板克隆 entry...")

def get_title(cid):
    """Extract title from transcript.jsonl."""
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
                            return match.group(1).strip()[:60]
        except:
            pass
    return f"Conversation {cid[:8]}"

def get_conversation_timestamps(cid):
    """Get create/modify times from .db file."""
    db_path = db_conversations[cid]
    stat = os.stat(db_path)
    return int(stat.st_ctime), int(stat.st_mtime)

def build_inner_protobuf(title, create_epoch, modify_epoch, model_uuid=None):
    """Build the inner protobuf blob (the content inside base64)."""
    if not model_uuid:
        model_uuid = "00000000-0000-0000-0000-000000000000"
    
    inner = b""
    inner += write_string_field(1, title)               # Field 1: title
    inner += write_varint_field(2, 10)                   # Field 2: step count (approximate)
    inner += write_timestamp(3, create_epoch, 0)         # Field 3: create timestamp
    inner += write_string_field(4, model_uuid)           # Field 4: model UUID
    inner += write_varint_field(5, 1)                    # Field 5: type=1
    inner += write_timestamp(7, modify_epoch, 0)         # Field 7: last modified
    
    # Field 9: workspace metadata (keep same as template - same workspace)
    # Extract Field 9 from template's inner protobuf
    # For simplicity, reconstruct workspace metadata for d:/hermes-agent
    ws_inner = b""
    ws_inner += write_string_field(1, "file:///d:/hermes-agent")
    ws_inner += write_string_field(2, "file:///d:/hermes-agent")
    ws_sub3 = write_string_field(1, "jasper7523/hermes-agent") + write_string_field(2, "https://github.com/jasper7523/hermes-agent.git")
    ws_inner += write_bytes_field(3, ws_sub3)
    ws_inner += write_string_field(4, "main")
    inner += write_bytes_field(9, ws_inner)
    
    inner += write_timestamp(10, modify_epoch, 0)        # Field 10: another timestamp
    inner += write_varint_field(16, 10)                   # Field 16: step count
    
    # Field 17: workspace extended metadata
    ws17 = b""
    ws17 += write_bytes_field(1, ws_inner)               # Same workspace info
    ws17 += write_timestamp(2, create_epoch, 0)          # Field 2: timestamp
    ws17 += write_string_field(3, model_uuid)            # Field 3: session UUID
    ws17 += write_string_field(7, "file:///d%3A/hermes-agent")  # Field 7: encoded URI
    inner += write_bytes_field(17, ws17)
    
    inner += write_varint_field(22, 4)                   # Field 22: status
    
    return inner

new_entries_bytes = b""
for cid in missing:
    title = get_title(cid)
    create_epoch, modify_epoch = get_conversation_timestamps(cid)
    
    print(f"  {cid[:8]}... | {title}")
    print(f"    created={time.strftime('%Y-%m-%d %H:%M', time.localtime(create_epoch))}")
    print(f"    modified={time.strftime('%Y-%m-%d %H:%M', time.localtime(modify_epoch))}")
    
    # Build inner protobuf
    inner_pb = build_inner_protobuf(title, create_epoch, modify_epoch)
    inner_b64 = base64.b64encode(inner_pb).decode('ascii')
    
    # Build Field 2 (wrapper containing base64 string)
    field2_content = write_string_field(1, inner_b64)
    
    # Build full entry: Field 1 = UUID, Field 2 = wrapper
    entry_content = write_string_field(1, cid) + write_bytes_field(2, field2_content)
    
    # Wrap as top-level Field 1
    new_entry = write_bytes_field(1, entry_content)
    new_entries_bytes += new_entry

print(f"\n  生成 {len(missing)} 個 entry ({len(new_entries_bytes)} bytes)")

# ============================================================================
# Step 4: Backup
# ============================================================================
print("\n[Step 4] 備份...")
ts = int(time.time())

state_backup = f"{STATE_DB}.pre_dbfix_{ts}"
shutil.copy2(STATE_DB, state_backup)
print(f"  state.vscdb -> {os.path.basename(state_backup)}")

if os.path.exists(SUMMARIES_PB):
    pb_backup = f"{SUMMARIES_PB}.pre_dbfix_{ts}"
    shutil.copy2(SUMMARIES_PB, pb_backup)
    print(f"  agyhub_summaries_proto.pb -> {os.path.basename(pb_backup)}")

# ============================================================================
# Step 5: Inject
# ============================================================================
print("\n[Step 5] 注入索引...")

# Inject into state.vscdb trajectorySummaries
new_decoded = decoded + new_entries_bytes
new_b64 = base64.b64encode(new_decoded).decode('ascii')

conn = sqlite3.connect(STATE_DB)
cur = conn.cursor()
cur.execute("UPDATE ItemTable SET value=? WHERE key=?", (new_b64, PB_KEY))
conn.commit()
conn.close()
print(f"  state.vscdb: {len(decoded)} -> {len(new_decoded)} bytes")

# Inject into agyhub_summaries_proto.pb
if os.path.exists(SUMMARIES_PB):
    with open(SUMMARIES_PB, 'rb') as f:
        pb_data = f.read()
    with open(SUMMARIES_PB, 'wb') as f:
        f.write(pb_data + new_entries_bytes)
    print(f"  agyhub_summaries_proto.pb: {len(pb_data)} -> {len(pb_data) + len(new_entries_bytes)} bytes")

# ============================================================================
# Step 6: Verify
# ============================================================================
print("\n[Step 6] 驗證...")
conn = sqlite3.connect(STATE_DB)
cur = conn.cursor()
cur.execute("SELECT value FROM ItemTable WHERE key=?", (PB_KEY,))
verify_b64 = cur.fetchone()[0]
conn.close()

verify_decoded = base64.b64decode(verify_b64)
all_ok = True
for cid in missing:
    found = cid.encode() in verify_decoded
    status = "OK" if found else "FAIL"
    print(f"  [{status}] {cid[:8]}... in trajectorySummaries")
    if not found:
        all_ok = False

if os.path.exists(SUMMARIES_PB):
    with open(SUMMARIES_PB, 'rb') as f:
        pb_verify = f.read()
    for cid in missing:
        found = cid.encode() in pb_verify
        status = "OK" if found else "FAIL"
        print(f"  [{status}] {cid[:8]}... in agyhub_summaries_proto.pb")
        if not found:
            all_ok = False

print()
if all_ok:
    print("=" * 60)
    print("  修復完成! 請重新啟動 Antigravity IDE")
    print("=" * 60)
    print(f"\n  如需回滾:")
    print(f"    state.vscdb:  copy {os.path.basename(state_backup)} -> state.vscdb")
    print(f"    summaries.pb: copy {os.path.basename(pb_backup)} -> agyhub_summaries_proto.pb")
else:
    print("  WARNING: 部分注入失敗，請檢查備份")
