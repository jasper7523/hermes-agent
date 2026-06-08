"""Critical: When did Ch2.6 read literature_reviews? What triggered segmented reads?"""
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

# Show steps 18 (Gate A) through 200 (Gate B/C area) - key flow
print("=== Ch2.6 FLOW: Gate A → Gate B (Steps 18-200) ===\n")
for s in steps:
    idx = s.get("step_index", -1)
    if idx < 18 or idx > 200:
        continue
    t = s.get("type","")
    c = s.get("content","")
    
    if t == "USER_INPUT":
        if "<USER_REQUEST>" in c:
            req = c.split("<USER_REQUEST>")[1].split("</USER_REQUEST>")[0] if "</USER_REQUEST>" in c else c.split("<USER_REQUEST>")[1][:300]
            print(f"Step {idx:3d} [USER]: {req[:300]}")
    elif t == "PLANNER_RESPONSE" and len(c) > 50:
        print(f"Step {idx:3d} [MODEL]: {c[:250]}")
    elif t == "VIEW_FILE":
        if "File Path:" in c:
            fp = c.split("File Path:")[1].split("\n")[0].strip().replace("`","").replace("file:///","")
            fname = fp.split("/")[-1] if "/" in fp else fp.split("\\")[-1]
            sl = c.split("Showing lines ")[1].split("\n")[0] if "Showing lines " in c else "?"
            tb = c.split("Total Bytes:")[1].split("\n")[0].strip() if "Total Bytes:" in c else "?"
            print(f"Step {idx:3d} [READ]: {fname} [{sl}] ({tb} bytes)")
    elif t == "CODE_ACTION":
        if "file:///" in c:
            fpi = c.index("file:///")
            fp = c[fpi:fpi+120]
            print(f"Step {idx:3d} [WRITE]: {fp}")
    elif t == "GREP_SEARCH":
        result = "HIT" if "No results found" not in c else "MISS"
        print(f"Step {idx:3d} [GREP]: {result}")
    elif t == "MCP_TOOL":
        print(f"Step {idx:3d} [MCP]: {c[:120]}")
    elif t in ["RUN_COMMAND"]:
        print(f"Step {idx:3d} [CMD]: {c[:120]}")
    # Skip EPHEMERAL, CONVERSATION_HISTORY for clarity
