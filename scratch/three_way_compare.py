#!/usr/bin/env python3
"""三方比對：antigravity-ide vs antigravity vs antigravity-backup，找出最完整的版本。"""
import os, sys, time
sys.stdout.reconfigure(encoding='utf-8')

dirs = {
    'ide': os.path.expanduser(r'~\.gemini\antigravity-ide'),
    'ag2': os.path.expanduser(r'~\.gemini\antigravity'),
    'bak': os.path.expanduser(r'~\.gemini\antigravity-backup'),
}

def scan_conversations(base):
    convos = {}
    conv_dir = os.path.join(base, 'conversations')
    if not os.path.isdir(conv_dir):
        return convos
    for f in os.listdir(conv_dir):
        if f.endswith(('.pb', '.db')):
            full = os.path.join(conv_dir, f)
            stat = os.stat(full)
            convos[f] = {
                'size': stat.st_size,
                'mtime': stat.st_mtime,
                'mtime_str': time.strftime('%m-%d %H:%M', time.localtime(stat.st_mtime)),
            }
    return convos

def scan_brains(base):
    brains = {}
    brain_dir = os.path.join(base, 'brain')
    if not os.path.isdir(brain_dir):
        return brains
    for d in os.listdir(brain_dir):
        full = os.path.join(brain_dir, d)
        if os.path.isdir(full):
            total_size = sum(
                os.path.getsize(os.path.join(dp, f))
                for dp, _, fns in os.walk(full)
                for f in fns
            )
            file_count = sum(len(fns) for _, _, fns in os.walk(full))
            brains[d] = {'size': total_size, 'files': file_count}
    return brains

# Scan all three
print("=" * 70)
print("  三方對話比對")
print("=" * 70)

all_convos = {name: scan_conversations(path) for name, path in dirs.items()}
all_brains = {name: scan_brains(path) for name, path in dirs.items()}

# Find all unique conversation files
all_files = set()
for convos in all_convos.values():
    all_files.update(convos.keys())

# Categorize
print(f"\n[1] 對話檔案總覽:")
print(f"  IDE: {len(all_convos['ide'])} files")
print(f"  AG2: {len(all_convos['ag2'])} files")
print(f"  BAK: {len(all_convos['bak'])} files")
print(f"  不重複總計: {len(all_files)} files")

# Find files only in one source
print(f"\n[2] 獨有檔案:")
for name in ['ide', 'ag2', 'bak']:
    others = [n for n in ['ide', 'ag2', 'bak'] if n != name]
    unique = set(all_convos[name].keys())
    for other in others:
        unique -= set(all_convos[other].keys())
    if unique:
        for f in sorted(unique):
            info = all_convos[name][f]
            print(f"  [{name} only] {f} ({info['size']} bytes, {info['mtime_str']})")

# Find files with different sizes/mtimes across sources
print(f"\n[3] 版本差異 (同名但大小不同):")
diff_count = 0
for f in sorted(all_files):
    sources = {name: all_convos[name][f] for name in ['ide', 'ag2', 'bak'] if f in all_convos[name]}
    if len(sources) > 1:
        sizes = set(s['size'] for s in sources.values())
        if len(sizes) > 1:
            diff_count += 1
            if diff_count <= 10:  # Only show first 10
                best_name = max(sources.keys(), key=lambda n: sources[n]['mtime'])
                parts = []
                for name, info in sorted(sources.items()):
                    marker = " ★" if name == best_name else ""
                    parts.append(f"{name}={info['size']}b/{info['mtime_str']}{marker}")
                print(f"  {f}: {' | '.join(parts)}")

if diff_count > 10:
    print(f"  ... +{diff_count-10} more")
elif diff_count == 0:
    print(f"  (無差異)")

# Brain comparison
print(f"\n[4] Brain 目錄總覽:")
all_brain_ids = set()
for brains in all_brains.values():
    all_brain_ids.update(brains.keys())

print(f"  IDE: {len(all_brains['ide'])} dirs")
print(f"  AG2: {len(all_brains['ag2'])} dirs")
print(f"  BAK: {len(all_brains['bak'])} dirs")
print(f"  不重複總計: {len(all_brain_ids)} dirs")

# Unique brains
for name in ['ide', 'ag2', 'bak']:
    others = [n for n in ['ide', 'ag2', 'bak'] if n != name]
    unique = set(all_brains[name].keys())
    for other in others:
        unique -= set(all_brains[other].keys())
    if unique:
        for d in sorted(unique):
            info = all_brains[name][d]
            print(f"  [{name} only] brain/{d[:12]}... ({info['files']} files, {info['size']} bytes)")

# Summary: what the canonical store should look like
print(f"\n[5] Canonical Store 應有內容 (三方聯集):")
total_pb = len([f for f in all_files if f.endswith('.pb')])
total_db = len([f for f in all_files if f.endswith('.db')])
print(f"  conversations: {total_pb} .pb + {total_db} .db = {len(all_files)} total")
print(f"  brain: {len(all_brain_ids)} dirs")

# For files existing in multiple sources, pick the newest
print(f"\n[6] 合併策略 (每個檔案取最新版):")
merge_plan = {}
for f in sorted(all_files):
    sources = {name: all_convos[name][f] for name in ['ide', 'ag2', 'bak'] if f in all_convos[name]}
    best_name = max(sources.keys(), key=lambda n: sources[n]['mtime'])
    merge_plan[f] = best_name

from collections import Counter
source_counts = Counter(merge_plan.values())
for name, count in sorted(source_counts.items()):
    print(f"  從 {name} 取: {count} files")
