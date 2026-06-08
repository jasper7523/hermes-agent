"""Ch2.6 correct - Part 1: Focus on structure and reading pattern."""
import json, sys
from pathlib import Path
sys.stdout.reconfigure(encoding='utf-8')

cid = "ac8c1334-319b-4971-85b3-14cb36445cdf"
log_path = Path(r"C:\Users\promy\.gemini\antigravity-ide\brain") / cid / ".system_generated" / "logs" / "transcript.jsonl"

steps = []
with open(log_path, "r", encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if line:
            try: steps.append(json.loads(line))
            except: pass

print(f"Total steps: {len(steps)}, File size: {log_path.stat().st_size}")

# Step types
tc = {}
for s in steps:
    t = s.get("type","?")
    tc[t] = tc.get(t,0)+1
print(f"Types: {json.dumps(tc, ensure_ascii=False)}")

# USER_INPUT - first 3 only
print("\n=== FIRST 3 USER INPUTS ===")
ui_count = 0
for s in steps:
    if s.get("type") == "USER_INPUT":
        c = s.get("content","")
        if "<USER_REQUEST>" in c:
            req = c.split("<USER_REQUEST>")[1].split("</USER_REQUEST>")[0] if "</USER_REQUEST>" in c else c.split("<USER_REQUEST>")[1][:600]
            print(f"\n[USER] Step {s['step_index']}: {req[:600]}")
            ui_count += 1
            if ui_count >= 3:
                break

# ALL Files read - with size info
print("\n=== ALL FILES READ ===")
lit_review_total_bytes = 0
for s in steps:
    if s.get("type") == "VIEW_FILE" and s.get("status") == "DONE":
        c = s.get("content","")
        if "File Path:" in c:
            fp = c.split("File Path:")[1].split("\n")[0].strip().replace("`","").replace("file:///","")
            tl = c.split("Total Lines:")[1].split("\n")[0].strip() if "Total Lines:" in c else "?"
            tb = c.split("Total Bytes:")[1].split("\n")[0].strip() if "Total Bytes:" in c else "?"
            sl_el = ""
            if "Showing lines " in c:
                sl = c.split("Showing lines ")[1].split("\n")[0]
                sl_el = f" showing {sl}"
            print(f"  Step {s['step_index']}: {fp.split('/')[-1]} (L:{tl}, B:{tb}{sl_el})")
            if "literature_review" in fp:
                try: lit_review_total_bytes += int(tb)
                except: pass

print(f"\n  Total literature_review bytes read: {lit_review_total_bytes}")

# SMPP
print("\n=== SMPP/MEMORY ===")
smpp_found = False
for s in steps:
    full = json.dumps(s, ensure_ascii=False)
    if any(kw in full.lower() for kw in ["session_load","smpp-1","session memory"]):
        if s.get("type") in ["RUN_COMMAND","PLANNER_RESPONSE","VIEW_FILE"]:
            smpp_found = True
            c = s.get("content","")
            print(f"  Step {s['step_index']} [{s['type']}]: {c[:200]}")
if not smpp_found:
    print("  (None found)")

# MCP tool calls
print("\n=== MCP TOOL CALLS ===")
for s in steps:
    full = json.dumps(s, ensure_ascii=False)
    if "mcp" in full.lower() and s.get("type") in ["RUN_COMMAND","PLANNER_RESPONSE","MCP_TOOL"]:
        c = s.get("content","")
        if "validate" in c.lower() or "claim" in c.lower() or "mcp" in c.lower():
            print(f"  Step {s['step_index']} [{s['type']}]: {c[:200]}")

# List how many user turns
user_turns = sum(1 for s in steps if s.get("type") == "USER_INPUT")
print(f"\nTotal user turns: {user_turns}")

# session_save calls
print("\n=== SESSION_SAVE calls ===")
for s in steps:
    c = s.get("content","")
    if "session_save" in c:
        print(f"  Step {s['step_index']}: {c[:250]}")
