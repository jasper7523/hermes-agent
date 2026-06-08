"""Deep dive into specific conversations for root cause analysis."""
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

BASE = Path(r"C:\Users\promy\.gemini\antigravity-ide\brain")

conversations = {
    "Ch2.6_success": "22567875-d234-47b8-9055-5fc2a7418581",
    "Ch3.1_attempt1": "92c8b12a-8318-4b70-9075-b3a143254c7f",
    "Ch3.1_attempt2": "32dbf097-0165-4d70-a560-c7891d6bb8b0",
    "Ch3.1_attempt3": "a61b758d-e428-4aaa-86bc-79ce77c456e3",
}

for label, cid in conversations.items():
    log_path = BASE / cid / ".system_generated" / "logs" / "transcript.jsonl"
    if not log_path.exists():
        continue
    
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
    
    # 1) Check session_load results 
    for s in steps:
        content = s.get("content", "")
        if "session_load" in content and s.get("type") == "RUN_COMMAND":
            print(f"\n[SMPP session_load] Step {s.get('step_index')}:")
            # Show first 500 chars
            print(content[:500])
            print("---")
    
    # 2) Show USER_INPUT content clearly
    for s in steps:
        if s.get("type") == "USER_INPUT":
            content = s.get("content", "")
            # Find the <USER_REQUEST> part
            if "<USER_REQUEST>" in content:
                req = content.split("<USER_REQUEST>")[1]
                if "</USER_REQUEST>" in req:
                    req = req.split("</USER_REQUEST>")[0]
                print(f"\n[USER_INPUT] Step {s.get('step_index')}:")
                print(req[:500])
                print("---")
    
    # 3) Show model's first substantive response (skill loading, planning)
    for s in steps:
        if s.get("type") == "PLANNER_RESPONSE":
            content = s.get("content", "")
            if content and len(content) > 50:  # Skip empty planning steps
                print(f"\n[FIRST_RESPONSE] Step {s.get('step_index')}:")
                print(content[:800])
                print("---")
                break
    
    # 4) Check if the model searched for "done" folder references
    done_refs = 0
    for s in steps:
        content_str = json.dumps(s, ensure_ascii=False)
        if "done" in content_str.lower() and s.get("type") in ["VIEW_FILE", "LIST_DIRECTORY", "GREP_SEARCH"]:
            done_refs += 1
    print(f"\n[DONE_FOLDER_REFS] {done_refs} steps referencing 'done' folder")
    
    # 5) Check grep search targets
    for s in steps:
        if s.get("type") == "GREP_SEARCH":
            content = s.get("content", "")
            # Find Query in content or tool_calls
            if "Query" in content:
                print(f"\n[GREP] Step {s.get('step_index')}: {content[:200]}")
    
    # 6) Check for the "Please search for" file (anomaly in attempt2)
    for s in steps:
        content = s.get("content", "")
        if "Please search for" in content:
            print(f"\n[ANOMALY] Step {s.get('step_index')} [{s.get('type')}]: 'Please search for' found!")
            print(content[:300])
            print("---")
    
    # 7) Check EPHEMERAL_MESSAGE contents
    ephem_count = 0
    for s in steps:
        if s.get("type") == "EPHEMERAL_MESSAGE":
            ephem_count += 1
    print(f"\n[EPHEMERAL_MESSAGES] {ephem_count} total")

    # 8) show final model output stats
    last_response = ""
    for s in steps:
        if s.get("type") == "PLANNER_RESPONSE" and s.get("content"):
            last_response = s.get("content", "")
    print(f"\n[FINAL_RESPONSE] Length: {len(last_response)} chars")
    print(f"  First 300 chars: {last_response[:300]}")
