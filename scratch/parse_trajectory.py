#!/usr/bin/env python3
"""Parse trajectorySummaries protobuf to understand entry structure and find the aebe795c entry."""
import sqlite3
import base64

db = r"C:\Users\promy\AppData\Roaming\Antigravity IDE\User\globalStorage\state.vscdb"
conn = sqlite3.connect(db)
c = conn.cursor()
c.execute("SELECT value FROM ItemTable WHERE key=?", ("antigravityUnifiedStateSync.trajectorySummaries",))
val = c.fetchone()[0]
conn.close()

decoded = base64.b64decode(val)
print(f"Decoded: {len(decoded)} bytes")

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

# Parse top-level entries
pos = 0
entries = []
while pos < len(decoded):
    tag, pos = decode_varint(decoded, pos)
    field_num = tag >> 3
    wire_type = tag & 7
    
    if wire_type != 2:
        break
    
    length, pos = decode_varint(decoded, pos)
    entry_data = decoded[pos:pos+length]
    pos += length
    
    # Try to find UUID in entry
    uuid = None
    try:
        entry_str = entry_data.decode('utf-8', errors='ignore')
        import re
        match = re.search(r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}', entry_str)
        if match:
            uuid = match.group()
    except:
        pass
    
    entries.append({
        'field_num': field_num,
        'length': length,
        'uuid': uuid,
        'data': entry_data,
    })

print(f"Total top-level entries: {len(entries)}")

# Find the aebe795c entry and show its structure  
target_uuids = ['aebe795c-466d-47e9-bed5-70aadbcc822d', 'f7241b8b-c1c8-486e-a1e0-f070be6b4268']
for target in target_uuids:
    for i, e in enumerate(entries):
        if e['uuid'] and target[:8] in e['uuid']:
            print(f"\n{'='*60}")
            print(f"Entry #{i}: UUID={e['uuid']}")
            print(f"  Field num: {e['field_num']}, Length: {e['length']}")
            print(f"  Hex (first 200): {e['data'][:200].hex()}")
            
            # Parse inner fields
            ep = 0
            data = e['data']
            while ep < len(data):
                try:
                    t, ep = decode_varint(data, ep)
                    fn = t >> 3
                    wt = t & 7
                    if wt == 2:
                        l, ep = decode_varint(data, ep)
                        content = data[ep:ep+l]
                        ep += l
                        try:
                            text = content.decode('utf-8', errors='strict')
                            if len(text) < 200:
                                print(f"  Field {fn} (LEN): {repr(text)}")
                            else:
                                print(f"  Field {fn} (LEN): {repr(text[:100])}... ({len(text)} chars)")
                        except:
                            print(f"  Field {fn} (LEN): <{len(content)} bytes binary>")
                    elif wt == 0:
                        v, ep = decode_varint(data, ep)
                        print(f"  Field {fn} (VAR): {v}")
                    elif wt == 1:
                        ep += 8
                        print(f"  Field {fn} (64b)")
                    elif wt == 5:
                        ep += 4
                        print(f"  Field {fn} (32b)")
                    else:
                        print(f"  Field {fn} (wt={wt}) - unknown, breaking")
                        break
                except Exception as ex:
                    print(f"  Parse error at {ep}: {ex}")
                    break
            break
