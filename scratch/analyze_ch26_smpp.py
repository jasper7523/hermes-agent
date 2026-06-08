"""Check if Ch2.6 used SMPP at all."""
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

cid = "22567875-d234-47b8-9055-5fc2a7418581"
log_path = Path(r"C:\Users\promy\.gemini\antigravity-ide\brain") / cid / ".system_generated" / "logs" / "transcript.jsonl"

steps = []
with open(log_path, "r", encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if line:
            try:
                steps.append(json.loads(line))
            except json.JSONDecodeError:
                pass

# Check ALL steps for session_load or SMPP mentions
print("=== Ch2.6 SMPP/Memory Analysis ===")
for s in steps:
    full = json.dumps(s, ensure_ascii=False)
    if any(kw in full.lower() for kw in ["session_load", "smpp", "session memory", "session_save"]):
        print(f"\nStep {s['step_index']} [{s['type']}]:")
        print(s.get("content", "")[:300])
        print("---")

# Check for RUN_COMMAND
print("\n=== ALL RUN_COMMAND steps ===")
for s in steps:
    if s.get("type") == "RUN_COMMAND":
        print(f"\nStep {s['step_index']}: {s.get('content', '')[:400]}")

# Check the conversation_history step for rules/user_rules
print("\n=== CONVERSATION_HISTORY (rules check) ===")
for s in steps:
    if s.get("type") == "CONVERSATION_HISTORY":
        content = s.get("content", "")
        # Check if it mentions N5 or Book_Writer
        if "N5" in content or "Book_Writer" in content or "SMPP" in content:
            print(f"\nStep {s['step_index']}: Contains N5/Book_Writer/SMPP refs")
            # Find SMPP context
            if "SMPP" in content:
                idx = content.index("SMPP")
                print(f"  SMPP context: ...{content[max(0,idx-100):idx+200]}...")
        else:
            print(f"\nStep {s['step_index']}: No N5/Book_Writer/SMPP mentions (length: {len(content)})")

# Check the user_rules section
print("\n=== USER_RULES presence check ===")
for s in steps:
    content = s.get("content", "")
    if "hermes-agent" in content.lower() or "book_writer" in content.lower():
        if s.get("type") not in ["VIEW_FILE", "CODE_ACTION"]:
            t = s.get("type", "?")
            idx = s.get("step_index", "?")
            mentions = []
            if "hermes-agent" in content.lower(): mentions.append("hermes-agent")
            if "book_writer" in content.lower(): mentions.append("book_writer")
            if "hard-gate" in content.lower(): mentions.append("hard-gate")
            print(f"  Step {idx} [{t}]: mentions {mentions}")
