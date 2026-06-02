import sqlite3
import base64
import os
import sys
import glob
import re
import shutil
from datetime import datetime, timedelta
from pathlib import Path

# Config
APPDATA = Path(os.environ['APPDATA'])
GLOBALSTORE = APPDATA / 'Antigravity IDE' / 'User' / 'globalStorage'
STATE_DB = GLOBALSTORE / 'state.vscdb'
KEY = 'antigravityUnifiedStateSync.trajectorySummaries'
PB_DIR = Path(os.environ['USERPROFILE']) / '.gemini' / 'antigravity-ide'
BRAIN_DIR = PB_DIR / 'brain'

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

def parse_entries(decoded_bytes, source_name):
    pos = 0
    entries = {}
    while pos < len(decoded_bytes):
        start_pos = pos
        try:
            tag, pos = decode_varint(decoded_bytes, pos)
            field_num = tag >> 3
            wire_type = tag & 7
            
            if wire_type != 2:
                break
                
            length, pos = decode_varint(decoded_bytes, pos)
            if pos + length > len(decoded_bytes):
                break
                
            entry_data = decoded_bytes[pos:pos+length]
            full_entry_bytes = decoded_bytes[start_pos:pos+length]
            pos += length
            
            # Find UUID via regex
            entry_str = entry_data.decode('utf-8', errors='ignore')
            match = re.search(r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}', entry_str)
            if match:
                uuid = match.group()
                entries[uuid] = full_entry_bytes
        except Exception:
            break
    return entries

def get_vscdb_payload(db_path):
    try:
        conn = sqlite3.connect(f'file:{db_path}?mode=ro', uri=True)
        cursor = conn.cursor()
        cursor.execute('SELECT value FROM ItemTable WHERE key = ?', (KEY,))
        row = cursor.fetchone()
        conn.close()
        if row:
            if isinstance(row[0], bytes):
                return base64.b64decode(row[0])
            else:
                return base64.b64decode(row[0].encode('ascii') + b'==')
    except Exception:
        pass
    return None

def check_ide_running():
    import subprocess
    result = subprocess.run(
        ['powershell', '-Command',
         'Get-Process | Where-Object {$_.MainWindowTitle -like "*Antigravity*" -or $_.ProcessName -like "*Antigravity*"} | Measure-Object | Select-Object -ExpandProperty Count'],
        capture_output=True, text=True
    )
    count = int(result.stdout.strip()) if result.stdout.strip().isdigit() else 0
    return count > 0

def extract_title(entry):
    pos = 0
    while pos < len(entry):
        tag, pos = decode_varint(entry, pos)
        fn, wt = tag >> 3, tag & 7
        if wt == 2:
            l, pos = decode_varint(entry, pos)
            if fn == 2: # Field 2 is State
                sub = entry[pos-l:pos]
                sp = 0
                while sp < len(sub):
                    stag, sp = decode_varint(sub, sp)
                    sfn, swt = stag >> 3, stag & 7
                    if swt == 2:
                        sl, sp = decode_varint(sub, sp)
                        if sfn == 1: # Nested Field 1 is Title
                            return sub[sp-sl:sp]
                        sp += sl
                    elif swt == 0:
                        _, sp = decode_varint(sub, sp)
                    else:
                        break
                break
        elif wt == 0:
            _, pos = decode_varint(entry, pos)
        else:
            break
    return b""

def create_template_entry(template_bytes, old_uuid, new_uuid, new_title_str):
    b_old = old_uuid.encode('ascii')
    b_new = new_uuid.encode('ascii')
    if b_old not in template_bytes:
        return None
    
    target_block = template_bytes.replace(b_old, b_new)
    
    # Pad or truncate new title to exact byte length of old title
    old_title_bytes = extract_title(target_block)
    if old_title_bytes:
        target_len = len(old_title_bytes)
        new_title_bytes = new_title_str.encode('utf-8', errors='ignore')
        
        # Adjust length with spaces to match exactly
        if len(new_title_bytes) < target_len:
            new_title_bytes += b' ' * (target_len - len(new_title_bytes))
        elif len(new_title_bytes) > target_len:
            # truncate (be careful with utf-8 boundaries, but simple ascii spaces is safe)
            new_title_bytes = new_title_bytes[:target_len]
            
        target_block = target_block.replace(old_title_bytes, new_title_bytes, 1)
        
    return target_block

def main():
    print("============================================================")
    print("  ULTIMATE ANTIGRAVITY IDE HISTORY RECOVERY (WITH INJECTION)")
    print("============================================================")
    
    if check_ide_running():
        print("[ERROR] IDE is running. Please close it first.")
        sys.exit(1)

    files = []
    
    # Collect safe sources ONLY. We ignore the files corrupted by earlier failed runs.
    for f in glob.glob(str(GLOBALSTORE / 'state.vscdb*')):
        name = os.path.basename(f)
        if "pre_ultimate_recover" in name:
            continue
        files.append(Path(f))
        
    for pb in PB_DIR.rglob("agyhub_summaries_proto*.pb"):
        files.append(pb)
        
    files.sort(key=lambda x: x.stat().st_mtime)
    all_entries = {}
    
    for f in files:
        payload = get_vscdb_payload(f) if f.suffix != ".pb" else f.read_bytes()
        if payload:
            entries = parse_entries(payload, f.name)
            for u, b in entries.items():
                all_entries[u] = b

    print(f"[INFO] Recovered {len(all_entries)} unique conversations from DB/PB backups.")
    
    # 3. Scan the actual brain/ folder for missing 14-day history
    cutoff_time = datetime.now() - timedelta(days=14)
    missing_uuids = []
    
    for uuid_dir in BRAIN_DIR.iterdir():
        if not uuid_dir.is_dir(): continue
        uuid = uuid_dir.name
        if not re.match(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', uuid):
            continue
            
        transcript = uuid_dir / '.system_generated' / 'logs' / 'transcript.jsonl'
        if transcript.exists():
            mod_time = datetime.fromtimestamp(transcript.stat().st_mtime)
            if mod_time > cutoff_time:
                if uuid not in all_entries:
                    # extract 10 char snippet smartly
                    snippet = "Recovered "
                    try:
                        import json
                        with open(transcript, 'r', encoding='utf-8') as f:
                            for line in f:
                                data = json.loads(line)
                                if data.get('type') == 'USER_INPUT' and data.get('content'):
                                    text = data['content']
                                    # Strip XML tags injected by system
                                    text = re.sub(r'<[^>]+>', '', text)
                                    # Strip common boilerplate or model declarations
                                    text = re.sub(r'(?i)(gemini|ollama|gemma|模型|宣告|使用|N[1-9])', '', text)
                                    text = text.strip()
                                    text = re.sub(r'[\r\n\t]+', ' ', text)
                                    # Strip non-alphanumeric punctuation at start
                                    text = re.sub(r'^[^a-zA-Z0-9\u4e00-\u9fa5]+', '', text)
                                    if len(text) >= 2:
                                        snippet = text[:10].ljust(10, ' ')
                                        break
                    except Exception:
                        pass
                    
                    missing_uuids.append((uuid, snippet))
                    
    print(f"[INFO] Found {len(missing_uuids)} MISSING recent conversations on disk (last 14 days)!")
    
    # 4. Inject missing ones
    if missing_uuids and all_entries:
        # Avoid using a known bad template if possible
        template_uuid = list(all_entries.keys())[-1]
        template_bytes = all_entries[template_uuid]
        
        injected_count = 0
        for missing_uuid, snippet in missing_uuids:
            new_entry = create_template_entry(template_bytes, template_uuid, missing_uuid, snippet)
            if new_entry:
                all_entries[missing_uuid] = new_entry
                injected_count += 1
                
        print(f"[SUCCESS] Injected {injected_count} missing recent conversations with custom titles!")
    
    merged_bytes = b"".join(all_entries.values())
    merged_b64 = base64.b64encode(merged_bytes).decode('ascii')
    
    if STATE_DB.exists():
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_path = STATE_DB.parent / f"state.vscdb.pre_ultimate_recover_{timestamp}"
        shutil.copy2(STATE_DB, backup_path)
        
    conn = sqlite3.connect(str(STATE_DB))
    cursor = conn.cursor()
    cursor.execute('SELECT 1 FROM ItemTable WHERE key = ?', (KEY,))
    if cursor.fetchone():
        cursor.execute('UPDATE ItemTable SET value = ? WHERE key = ?', (merged_b64, KEY))
    else:
        cursor.execute('INSERT INTO ItemTable (key, value) VALUES (?, ?)', (KEY, merged_b64))
    conn.commit()
    conn.close()
    
    print(f"\n[SUCCESS] Unified history ({len(all_entries)} total) written to state.vscdb!")

if __name__ == "__main__":
    main()
