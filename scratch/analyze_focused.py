"""Focused analysis on Ch2.6 success and Ch3.1 attempt1."""
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

BASE = Path(r"C:\Users\promy\.gemini\antigravity-ide\brain")

conversations = {
    "Ch2.6_success": "22567875-d234-47b8-9055-5fc2a7418581",
    "Ch3.1_attempt1": "92c8b12a-8318-4b70-9075-b3a143254c7f",
}

for label, cid in conversations.items():
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
    
    print(f"\n{'='*70}")
    print(f"=== {label} ===")
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
        if "session_load" in content and s.get("type") == "RUN_COMMAND":
            print(f"\n[SMPP] Step {s.get('step_index')}: {content[:400]}")
    
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

    # All PLANNER_RESPONSE first 200 chars
    print("\n--- MODEL RESPONSES ---")
    for s in steps:
        if s.get("type") == "PLANNER_RESPONSE":
            content = s.get("content", "")
            if content:
                print(f"\n[MODEL] Step {s.get('step_index')} ({len(content)} chars): {content[:300]}")
    
    # EPHEMERAL_MESSAGE contents
    print("\n--- EPHEMERAL MESSAGES ---")
    for s in steps:
        if s.get("type") == "EPHEMERAL_MESSAGE":
            content = s.get("content", "")
            print(f"\n[EPHEM] Step {s.get('step_index')}: {content[:200]}")
    
    # CODE_ACTION targets
    for s in steps:
        if s.get("type") == "CODE_ACTION":
            content = s.get("content", "")
            # Find file path
            for marker in ["TargetFile", "file:///", "File Path"]:
                if marker in content:
                    idx = content.index(marker)
                    print(f"\n[WRITE] Step {s.get('step_index')}: ...{content[idx:idx+150]}")
                    break
