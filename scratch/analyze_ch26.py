"""Ch2.6 success analysis only."""
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

BASE = Path(r"C:\Users\promy\.gemini\antigravity-ide\brain")
cid = "22567875-d234-47b8-9055-5fc2a7418581"
log_path = BASE / cid / ".system_generated" / "logs" / "transcript.jsonl"

steps = []
with open(log_path, "r", encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if line:
            try:
                steps.append(json.loads(line))
            except json.JSONDecodeError:
                pass

print(f"=== Ch2.6 SUCCESS ===")
print(f"Total steps: {len(steps)}")

# Step types
type_counts = {}
for s in steps:
    t = s.get("type", "UNKNOWN")
    type_counts[t] = type_counts.get(t, 0) + 1
print(f"Step types: {json.dumps(type_counts, indent=2, ensure_ascii=False)}")

# session_load
for s in steps:
    content = s.get("content", "")
    if "session_load" in content:
        print(f"\n[SMPP] Step {s.get('step_index')} [{s.get('type')}]: {content[:300]}")

# USER_INPUT
for s in steps:
    if s.get("type") == "USER_INPUT":
        content = s.get("content", "")
        if "<USER_REQUEST>" in content:
            req = content.split("<USER_REQUEST>")[1]
            if "</USER_REQUEST>" in req:
                req = req.split("</USER_REQUEST>")[0]
            print(f"\n[USER] Step {s.get('step_index')}: {req[:400]}")

# Files read
view_files = []
for s in steps:
    if s.get("type") == "VIEW_FILE" and s.get("status") == "DONE":
        content = s.get("content", "")
        if "File Path:" in content:
            fp = content.split("File Path:")[1].split("\n")[0].strip()
            fp = fp.replace("`", "").replace("file:///", "")
            view_files.append(fp)
print(f"\nFiles read ({len(view_files)} total):")
for vf in view_files:
    print(f"  - {vf}")

# All CODE_ACTION targets
for s in steps:
    if s.get("type") == "CODE_ACTION":
        content = s.get("content", "")
        # Find TargetFile
        if "TargetFile" in content:
            idx = content.index("TargetFile")
            snippet = content[idx:idx+200]
            print(f"\n[WRITE] Step {s.get('step_index')}: {snippet}")
        elif "file:" in content.lower():
            idx = content.lower().index("file:")
            snippet = content[idx:idx+200]
            print(f"\n[WRITE] Step {s.get('step_index')}: {snippet}")

# Final response
for s in reversed(steps):
    if s.get("type") == "PLANNER_RESPONSE" and s.get("content"):
        print(f"\n[FINAL MODEL] Step {s.get('step_index')} ({len(s['content'])} chars): {s['content'][:400]}")
        break
    
# EPHEMERAL count
ephem_count = sum(1 for s in steps if s.get("type") == "EPHEMERAL_MESSAGE")
print(f"\nEphemeral messages: {ephem_count}")

# Check if model loaded "done" folder or references
done_refs = sum(1 for s in steps if "done" in json.dumps(s, ensure_ascii=False).lower() and s.get("type") in ["VIEW_FILE", "LIST_DIRECTORY"])
print(f"References to 'done' folder: {done_refs}")
