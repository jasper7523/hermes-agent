"""Critical: What did Ch2.6's model do between Step 0 and Step 18 (Gate A)?
WHY did it not read literature_reviews before Gate A?"""
import json, sys
from pathlib import Path
sys.stdout.reconfigure(encoding='utf-8')

BASE = Path(r"C:\Users\promy\.gemini\antigravity-ide\brain")
cid = "ac8c1334-319b-4971-85b3-14cb36445cdf"
log_path = BASE / cid / ".system_generated" / "logs" / "transcript.jsonl"

steps = []
with open(log_path, "r", encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if line:
            try: steps.append(json.loads(line))
            except: pass

print("=== Ch2.6: EVERY STEP from 0 to 20 ===\n")
for s in steps:
    idx = s.get("step_index", -1)
    if idx > 20: break
    t = s.get("type","")
    c = s.get("content","")
    
    if t == "USER_INPUT":
        # Show USER_REQUEST only
        if "<USER_REQUEST>" in c:
            req = c.split("<USER_REQUEST>")[1].split("</USER_REQUEST>")[0] if "</USER_REQUEST>" in c else ""
            print(f"Step {idx:2d} [{t:20s}] ({len(c):>5d} chars) USER_REQUEST: {req[:200]}")
        else:
            print(f"Step {idx:2d} [{t:20s}] ({len(c):>5d} chars)")
    elif t == "PLANNER_RESPONSE":
        print(f"Step {idx:2d} [{t:20s}] ({len(c):>5d} chars) {c[:300]}")
    elif t == "VIEW_FILE":
        if "File Path:" in c:
            fp = c.split("File Path:")[1].split("\n")[0].strip().replace("`","").replace("file:///","")
            fname = fp.split("/")[-1] if "/" in fp else fp.split("\\")[-1]
            sl = c.split("Showing lines ")[1].split("\n")[0] if "Showing lines " in c else "?"
            print(f"Step {idx:2d} [{t:20s}] READ: {fname} [{sl}]")
        else:
            print(f"Step {idx:2d} [{t:20s}] ({len(c):>5d} chars)")
    elif t == "RUN_COMMAND":
        # Show first line of output
        first_line = c.split('\n')[0] if c else ""
        print(f"Step {idx:2d} [{t:20s}] {first_line[:150]}")
    elif t == "EPHEMERAL_MESSAGE":
        print(f"Step {idx:2d} [{t:20s}] ({len(c):>5d} chars) {c[:100]}")
    elif t == "CONVERSATION_HISTORY":
        print(f"Step {idx:2d} [{t:20s}] ({len(c):>5d} chars) {c[:100]}")
    elif t == "GREP_SEARCH":
        result = "HIT" if "No results" not in c else "MISS"
        print(f"Step {idx:2d} [{t:20s}] {result}")
    else:
        print(f"Step {idx:2d} [{t:20s}] ({len(c):>5d} chars)")

# Now show Ch3.1 attempt 2 Steps 0-50
print("\n\n=== Ch3.1 Attempt 2: EVERY STEP from 0 to 50 ===\n")
cid2 = "32dbf097-0165-4d70-a560-c7891d6bb8b0"
log_path2 = BASE / cid2 / ".system_generated" / "logs" / "transcript.jsonl"
steps2 = []
with open(log_path2, "r", encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if line:
            try: steps2.append(json.loads(line))
            except: pass

for s in steps2:
    idx = s.get("step_index", -1)
    if idx > 50: break
    t = s.get("type","")
    c = s.get("content","")
    
    if t == "USER_INPUT":
        if "<USER_REQUEST>" in c:
            req = c.split("<USER_REQUEST>")[1].split("</USER_REQUEST>")[0] if "</USER_REQUEST>" in c else ""
            print(f"Step {idx:2d} [{t:20s}] ({len(c):>5d} chars) USER_REQUEST: {req[:200]}")
        else:
            print(f"Step {idx:2d} [{t:20s}] ({len(c):>5d} chars)")
    elif t == "PLANNER_RESPONSE":
        print(f"Step {idx:2d} [{t:20s}] ({len(c):>5d} chars) {c[:300]}")
    elif t == "VIEW_FILE":
        if "File Path:" in c:
            fp = c.split("File Path:")[1].split("\n")[0].strip().replace("`","").replace("file:///","")
            fname = fp.split("/")[-1] if "/" in fp else fp.split("\\")[-1]
            sl = c.split("Showing lines ")[1].split("\n")[0] if "Showing lines " in c else "?"
            print(f"Step {idx:2d} [{t:20s}] READ: {fname} [{sl}]")
    elif t == "RUN_COMMAND":
        first_line = c.split('\n')[0] if c else ""
        print(f"Step {idx:2d} [{t:20s}] {first_line[:150]}")
    elif t == "EPHEMERAL_MESSAGE":
        print(f"Step {idx:2d} [{t:20s}] ({len(c):>5d} chars)")
    elif t == "CONVERSATION_HISTORY":
        print(f"Step {idx:2d} [{t:20s}] ({len(c):>5d} chars) {c[:100]}")
    elif t == "GREP_SEARCH":
        result = "HIT" if "No results" not in c else "MISS"
        print(f"Step {idx:2d} [{t:20s}] {result}")
    else:
        print(f"Step {idx:2d} [{t:20s}] ({len(c):>5d} chars)")
