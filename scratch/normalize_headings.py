"""
P2 歷史債務修復腳本：統一 literature_review 標題層級
規則：
  - 文獻標題 → ### (H3)
  - 六維度標題 → #### (H4)

偵測邏輯：
  - 文獻標題：行首 # 後面跟著 [數字] 或 數字. 且包含 .pdf 或 Part
  - 六維度標題：行首 # 後面跟著 數字. 且包含白名單關鍵字
"""
import re
import sys
import shutil
from pathlib import Path

# 六維度白名單關鍵字（用於判斷該行是「維度標題」而非「文獻標題」）
DIMENSION_KEYWORDS = [
    "核心論點", "Core Argument",
    "支援論述", "Supporting Evidence",
    "反證論述", "Contradictory Evidence",
    "關鍵段落", "Key Paragraphs",
    "學術語境", "Contextual Rewrite", "Professional Contextual Rewrite",
    "精確註腳", "Citation",
]

# 文獻標題特徵（包含檔名或 Part 標記）
LITERATURE_PATTERNS = [
    r'\.pdf',
    r'Part\s+\d+',
]

def classify_heading(line_stripped):
    """判斷一行標題是文獻標題還是維度標題，回傳 'literature' | 'dimension' | None"""
    # 先確認是標題行
    m = re.match(r'^(#{2,6})\s+(.*)', line_stripped)
    if not m:
        return None, None, None
    
    hashes = m.group(1)
    content = m.group(2)
    
    # 檢查是否為維度標題
    for kw in DIMENSION_KEYWORDS:
        if kw in content:
            return 'dimension', hashes, content
    
    # 檢查是否為文獻標題
    for pat in LITERATURE_PATTERNS:
        if re.search(pat, content, re.IGNORECASE):
            return 'literature', hashes, content
    
    # 無法分類 - 可能是其他標題（如 ## 1. CG_and_carbon...）
    # 檢查是否包含編號格式
    if re.match(r'^\[?\d+\]?[\.\s]', content):
        return 'literature', hashes, content
    
    return 'unknown', hashes, content

def normalize_file(filepath, dry_run=False):
    path = Path(filepath)
    if not path.exists():
        print(f"ERROR: File not found: {filepath}")
        return
    
    content = path.read_text(encoding='utf-8')
    lines = content.split('\n')
    
    changes = []
    new_lines = []
    
    for i, line in enumerate(lines):
        line_stripped = line.rstrip('\r')
        category, old_hashes, heading_content = classify_heading(line_stripped)
        
        if category == 'literature':
            target_hashes = '###'
            if old_hashes != target_hashes:
                new_line = f"{target_hashes} {heading_content}"
                if line.endswith('\r'):
                    new_line += '\r'
                changes.append({
                    'line': i + 1,
                    'type': 'literature',
                    'from': old_hashes,
                    'to': target_hashes,
                    'content': heading_content[:60]
                })
                new_lines.append(new_line)
            else:
                new_lines.append(line)
        elif category == 'dimension':
            target_hashes = '####'
            if old_hashes != target_hashes:
                new_line = f"{target_hashes} {heading_content}"
                if line.endswith('\r'):
                    new_line += '\r'
                changes.append({
                    'line': i + 1,
                    'type': 'dimension',
                    'from': old_hashes,
                    'to': target_hashes,
                    'content': heading_content[:60]
                })
                new_lines.append(new_line)
            else:
                new_lines.append(line)
        elif category == 'unknown':
            changes.append({
                'line': i + 1,
                'type': 'UNKNOWN',
                'from': old_hashes,
                'to': '???',
                'content': heading_content[:60]
            })
            new_lines.append(line)
        else:
            new_lines.append(line)
    
    # 報告
    print(f"\n{'='*60}")
    print(f"FILE: {path.name}")
    print(f"{'='*60}")
    
    lit_fixes = [c for c in changes if c['type'] == 'literature' and c['from'] != c['to']]
    dim_fixes = [c for c in changes if c['type'] == 'dimension' and c['from'] != c['to']]
    unknowns = [c for c in changes if c['type'] == 'UNKNOWN']
    
    print(f"Literature title fixes: {len(lit_fixes)}")
    for c in lit_fixes:
        print(f"  L{c['line']:4d}: {c['from']} -> {c['to']} | {c['content']}")
    
    print(f"Dimension title fixes:  {len(dim_fixes)}")
    for c in dim_fixes:
        print(f"  L{c['line']:4d}: {c['from']} -> {c['to']} | {c['content']}")
    
    if unknowns:
        print(f"UNKNOWN headings:       {len(unknowns)}")
        for c in unknowns:
            print(f"  L{c['line']:4d}: {c['from']}       | {c['content']}")
    
    total_fixes = len(lit_fixes) + len(dim_fixes)
    print(f"Total changes: {total_fixes}")
    
    if not dry_run and total_fixes > 0:
        # 備份
        backup_path = path.with_suffix('.md.bak')
        shutil.copy2(path, backup_path)
        print(f"Backup saved: {backup_path.name}")
        
        # 寫入
        new_content = '\n'.join(new_lines)
        path.write_text(new_content, encoding='utf-8')
        print(f"File updated successfully.")
    elif dry_run:
        print(f"[DRY RUN] No changes written.")
    else:
        print(f"No changes needed.")

if __name__ == '__main__':
    mode = sys.argv[1] if len(sys.argv) > 1 else 'dry-run'
    
    files = [
        r"d:\Agent_Hub\agents\Book_Writer_Agent\data\workspace\book\ch 2.2\literature_review_1.md",
        r"d:\Agent_Hub\agents\Book_Writer_Agent\data\workspace\book\ch 2.2\literature_review_2.md",
    ]
    
    dry_run = (mode != 'apply')
    
    if dry_run:
        print("MODE: DRY RUN (pass 'apply' to write changes)")
    else:
        print("MODE: APPLY (writing changes to files)")
    
    for f in files:
        normalize_file(f, dry_run=dry_run)
