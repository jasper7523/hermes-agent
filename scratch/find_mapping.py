import sqlite3, sys, json
sys.stdout.reconfigure(encoding='utf-8')

# Check the implicit store - this might be where conversation-to-workspace is mapped
import os

implicit_dir = r'C:\Users\promy\.gemini\antigravity\implicit'
if os.path.exists(implicit_dir):
    print("=== Implicit directory .pb files ===")
    for f in os.listdir(implicit_dir):
        fpath = os.path.join(implicit_dir, f)
        size = os.path.getsize(fpath)
        print(f"  {f}: {size} bytes")
        
        # Read and search for conversation IDs
        with open(fpath, 'rb') as fp:
            data = fp.read()
        
        # Search for both conversation IDs
        for cid in [b'1a1192d6', b'fa9c7a65', b'hermes-agent', b'hermes_agent']:
            idx = data.find(cid)
            if idx >= 0:
                ctx = data[max(0,idx-30):min(len(data),idx+60)]
                print(f"    FOUND {cid} at offset {idx}: {ctx}")

# Also check conversations directory for any workspace metadata files
conv_dir = r'C:\Users\promy\.gemini\antigravity\conversations'
print("\n=== Conversations directory structure ===")
for f in sorted(os.listdir(conv_dir)):
    fpath = os.path.join(conv_dir, f)
    if os.path.isfile(fpath):
        size = os.path.getsize(fpath)
        ext = os.path.splitext(f)[1]
        if ext != '.pb':
            print(f"  NON-PB FILE: {f}: {size} bytes")
    else:
        print(f"  DIR: {f}")

# Check if there's a context_state directory
ctx_state = r'C:\Users\promy\.gemini\antigravity\context_state'
if os.path.exists(ctx_state):
    print("\n=== context_state directory ===")
    for f in os.listdir(ctx_state):
        fpath = os.path.join(ctx_state, f)
        size = os.path.getsize(fpath) if os.path.isfile(fpath) else 'DIR'
        print(f"  {f}: {size}")
