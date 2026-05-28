import os
import sqlite3
import base64
import sys
import shutil
from datetime import datetime
from pathlib import Path

# Config
APPDATA = Path(os.environ['APPDATA'])
GLOBALSTORE = APPDATA / 'Antigravity IDE' / 'User' / 'globalStorage'
STATE_DB = GLOBALSTORE / 'state.vscdb'
KEY = 'antigravityUnifiedStateSync.trajectorySummaries'

TEMPLATE_UUID = b'ed95ed37-f2bf-450e-9003-e10dbb89ef8c'
TARGET_UUID = b'e4c99172-6a55-4cf0-82b8-e0978d7c6361'

def check_ide_running():
    # Bypass check since Stop-Process is handled by the .bat file
    return False

def main():
    print("=" * 60)
    print("ANTIGRAVITY IDE INJECT CONVERSATION TOOL")
    print("=" * 60)

    if not STATE_DB.exists():
        print(f"[ERROR] Database not found at {STATE_DB}")
        sys.exit(1)

    # 1. Read original
    conn = sqlite3.connect(str(STATE_DB))
    cursor = conn.cursor()
    cursor.execute('SELECT value FROM ItemTable WHERE key = ?', (KEY,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        print("[ERROR] Key trajectorySummaries not found in database.")
        sys.exit(1)

    original_b64 = row[0]
    original_bytes = base64.b64decode(original_b64.encode('ascii') + b'===')

    # 2. Locate template entry
    start_offset = 95957
    entry_length = 1271

    # Safe verification of template block
    template_block = original_bytes[start_offset:start_offset + entry_length]
    if TEMPLATE_UUID not in template_block:
        print("[ERROR] Template UUID not found in the specified block offset.")
        # Search dynamically
        idx = original_bytes.find(TEMPLATE_UUID)
        if idx == -1:
            print("[ERROR] Template UUID not found anywhere in the index!")
            sys.exit(1)
        print(f"[INFO] Dynamic template search found UUID at: {idx}")
        # Re-align start_offset
        prefix_idx = original_bytes.rfind(b'\n$', 0, idx)
        if prefix_idx != -1:
            if original_bytes[prefix_idx-2] == 10: # \n
                start_offset = prefix_idx - 2
            elif original_bytes[prefix_idx-3] == 10: # \n
                start_offset = prefix_idx - 3
            else:
                start_offset = prefix_idx - 3
            
            # Find next entry
            next_entry_idx = -1
            for offset in range(idx + len(TEMPLATE_UUID), len(original_bytes) - 50):
                if original_bytes[offset] == 10: # \n
                    if original_bytes[offset+2] == 10 and original_bytes[offset+3] == 36:
                        next_entry_idx = offset
                        break
                    elif original_bytes[offset+3] == 10 and original_bytes[offset+4] == 36:
                        next_entry_idx = offset
                        break
            if next_entry_idx != -1:
                entry_length = next_entry_idx - start_offset
            else:
                entry_length = len(original_bytes) - start_offset
        print(f"[INFO] Realigned template block: start={start_offset}, length={entry_length}")
        template_block = original_bytes[start_offset:start_offset + entry_length]

    # Verify template block again
    if TEMPLATE_UUID not in template_block:
        print("[ERROR] Failed to align template block.")
        sys.exit(1)

    print(f"[OK] Template block aligned. Start: {start_offset}, Length: {entry_length}")

    # 3. Create target block
    target_block = template_block.replace(TEMPLATE_UUID, TARGET_UUID)
    if TARGET_UUID not in target_block:
        print("[ERROR] Failed to replace UUID in block.")
        sys.exit(1)

    # 4. Merge
    merged_bytes = original_bytes + target_block
    merged_b64 = base64.b64encode(merged_bytes).decode('ascii')

    # 5. Backup database
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_db_path = GLOBALSTORE / f"state.vscdb.pre_inject_{timestamp}"
    shutil.copy2(STATE_DB, backup_db_path)
    print(f"[BACKUP] Database backed up to {backup_db_path.name}")

    # 6. Write back
    conn = sqlite3.connect(str(STATE_DB))
    cursor = conn.cursor()
    cursor.execute('UPDATE ItemTable SET value = ? WHERE key = ?', (merged_b64, KEY))
    conn.commit()
    conn.close()

    print(f"[SUCCESS] Target UUID {TARGET_UUID.decode('ascii')} successfully injected into state.vscdb!")
    print("You can now start Antigravity IDE and check the sidebar.")

if __name__ == "__main__":
    main()
