#!/usr/bin/env python3
"""
Antigravity 2 — .db 對話完整修復腳本
1. 確認 AG2 未執行
2. 複製 .db 對話檔 + brain 目錄
3. 注入索引
"""
import sqlite3, base64, os, re, sys, json, shutil, time, subprocess
sys.stdout.reconfigure(encoding='utf-8')

AG2_GEMINI = os.path.expanduser(r"~\.gemini\antigravity")
AG2_CONVOS = os.path.join(AG2_GEMINI, "conversations")
AG2_BRAIN = os.path.join(AG2_GEMINI, "brain")
AG2_STATE = os.path.join(os.environ["APPDATA"], "Antigravity", "User", "globalStorage", "state.vscdb")
AG2_PB = os.path.join(AG2_GEMINI, "agyhub_summaries_proto.pb")

IDE_GEMINI = os.path.expanduser(r"~\.gemini\antigravity-ide")
IDE_CONVOS = os.path.join(IDE_GEMINI, "conversations")
IDE_BRAIN = os.path.join(IDE_GEMINI, "brain")

PB_KEY = "antigravityUnifiedStateSync.trajectorySummaries"
TARGETS = [
    "a0af2503-6528-4691-850e-bea17cc94e66",
    "fb9a0c95-75a7-49c8-b66a-4aec7f38855c",
    "aebe795c-466d-47e9-bed5-70aadbcc822d",
]

def decode_varint(data, pos):
    result, shift = 0, 0
    while pos < len(data):
        b = data[pos]; result |= (b & 0x7F) << shift; pos += 1
        if not (b & 0x80): break
        shift += 7
    return result, pos

def encode_varint(v):
    if v == 0: return b"\x00"
    r = bytearray()
    while v > 0x7F: r.append((v & 0x7F) | 0x80); v >>= 7
    r.append(v & 0x7F)
    return bytes(r)

def write_string_field(fn, val):
    b = val.encode("utf-8") if isinstance(val, str) else val
    return encode_varint((fn << 3) | 2) + encode_varint(len(b)) + b

def write_bytes_field(fn, val):
    return encode_varint((fn << 3) | 2) + encode_varint(len(val)) + val

def write_varint_field(fn, val):
    return encode_varint((fn << 3) | 0) + encode_varint(val)

def write_timestamp(fn, epoch, nanos=0):
    inner = write_varint_field(1, epoch) + write_varint_field(2, nanos)
    return write_bytes_field(fn, inner)

def get_title(cid):
    transcript = os.path.join(IDE_BRAIN, cid, ".system_generated", "logs", "transcript.jsonl")
    if os.path.exists(transcript):
        try:
            with open(transcript, 'r', encoding='utf-8') as f:
                for line in f:
                    data = json.loads(line)
                    if data.get("type") == "USER_INPUT" and data.get("content"):
                        m = re.search(r'<USER_REQUEST>\s*(.*?)(?:\s*</USER_REQUEST>|\n)', data["content"], re.DOTALL)
                        if m: return m.group(1).strip()[:60]
        except: pass
    return f"Conversation {cid[:8]}"

print("=" * 60)
print("  Antigravity 2 — .db 對話修復")
print("=" * 60)

# Step 0: Verify AG2 is closed
print("\n[0] 確認 Antigravity 2 未執行...")
r = subprocess.run(["powershell", "-Command", "Get-Process 'Antigravity' -ErrorAction SilentlyContinue | Select-Object -First 1"], capture_output=True, text=True)
if "Antigravity" in r.stdout:
    print("  ⚠️  Antigravity 2 仍在執行! 請先關閉。")
    sys.exit(1)
print("  ✅ 未執行")

# Step 1: Copy .db files
print("\n[1] 複製 .db 對話檔...")
for cid in TARGETS:
    src = os.path.join(IDE_CONVOS, f"{cid}.db")
    dst = os.path.join(AG2_CONVOS, f"{cid}.db")
    if not os.path.exists(src):
        print(f"  ⚠️  來源不存在: {cid[:8]}.db")
        continue
    if os.path.exists(dst):
        print(f"  ℹ️  已存在: {cid[:8]}.db ({os.path.getsize(dst)} bytes)")
    else:
        shutil.copy2(src, dst)
        print(f"  ✅ 複製: {cid[:8]}.db ({os.path.getsize(dst)} bytes)")

# Step 2: Copy brain dirs
print("\n[2] 複製 brain/ 目錄...")
for cid in TARGETS:
    src = os.path.join(IDE_BRAIN, cid)
    dst = os.path.join(AG2_BRAIN, cid)
    if not os.path.isdir(src):
        print(f"  ⚠️  來源不存在: brain/{cid[:8]}/")
        continue
    if os.path.isdir(dst):
        print(f"  ℹ️  已存在: brain/{cid[:8]}/")
    else:
        shutil.copytree(src, dst)
        file_count = sum(len(files) for _, _, files in os.walk(dst))
        print(f"  ✅ 複製: brain/{cid[:8]}/ ({file_count} files)")

# Step 3: Backup
print("\n[3] 備份...")
ts = int(time.time())
state_bak = f"{AG2_STATE}.pre_dbfix_{ts}"
shutil.copy2(AG2_STATE, state_bak)
print(f"  ✅ {os.path.basename(state_bak)}")
pb_bak = f"{AG2_PB}.pre_dbfix_{ts}"
shutil.copy2(AG2_PB, pb_bak)
print(f"  ✅ {os.path.basename(pb_bak)}")

# Step 4: Read current index
print("\n[4] 讀取索引...")
conn = sqlite3.connect(AG2_STATE)
cur = conn.cursor()
cur.execute("SELECT value FROM ItemTable WHERE key=?", (PB_KEY,))
row = cur.fetchone()
conn.close()

decoded = base64.b64decode(row[0])
print(f"  trajectorySummaries: {len(decoded)} bytes")

# Check which are already indexed
already_indexed = set()
for cid in TARGETS:
    if cid.encode() in decoded:
        already_indexed.add(cid)
        print(f"  ✅ {cid[:8]}... 已在索引")

to_inject = [cid for cid in TARGETS if cid not in already_indexed]
if not to_inject:
    print("\n  🎉 所有對話都已索引!")
    sys.exit(0)

print(f"\n  需注入: {len(to_inject)} 個")

# Step 5: Build entries
print("\n[5] 建構索引條目...")

def build_inner_pb(title, create_epoch, modify_epoch):
    ws_inner = b""
    ws_inner += write_string_field(1, "file:///d:/hermes-agent")
    ws_inner += write_string_field(2, "file:///d:/hermes-agent")
    ws_sub3 = write_string_field(1, "jasper7523/hermes-agent") + write_string_field(2, "https://github.com/jasper7523/hermes-agent.git")
    ws_inner += write_bytes_field(3, ws_sub3)
    ws_inner += write_string_field(4, "main")

    inner = b""
    inner += write_string_field(1, title)
    inner += write_varint_field(2, 10)
    inner += write_timestamp(3, create_epoch, 0)
    inner += write_string_field(4, "00000000-0000-0000-0000-000000000000")
    inner += write_varint_field(5, 1)
    inner += write_timestamp(7, modify_epoch, 0)
    inner += write_bytes_field(9, ws_inner)
    inner += write_timestamp(10, modify_epoch, 0)
    inner += write_varint_field(16, 10)
    ws17 = write_bytes_field(1, ws_inner) + write_timestamp(2, create_epoch, 0) + write_string_field(3, "00000000-0000-0000-0000-000000000000") + write_string_field(7, "file:///d%3A/hermes-agent")
    inner += write_bytes_field(17, ws17)
    inner += write_varint_field(22, 4)
    return inner

new_bytes = b""
for cid in to_inject:
    title = get_title(cid)
    db_path = os.path.join(AG2_CONVOS, f"{cid}.db")
    stat = os.stat(db_path)
    create_ts, modify_ts = int(stat.st_ctime), int(stat.st_mtime)

    print(f"  {cid[:8]}... | {title}")

    inner_pb = build_inner_pb(title, create_ts, modify_ts)
    inner_b64 = base64.b64encode(inner_pb).decode('ascii')
    field2 = write_string_field(1, inner_b64)
    entry = write_string_field(1, cid) + write_bytes_field(2, field2)
    new_bytes += write_bytes_field(1, entry)

# Step 6: Inject
print(f"\n[6] 注入 ({len(new_bytes)} bytes)...")

# state.vscdb
new_decoded = decoded + new_bytes
new_b64 = base64.b64encode(new_decoded).decode('ascii')
conn = sqlite3.connect(AG2_STATE)
cur = conn.cursor()
cur.execute("UPDATE ItemTable SET value=? WHERE key=?", (new_b64, PB_KEY))
conn.commit()
conn.close()
print(f"  ✅ state.vscdb: {len(decoded)} → {len(new_decoded)} bytes")

# agyhub_summaries_proto.pb
with open(AG2_PB, 'rb') as f:
    pb_data = f.read()
with open(AG2_PB, 'wb') as f:
    f.write(pb_data + new_bytes)
print(f"  ✅ agyhub_summaries_proto.pb: {len(pb_data)} → {len(pb_data)+len(new_bytes)} bytes")

# Step 7: Verify
print(f"\n[7] 驗證...")
conn = sqlite3.connect(AG2_STATE)
cur = conn.cursor()
cur.execute("SELECT value FROM ItemTable WHERE key=?", (PB_KEY,))
v = base64.b64decode(cur.fetchone()[0])
conn.close()

with open(AG2_PB, 'rb') as f:
    pb_v = f.read()

all_ok = True
for cid in to_inject:
    s1 = cid.encode() in v
    s2 = cid.encode() in pb_v
    ok = s1 and s2
    print(f"  {'✅' if ok else '❌'} {cid[:8]}... | vscdb={s1} pb={s2}")
    if not ok: all_ok = False

print()
if all_ok:
    print("=" * 60)
    print("  ✅ 修復完成! 請開啟 Antigravity 2 驗證")
    print("=" * 60)
    print(f"\n  回滾指令:")
    print(f"    copy \"{state_bak}\" \"{AG2_STATE}\"")
    print(f"    copy \"{pb_bak}\" \"{AG2_PB}\"")
else:
    print("  ⚠️ 部分驗證失敗")
