import sqlite3, sys, json
sys.stdout.reconfigure(encoding='utf-8')

db_path = r'C:\Users\promy\AppData\Roaming\Antigravity\User\globalStorage\state.vscdb'
conn = sqlite3.connect(f'file:{db_path}?mode=ro', uri=True)
cursor = conn.cursor()

# Dump key Antigravity state entries
keys_to_check = [
    'jetskiStateSync.agentManagerInitState',
    'antigravityUnifiedStateSync.agentManagerWindow',
    'antigravityUnifiedStateSync.agentPreferences',
]

for key in keys_to_check:
    cursor.execute("SELECT value FROM ItemTable WHERE key = ?", (key,))
    row = cursor.fetchone()
    if row:
        val = row[0]
        print(f'\n=== {key} ({len(val)} chars) ===')
        try:
            parsed = json.loads(val)
            print(json.dumps(parsed, indent=2, ensure_ascii=False)[:2000])
        except:
            print(val[:2000])

# Also search ALL keys for any conversation ID
cursor.execute("SELECT key, value FROM ItemTable")
for key, val in cursor.fetchall():
    if isinstance(val, str) and ('1a1192d6' in val or 'fa9c7a65' in val):
        print(f'\n*** FOUND conversation ID in key: {key} ***')
        idx = val.find('1a1192d6') if '1a1192d6' in val else val.find('fa9c7a65')
        print(f'Context: {val[max(0,idx-100):idx+100]}')

conn.close()
