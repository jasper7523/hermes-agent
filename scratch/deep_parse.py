#!/usr/bin/env python3
"""Deeply analyze the aebe795c entry structure to reverse-engineer the exact protobuf schema for cloning."""
import sqlite3
import base64
import os

STATE_DB = os.path.join(os.environ["APPDATA"], "Antigravity IDE", "User", "globalStorage", "state.vscdb")

conn = sqlite3.connect(STATE_DB)
cur = conn.cursor()
cur.execute("SELECT value FROM ItemTable WHERE key=?", ("antigravityUnifiedStateSync.trajectorySummaries",))
raw_b64 = cur.fetchone()[0]
conn.close()

decoded = base64.b64decode(raw_b64)

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

def parse_fields(data, indent=0):
    """Recursively parse protobuf fields."""
    prefix = "  " * indent
    pos = 0
    while pos < len(data):
        try:
            tag, new_pos = decode_varint(data, pos)
        except:
            break
        fn = tag >> 3
        wt = tag & 7
        if wt == 2:  # length-delimited
            length, new_pos = decode_varint(data, new_pos)
            content = data[new_pos:new_pos+length]
            new_pos += length
            try:
                text = content.decode('utf-8', errors='strict')
                # Check if it looks like base64
                if len(text) > 10 and all(c in 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=' for c in text):
                    try:
                        inner = base64.b64decode(text)
                        print(f"{prefix}Field {fn} (LEN/b64): {len(text)} chars -> {len(inner)} bytes decoded")
                        parse_fields(inner, indent+1)
                    except:
                        print(f"{prefix}Field {fn} (LEN/str): {repr(text[:80])}{'...' if len(text) > 80 else ''}")
                else:
                    print(f"{prefix}Field {fn} (LEN/str): {repr(text[:80])}{'...' if len(text) > 80 else ''}")
            except UnicodeDecodeError:
                # Try to parse as nested protobuf
                print(f"{prefix}Field {fn} (LEN/pb): {length} bytes")
                parse_fields(content, indent+1)
        elif wt == 0:  # varint
            v, new_pos = decode_varint(data, new_pos)
            print(f"{prefix}Field {fn} (VAR): {v}")
        elif wt == 1:
            new_pos += 8
            print(f"{prefix}Field {fn} (64bit)")
        elif wt == 5:
            new_pos += 4
            print(f"{prefix}Field {fn} (32bit)")
        else:
            print(f"{prefix}Field {fn} (wt={wt}) unknown")
            break
        pos = new_pos

# Find aebe795c entry
pos = 0
entry_count = 0
while pos < len(decoded):
    entry_start = pos
    tag, pos = decode_varint(decoded, pos)
    if (tag & 7) != 2:
        break
    length, pos = decode_varint(decoded, pos)
    entry_data = decoded[pos:pos+length]
    pos += length
    
    if b'aebe795c' in entry_data:
        print(f"=== Entry {entry_count}: aebe795c (length={length}) ===")
        parse_fields(entry_data)
        print()
    
    # Also show entry 0 for comparison (old .pb format)
    if entry_count == 0:
        print(f"=== Entry 0: (old .pb format, length={length}) ===")
        parse_fields(entry_data)
        print()
    
    entry_count += 1
