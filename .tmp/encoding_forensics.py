#!/usr/bin/env python3
"""N7 Encoding Forensics - Deep analysis of batch_9 corruption."""
import os, sys

sys.stdout.reconfigure(encoding='utf-8')

BASE = r'D:\Agent_Hub\agents\Book_Writer_Agent\data\workspace\book\ch 1.4\.tmp\batch_9'
OUT = []

def analyze_file(filepath, label):
    OUT.append(f'=== {label}: {os.path.basename(filepath)} ===')
    raw = open(filepath, 'rb').read()
    OUT.append(f'File size: {len(raw)} bytes')
    OUT.append(f'First 8 bytes hex: {raw[:8].hex(" ")}')
    
    # Detect BOM
    if raw[:3] == b'\xef\xbb\xbf':
        OUT.append('BOM: UTF-8 BOM detected (EF BB BF)')
        body = raw[3:]
        encoding = 'utf-8'
    elif raw[:2] == b'\xff\xfe':
        OUT.append('BOM: UTF-16LE BOM detected (FF FE)')
        body = raw[2:]
        encoding = 'utf-16-le'
    else:
        OUT.append('BOM: None detected')
        body = raw
        encoding = 'utf-8'
    
    # Decode
    text = body.decode(encoding, errors='replace')
    OUT.append(f'Decoded length: {len(text)} chars')
    
    # Character analysis
    cjk_standard = 0  # U+4E00-9FFF
    cjk_ext = 0       # CJK extensions
    pua = 0            # U+E000-F8FF (Private Use Area - corruption indicator!)
    ascii_printable = 0
    replacement = 0    # U+FFFD
    question_mark = 0  # ? that might be replacement
    whitespace = 0
    other = 0
    
    for c in text:
        cp = ord(c)
        if 0x4E00 <= cp <= 0x9FFF:
            cjk_standard += 1
        elif 0xE000 <= cp <= 0xF8FF:
            pua += 1
        elif 0x20 <= cp <= 0x7E:
            if c == '?':
                question_mark += 1
            else:
                ascii_printable += 1
        elif cp == 0xFFFD:
            replacement += 1
        elif c in '\r\n\t':
            whitespace += 1
        else:
            other += 1
    
    total = len(text)
    OUT.append(f'')
    OUT.append(f'CHARACTER DISTRIBUTION (first {total} chars):')
    OUT.append(f'  CJK standard (U+4E00-9FFF): {cjk_standard} ({cjk_standard/max(total,1)*100:.1f}%)')
    OUT.append(f'  Private Use Area (U+E000-F8FF): {pua} ({pua/max(total,1)*100:.1f}%) *** CORRUPTION INDICATOR ***')
    OUT.append(f'  ASCII printable: {ascii_printable} ({ascii_printable/max(total,1)*100:.1f}%)')
    OUT.append(f'  Question marks (?): {question_mark} ({question_mark/max(total,1)*100:.1f}%)')
    OUT.append(f'  Replacement char (U+FFFD): {replacement}')
    OUT.append(f'  Whitespace: {whitespace}')
    OUT.append(f'  Other: {other}')
    
    # Diagnosis
    OUT.append(f'')
    if pua > 50:
        OUT.append(f'DIAGNOSIS: SEVERE DOUBLE-ENCODING CORRUPTION')
        OUT.append(f'  {pua} characters fall in Private Use Area.')
        OUT.append(f'  This indicates UTF-8 text was misread as Big5/CP950,')
        OUT.append(f'  then re-encoded to UTF-8/UTF-16, creating gibberish')
        OUT.append(f'  in the PUA range. DATA IS IRRECOVERABLE.')
    elif replacement > 50:
        OUT.append(f'DIAGNOSIS: ENCODING MISMATCH (replacement chars)')
    elif question_mark > total * 0.05:
        OUT.append(f'DIAGNOSIS: POSSIBLE ENCODING LOSS (excessive ?)')
    else:
        OUT.append(f'DIAGNOSIS: File appears clean')
    
    OUT.append('')

# Analyze all txt files
for fname in sorted(os.listdir(BASE)):
    if fname.endswith('.txt') and fname != 'n7_analysis.txt' and fname != 'n7_deep.txt':
        analyze_file(os.path.join(BASE, fname), 'FORENSICS')

# Also check if source .md chunks exist
OUT.append('=== SOURCE CHUNK FILES (.md) ===')
md_files = [f for f in os.listdir(BASE) if f.endswith('.md')]
if md_files:
    for mf in sorted(md_files):
        fp = os.path.join(BASE, mf)
        raw = open(fp, 'rb').read()
        OUT.append(f'  {mf}: {len(raw)} bytes, BOM={raw[:3].hex()}')
        # Quick PUA check
        text = raw.decode('utf-8', errors='replace')
        pua_count = sum(1 for c in text[:2000] if 0xE000 <= ord(c) <= 0xF8FF)
        OUT.append(f'    PUA in first 2000 chars: {pua_count}')
else:
    OUT.append('  No .md chunk files found in batch_9/')

# Also check doc16.txt
doc16_path = os.path.join(BASE, 'doc16.txt')
if os.path.exists(doc16_path):
    OUT.append('')
    OUT.append('=== doc16.txt (source document) ===')
    raw = open(doc16_path, 'rb').read()
    OUT.append(f'Size: {len(raw)} bytes')
    OUT.append(f'First 4 bytes hex: {raw[:4].hex(" ")}')
    if raw[:3] == b'\xef\xbb\xbf':
        text = raw[3:].decode('utf-8', errors='replace')
        enc = 'UTF-8 BOM'
    elif raw[:2] == b'\xff\xfe':
        text = raw[2:].decode('utf-16-le', errors='replace')
        enc = 'UTF-16LE BOM'
    else:
        text = raw.decode('utf-8', errors='replace')
        enc = 'No BOM (assumed UTF-8)'
    
    OUT.append(f'Detected encoding: {enc}')
    pua_doc = sum(1 for c in text[:5000] if 0xE000 <= ord(c) <= 0xF8FF)
    repl_doc = sum(1 for c in text if ord(c) == 0xFFFD)
    OUT.append(f'PUA in first 5000 chars: {pua_doc}')
    OUT.append(f'Replacement chars total: {repl_doc}')
    OUT.append(f'First 200 chars: {repr(text[:200])}')

# Write report
report_path = os.path.join(BASE, 'n7_forensics_report.txt')
with open(report_path, 'w', encoding='utf-8') as f:
    f.write('\n'.join(OUT))
print(f'Report written to {report_path}')
