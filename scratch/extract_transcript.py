#!/usr/bin/env python3
"""Extract readable transcript from e4c99172 conversation."""
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

TRANSCRIPT = Path(r"C:\Users\promy\.gemini\antigravity-ide\brain\e4c99172-6a55-4cf0-82b8-e0978d7c6361\.system_generated\logs\transcript.jsonl")
OUTPUT = Path(r"C:\Users\promy\.gemini\antigravity-ide\brain\ed95ed37-f2bf-450e-9003-e10dbb89ef8c\e4c99172_readable_transcript.md")

lines = TRANSCRIPT.read_text(encoding='utf-8', errors='ignore').splitlines()

out = []
out.append("# 對話 e4c99172 完整紀錄摘要")
out.append(f"**UUID**: `e4c99172-6a55-4cf0-82b8-e0978d7c6361`")
out.append(f"**總步數**: {len(lines)}")
out.append("")

user_count = 0
model_count = 0

for i, line in enumerate(lines):
    try:
        j = json.loads(line)
    except:
        continue

    step = j.get('step_index', '?')
    stype = j.get('type', '')
    ts = j.get('created_at', '')
    content = j.get('content', '')

    if stype == 'USER_INPUT':
        user_count += 1
        # Extract just the user request text
        text = content
        if '<USER_REQUEST>' in text:
            start = text.find('<USER_REQUEST>') + len('<USER_REQUEST>')
            end = text.find('</USER_REQUEST>')
            if end > start:
                text = text[start:end].strip()
        out.append(f"---\n## 👤 使用者訊息 #{user_count} (Step {step}, {ts})\n")
        out.append(text[:1000])
        out.append("")

    elif stype == 'PLANNER_RESPONSE' and content:
        model_count += 1
        out.append(f"## 🤖 模型回覆 #{model_count} (Step {step}, {ts})\n")
        # Truncate very long responses
        if len(content) > 2000:
            out.append(content[:2000] + "\n\n*...（回覆過長，已截斷）...*")
        else:
            out.append(content)
        out.append("")

    elif stype == 'RUN_COMMAND' and content:
        # Show command outputs briefly
        cmd_preview = content[:300]
        out.append(f"<details><summary>🔧 工具執行 (Step {step})</summary>\n\n```\n{cmd_preview}\n```\n</details>\n")

out.append(f"\n---\n**統計**: {user_count} 個使用者訊息, {model_count} 個模型回覆, {len(lines)} 個步驟")

OUTPUT.write_text('\n'.join(out), encoding='utf-8')
print(f"[DONE] Readable transcript written to: {OUTPUT}")
print(f"  User messages: {user_count}")
print(f"  Model responses: {model_count}")
print(f"  Total steps: {len(lines)}")
