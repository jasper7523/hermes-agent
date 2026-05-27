"""
Antigravity IDE 對話索引滾動式備份與同步守護腳本
==================================================
用途：
  1. 定期備份 trajectorySummaries protobuf 索引
  2. 偵測遺失的對話（有 annotation 但不在索引中）
  3. 自動注入遺失的最近對話
  4. 滾動保留最近 7 天的備份

使用方式：
  python trajectory_guardian.py --check      # 檢查但不修改
  python trajectory_guardian.py --backup     # 僅備份
  python trajectory_guardian.py --fix        # 備份 + 自動修復
  python trajectory_guardian.py --restore <file>  # 從備份還原

建議：設定 Windows Task Scheduler 每 6 小時執行一次 --fix
"""
import sqlite3, os, sys, base64, time, json, re, argparse, glob, shutil
from datetime import datetime, timedelta

sys.stdout.reconfigure(encoding='utf-8')

# ============================================================
# Configuration
# ============================================================
DB_PATH = os.path.join(os.environ.get('APPDATA', ''), 'Antigravity IDE', 'User', 'globalStorage', 'state.vscdb')
ANN_DIR = os.path.join(os.environ.get('USERPROFILE', ''), '.gemini', 'antigravity-ide', 'annotations')
BRAIN_DIR = os.path.join(os.environ.get('USERPROFILE', ''), '.gemini', 'antigravity-ide', 'brain')
BACKUP_DIR = os.path.join('D:', os.sep, 'Agent_Hub', 'agents', 'Mem_Agent', 'data', 'n6', 'trajectory_backups')
MAX_BACKUP_DAYS = 7  # Keep backups for 7 days
MAX_INDEX_ENTRIES = 120  # Allow up to 120 entries (above the 100 limit to have buffer)
RECENT_THRESHOLD_HOURS = 96  # 4 days - inject missing conversations newer than this

# ============================================================
# Protobuf helpers
# ============================================================
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

def encode_varint(value):
    parts = []
    while value > 0x7F:
        parts.append((value & 0x7F) | 0x80)
        value >>= 7
    parts.append(value & 0x7F)
    return bytes(parts)

def parse_protobuf(data):
    pos = 0
    results = []
    while pos < len(data):
        try:
            tag_val, pos2 = decode_varint(data, pos)
            field_num = tag_val >> 3
            wire_type = tag_val & 0x7
            if wire_type == 0:
                val, pos2 = decode_varint(data, pos2)
                results.append((field_num, wire_type, val))
                pos = pos2
            elif wire_type == 2:
                length, pos2 = decode_varint(data, pos2)
                val = data[pos2:pos2+length]
                results.append((field_num, wire_type, val))
                pos = pos2 + length
            elif wire_type == 1: pos = pos2 + 8
            elif wire_type == 5: pos = pos2 + 4
            else: break
        except: break
    return results

def make_field(field_num, wire_type, value):
    tag = encode_varint((field_num << 3) | wire_type)
    if wire_type == 0:
        return tag + encode_varint(value)
    elif wire_type == 2:
        return tag + encode_varint(len(value)) + value
    return b''

# ============================================================
# Core functions
# ============================================================
def get_indexed_ids():
    """Get all conversation IDs currently in trajectorySummaries."""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT value FROM ItemTable WHERE key = ?",
                ('antigravityUnifiedStateSync.trajectorySummaries',))
    row = cur.fetchone()
    conn.close()
    if not row:
        return set(), b''
    raw = row[0]
    data = base64.b64decode(raw) if isinstance(raw, str) else raw
    ids = set()
    for fn, wt, val in parse_protobuf(data):
        if fn == 1 and wt == 2:
            for ifn, iwt, ival in parse_protobuf(val):
                if ifn == 1 and iwt == 2:
                    try: ids.add(ival.decode('utf-8'))
                    except: pass
    return ids, data

def get_annotation_ids():
    """Get all conversation IDs from annotations directory."""
    ids = {}
    if not os.path.isdir(ANN_DIR):
        return ids
    for f in os.listdir(ANN_DIR):
        if f.endswith('.pbtxt') and not f.endswith('.bak') and not f.endswith('.bak2'):
            cid = f.replace('.pbtxt', '')
            ann_path = os.path.join(ANN_DIR, f)
            with open(ann_path, 'r', encoding='utf-8', errors='replace') as fh:
                content = fh.read()
            ts_m = re.search(r'last_user_view_time:\{seconds:(\d+)', content)
            title_m = re.search(r'title:"([^"]*)"', content)
            ids[cid] = {
                'view_time': int(ts_m.group(1)) if ts_m else 0,
                'title': title_m.group(1)[:100] if title_m else '(no title)',
                'has_brain': os.path.isdir(os.path.join(BRAIN_DIR, cid)),
                'has_transcript': os.path.exists(
                    os.path.join(BRAIN_DIR, cid, '.system_generated', 'logs', 'transcript.jsonl'))
            }
    return ids

def find_missing(indexed_ids, ann_ids, threshold_hours=RECENT_THRESHOLD_HOURS):
    """Find conversations that have annotations but are missing from index."""
    now = int(time.time())
    missing = []
    for cid, info in ann_ids.items():
        if cid in indexed_ids:
            continue
        if not info['has_brain'] or not info['has_transcript']:
            continue
        age_h = (now - info['view_time']) / 3600 if info['view_time'] else 999999
        if age_h <= threshold_hours:
            missing.append({
                'id': cid,
                'title': info['title'],
                'age_hours': round(age_h, 1),
                'view_time': info['view_time']
            })
    missing.sort(key=lambda x: x['view_time'], reverse=True)
    return missing

def backup_index(data, label='auto'):
    """Backup current trajectorySummaries to file."""
    os.makedirs(BACKUP_DIR, exist_ok=True)
    ts = time.strftime('%Y%m%d_%H%M%S')
    backup_path = os.path.join(BACKUP_DIR, f'traj_index_{label}_{ts}.b64')
    b64_data = base64.b64encode(data).decode() if isinstance(data, bytes) else data
    with open(backup_path, 'w') as f:
        f.write(b64_data)
    print(f"  Backup saved: {backup_path} ({len(data)} bytes)")
    return backup_path

def cleanup_old_backups():
    """Remove backups older than MAX_BACKUP_DAYS."""
    if not os.path.isdir(BACKUP_DIR):
        return
    cutoff = time.time() - (MAX_BACKUP_DAYS * 86400)
    removed = 0
    for f in glob.glob(os.path.join(BACKUP_DIR, 'traj_index_*.b64')):
        if os.path.getmtime(f) < cutoff:
            os.remove(f)
            removed += 1
    if removed:
        print(f"  Cleaned up {removed} old backup(s)")

def build_inject_entry(conv_id, title, created_ts, modified_ts, step_count, workspace_uri):
    """Build a protobuf entry for injection."""
    ws_path = workspace_uri.replace('file:///d%3A/', 'file:///d:/')
    ws_raw = ws_path.encode('utf-8')
    ws_field = b'\n' + bytes([len(ws_raw)]) + ws_raw + b'\x12' + bytes([len(ws_raw)]) + ws_raw + b'\x1a\x00\"\x04main'
    
    f17_content = (
        make_field(1, 2, ws_field) +
        make_field(2, 2, make_field(1, 0, created_ts) + make_field(2, 0, 0)) +
        make_field(3, 2, conv_id.encode('utf-8')) +
        make_field(7, 2, workspace_uri.encode('utf-8'))
    )
    
    inner = b''
    inner += make_field(1, 2, title.encode('utf-8'))
    inner += make_field(2, 0, step_count)
    inner += make_field(3, 2, make_field(1, 0, modified_ts) + make_field(2, 0, 0))
    inner += make_field(4, 2, conv_id.encode('utf-8'))
    inner += make_field(5, 0, 1)
    inner += make_field(7, 2, make_field(1, 0, created_ts) + make_field(2, 0, 0))
    inner += make_field(9, 2, ws_field)
    inner += make_field(10, 2, make_field(1, 0, modified_ts) + make_field(2, 0, 0))
    inner += make_field(16, 0, max(step_count - 10, 0))
    inner += make_field(17, 2, f17_content)
    inner += make_field(22, 0, 4)
    
    entry = make_field(1, 2, conv_id.encode('utf-8')) + make_field(2, 2, base64.b64encode(inner))
    return entry

def guess_workspace(title):
    """Guess workspace from conversation title."""
    title_lower = title.lower()
    if any(k in title_lower for k in ['ch ', 'ch2', 'ch1', '文獻', '撰寫', '架構', 'literature', 'synthesis']):
        return 'file:///d%3A/Agent_Hub/agents/Book_Writer_Agent'
    if any(k in title_lower for k in ['論文', 'thesis', 'ssci', 'academic', 'research proposal']):
        return 'file:///d%3A/Agent_Hub/agents/Academic_Oracle_Agent'
    return 'file:///d%3A/hermes-agent'

def inject_missing(data, missing_convos):
    """Inject missing conversations into the protobuf data."""
    now = int(time.time())
    new_entries_bytes = b''
    
    for m in missing_convos:
        cid = m['id']
        title = m['title']
        
        # Get timestamps from brain dir
        brain_path = os.path.join(BRAIN_DIR, cid)
        modified_ts = int(os.path.getmtime(brain_path)) if os.path.exists(brain_path) else now
        created_ts = modified_ts - 3600  # default 1 hour before modified
        
        transcript = os.path.join(brain_path, '.system_generated', 'logs', 'transcript.jsonl')
        step_count = 0
        if os.path.exists(transcript):
            try:
                with open(transcript, 'r', encoding='utf-8', errors='replace') as f:
                    step_count = sum(1 for _ in f)
                with open(transcript, 'r', encoding='utf-8', errors='replace') as f:
                    first_line = f.readline()
                if first_line:
                    first = json.loads(first_line)
                    ts_str = first.get('timestamp', '')
                    if ts_str:
                        try:
                            dt = datetime.fromisoformat(ts_str.replace('Z', '+00:00'))
                            created_ts = int(dt.timestamp())
                        except: pass
            except: pass
        
        workspace = guess_workspace(title)
        entry_bytes = build_inject_entry(cid, title, created_ts, modified_ts, step_count, workspace)
        new_entries_bytes += make_field(1, 2, entry_bytes)
    
    return data + new_entries_bytes

def restore_index(backup_path):
    """Restore trajectorySummaries from a backup file."""
    with open(backup_path, 'r') as f:
        b64_data = f.read()
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("UPDATE ItemTable SET value = ? WHERE key = ?",
                (b64_data, 'antigravityUnifiedStateSync.trajectorySummaries'))
    conn.commit()
    conn.close()
    print(f"  Restored from: {backup_path}")

# ============================================================
# Main
# ============================================================
def main():
    parser = argparse.ArgumentParser(description='Trajectory Index Guardian')
    parser.add_argument('--check', action='store_true', help='Check for missing conversations')
    parser.add_argument('--backup', action='store_true', help='Backup current index')
    parser.add_argument('--fix', action='store_true', help='Backup + auto-fix missing')
    parser.add_argument('--restore', type=str, help='Restore from backup file')
    args = parser.parse_args()
    
    if not any([args.check, args.backup, args.fix, args.restore]):
        args.check = True
    
    print(f"[Trajectory Guardian] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    if args.restore:
        if not os.path.exists(args.restore):
            print(f"  ERROR: Backup file not found: {args.restore}")
            return 1
        restore_index(args.restore)
        return 0
    
    # Get current state
    indexed_ids, raw_data = get_indexed_ids()
    ann_ids = get_annotation_ids()
    missing = find_missing(indexed_ids, ann_ids)
    
    print(f"  Indexed entries:    {len(indexed_ids)}")
    print(f"  Annotation entries: {len(ann_ids)}")
    print(f"  Missing (recent):   {len(missing)}")
    print()
    
    if missing:
        print("  Missing conversations:")
        for m in missing:
            print(f"    {m['id'][:12]}.. age={m['age_hours']:7.1f}h  {m['title'][:60]}")
        print()
    else:
        print("  No missing conversations detected.")
    
    if args.backup or args.fix:
        print("  Creating backup...")
        backup_index(raw_data, 'guardian')
        cleanup_old_backups()
        print()
    
    if args.fix and missing:
        print(f"  Injecting {len(missing)} missing conversations...")
        new_data = inject_missing(raw_data, missing)
        new_b64 = base64.b64encode(new_data).decode()
        
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("UPDATE ItemTable SET value = ? WHERE key = ?",
                    (new_b64, 'antigravityUnifiedStateSync.trajectorySummaries'))
        conn.commit()
        conn.close()
        
        # Verify
        new_indexed, _ = get_indexed_ids()
        injected = sum(1 for m in missing if m['id'] in new_indexed)
        print(f"  Injected: {injected}/{len(missing)}")
        print(f"  New total: {len(new_indexed)} entries")
        print()
    
    print("  Done.")
    return 0

if __name__ == '__main__':
    sys.exit(main())
