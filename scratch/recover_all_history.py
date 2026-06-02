import sqlite3
import base64
import os
import sys
import glob
import re
import shutil
from datetime import datetime
from pathlib import Path

# Config
APPDATA = Path(os.environ['APPDATA'])
GLOBALSTORE = APPDATA / 'Antigravity IDE' / 'User' / 'globalStorage'
STATE_DB = GLOBALSTORE / 'state.vscdb'
KEY = 'antigravityUnifiedStateSync.trajectorySummaries'
PB_DIR = Path(os.environ['USERPROFILE']) / '.gemini' / 'antigravity-ide'

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
                # Top level fields must be length delimited. If not, this is likely corrupt data or we lost sync.
                break
                
            length, pos = decode_varint(decoded_bytes, pos)
            if pos + length > len(decoded_bytes):
                break # corrupted chunk
                
            entry_data = decoded_bytes[pos:pos+length]
            full_entry_bytes = decoded_bytes[start_pos:pos+length]
            pos += length
            
            # Find UUID via regex
            entry_str = entry_data.decode('utf-8', errors='ignore')
            match = re.search(r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}', entry_str)
            if match:
                uuid = match.group()
                entries[uuid] = full_entry_bytes
        except Exception as e:
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
    except Exception as e:
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

def main():
    print("============================================================")
    print("  ULTIMATE ANTIGRAVITY IDE HISTORY RECOVERY")
    print("============================================================")
    
    if check_ide_running():
        print("[ERROR] IDE is running. Please close it first.")
        sys.exit(1)

    files = []
    
    # 1a. vscdb backups
    for f in glob.glob(str(GLOBALSTORE / 'state.vscdb*')):
        files.append(Path(f))
        
    # 1b. PB index backups (only specific summary files, not individual conversations!)
    for pb in PB_DIR.rglob("agyhub_summaries_proto*.pb"):
        files.append(pb)
        
    files.sort(key=lambda x: x.stat().st_mtime)
    print(f"Found {len(files)} potential sources of history.")
    
    all_entries = {}
    source_stats = {}
    
    for f in files:
        payload = None
        if f.suffix == ".pb":
            payload = f.read_bytes()
        else:
            payload = get_vscdb_payload(f)
            
        if payload:
            entries = parse_entries(payload, f.name)
            if entries:
                added = 0
                for u, b in entries.items():
                    if u not in all_entries:
                        added += 1
                    all_entries[u] = b
                source_stats[f.name] = (len(entries), added)
                print(f"Read {f.name:45s}: {len(entries):4d} entries (+{added} new)")
                
    print("\n------------------------------------------------------------")
    print(f"Total Unique Conversations Recovered: {len(all_entries)}")
    print("------------------------------------------------------------\n")
    
    if not all_entries:
        print("[ERROR] No history found to recover!")
        sys.exit(1)
        
    merged_bytes = b"".join(all_entries.values())
    merged_b64 = base64.b64encode(merged_bytes).decode('ascii')
    
    if STATE_DB.exists():
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_path = STATE_DB.parent / f"state.vscdb.pre_ultimate_recover_{timestamp}"
        shutil.copy2(STATE_DB, backup_path)
        print(f"[BACKUP] Current DB saved to {backup_path.name}")
        
    conn = sqlite3.connect(str(STATE_DB))
    cursor = conn.cursor()
    cursor.execute('SELECT 1 FROM ItemTable WHERE key = ?', (KEY,))
    if cursor.fetchone():
        cursor.execute('UPDATE ItemTable SET value = ? WHERE key = ?', (merged_b64, KEY))
    else:
        cursor.execute('INSERT INTO ItemTable (key, value) VALUES (?, ?)', (KEY, merged_b64))
    conn.commit()
    conn.close()
    
    print("\n[SUCCESS] Unified history successfully written to state.vscdb!")

if __name__ == "__main__":
    main()
