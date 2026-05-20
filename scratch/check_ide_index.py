#!/usr/bin/env python3
"""Check the agyhub_summaries_proto.pb index file metadata and the implicit directory."""
import os, time

pb = r'C:\Users\promy\.gemini\antigravity-ide\agyhub_summaries_proto.pb'
stat = os.stat(pb)
fmt = "%Y-%m-%d %H:%M:%S"
print(f"agyhub_summaries_proto.pb")
print(f"  Size: {stat.st_size} bytes")
print(f"  Last modified: {time.strftime(fmt, time.localtime(stat.st_mtime))}")

# Check the implicit directory
implicit_dir = r'C:\Users\promy\.gemini\antigravity-ide\implicit'
if os.path.isdir(implicit_dir):
    print(f"\nimplicit/ directory contents:")
    for item in sorted(os.listdir(implicit_dir)):
        full = os.path.join(implicit_dir, item)
        if os.path.isfile(full):
            s = os.stat(full)
            print(f"  {item}  ({s.st_size} bytes, modified: {time.strftime(fmt, time.localtime(s.st_mtime))})")
        elif os.path.isdir(full):
            count = len(os.listdir(full))
            print(f"  {item}/  ({count} items)")

# Check backup dir
backup_dir = r'C:\Users\promy\.gemini\antigravity-ide\backup_20260520'
if os.path.isdir(backup_dir):
    print(f"\nbackup_20260520/ directory (top-level items):")
    for item in sorted(os.listdir(backup_dir))[:10]:
        full = os.path.join(backup_dir, item)
        if os.path.isfile(full):
            print(f"  {item}  ({os.path.getsize(full)} bytes)")
        elif os.path.isdir(full):
            print(f"  {item}/")
