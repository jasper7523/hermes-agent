import sqlite3, sys, json
sys.stdout.reconfigure(encoding='utf-8')

# Global state database
db_path = r'C:\Users\promy\AppData\Roaming\Antigravity\User\globalStorage\state.vscdb'

try:
    conn = sqlite3.connect(f'file:{db_path}?mode=ro', uri=True)
    cursor = conn.cursor()
    
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    print('Tables:', [t[0] for t in tables])
    
    for table in tables:
        tname = table[0]
        cursor.execute(f'SELECT COUNT(*) FROM {tname}')
        count = cursor.fetchone()[0]
        print(f'\nTable {tname}: {count} rows')
        
        # Get all keys
        cursor.execute(f'SELECT key FROM {tname}')
        all_keys = [r[0] for r in cursor.fetchall()]
        
        # Find conversation/chat related keys
        for key in all_keys:
            if any(term in key.lower() for term in ['conversation', 'chat', 'session', 'history', 'agent']):
                cursor.execute(f'SELECT value FROM {tname} WHERE key = ?', (key,))
                val = cursor.fetchone()
                if val:
                    val_str = val[0] if isinstance(val[0], str) else val[0].decode('utf-8', errors='replace')
                    # Check if it contains the conversation ID
                    has_missing = '1a1192d6' in val_str
                    has_visible = 'fa9c7a65' in val_str
                    print(f'\n  KEY: {key}')
                    print(f'    Length: {len(val_str)} chars')
                    print(f'    Contains 1a1192d6 (missing): {has_missing}')
                    print(f'    Contains fa9c7a65 (visible): {has_visible}')
                    if has_missing or has_visible:
                        # Find the context around the ID
                        for cid in ['1a1192d6', 'fa9c7a65']:
                            idx = val_str.find(cid)
                            if idx >= 0:
                                start = max(0, idx - 50)
                                end = min(len(val_str), idx + 80)
                                print(f'    Context for {cid}: ...{val_str[start:end]}...')
    
    conn.close()
except Exception as e:
    print(f'Error: {e}')
