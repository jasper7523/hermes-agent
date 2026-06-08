"""Critical insight: Ch2.6 read literature reviews AT Gate B/C, NOT Gate A.
Ch3.1 tried to read ALL literature reviews BEFORE Gate A."""
import json, sys
from pathlib import Path
sys.stdout.reconfigure(encoding='utf-8')

BASE = Path(r"C:\Users\promy\.gemini\antigravity-ide\brain")

# Show Ch3.1 attempt 2 flow
cid = "32dbf097-0165-4d70-a560-c7891d6bb8b0"
log_path = BASE / cid / ".system_generated" / "logs" / "transcript.jsonl"

steps = []
with open(log_path, "r", encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if line:
            try: steps.append(json.loads(line))
            except: pass

print("=== Ch3.1 Attempt 2 FULL FLOW ===\n")
for s in steps:
    idx = s.get("step_index", -1)
    t = s.get("type","")
    c = s.get("content","")
    
    if t == "USER_INPUT":
        if "<USER_REQUEST>" in c:
            req = c.split("<USER_REQUEST>")[1].split("</USER_REQUEST>")[0] if "</USER_REQUEST>" in c else c.split("<USER_REQUEST>")[1][:400]
            print(f"\nStep {idx:3d} [USER]: {req[:400]}")
    elif t == "PLANNER_RESPONSE" and len(c) > 30:
        print(f"\nStep {idx:3d} [MODEL] ({len(c)} chars): {c[:300]}")
    elif t == "VIEW_FILE":
        if "File Path:" in c:
            fp = c.split("File Path:")[1].split("\n")[0].strip().replace("`","").replace("file:///","")
            fname = fp.split("/")[-1] if "/" in fp else fp.split("\\")[-1]
            sl = c.split("Showing lines ")[1].split("\n")[0] if "Showing lines " in c else "?"
            tb = c.split("Total Bytes:")[1].split("\n")[0].strip() if "Total Bytes:" in c else "?"
            print(f"Step {idx:3d} [READ]: {fname} [{sl}] ({tb} bytes)")
    elif t == "GREP_SEARCH":
        result = "HIT" if "No results found" not in c else "MISS"
        print(f"Step {idx:3d} [GREP]: {result}")
    elif t == "RUN_COMMAND":
        print(f"Step {idx:3d} [CMD]: {c[:150]}")
