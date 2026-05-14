import sqlite3, sys, json
sys.stdout.reconfigure(encoding='utf-8')

db_path = r'C:\Users\promy\AppData\Roaming\Antigravity\User\workspaceStorage\60d3355b4fb31435e444fe86ea6c1f5e\state.vscdb'

try:
    conn = sqlite3.connect(f'file:{db_path}?mode=ro', uri=True)
    cursor = conn.cursor()
    
    # List all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    print('Tables:', [t[0] for t in tables])
    
    # Check each table schema and find conversation-related keys
    for table in tables:
        tname = table[0]
        cursor.execute(f'PRAGMA table_info({tname})')
        cols = cursor.fetchall()
        col_names = [c[1] for c in cols]
        print(f'\nTable {tname}: {col_names}')
        
        cursor.execute(f'SELECT COUNT(*) FROM {tname}')
        count = cursor.fetchone()[0]
        print(f'  Rows: {count}')
        
        # Show all keys (usually not that many in vscdb)
        if 'key' in col_names:
            cursor.execute(f'SELECT key FROM {tname} LIMIT 50')
            keys = [r[0] for r in cursor.fetchall()]
            print(f'  Keys: {keys}')
            
            # Search for conversation-related keys
            for key in keys:
                if any(term in key.lower() for term in ['conversation', 'chat', 'history', '1a1192d6', 'session']):
                    cursor.execute(f'SELECT value FROM {tname} WHERE key = ?', (key,))
                    val = cursor.fetchone()
                    if val:
                        val_str = val[0] if isinstance(val[0], str) else str(val[0][:200])
                        print(f'  >>> {key}: {val_str[:300]}')
    
    conn.close()
except Exception as e:
    print(f'Error: {e}')
