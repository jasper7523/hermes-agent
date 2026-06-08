"""Analyze CORRECT Ch2.6 success transcript: ac8c1334"""
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

print(f"Total steps: {len(steps)}")
print(f"File size: {log_path.stat().st_size} bytes")

# Step types
tc = {}
for s in steps:
    t = s.get("type","?")
    tc[t] = tc.get(t,0)+1
print(f"Types: {json.dumps(tc, ensure_ascii=False)}")

# USER_INPUT
print("\n=== USER INPUTS ===")
for s in steps:
    if s.get("type") == "USER_INPUT":
        c = s.get("content","")
        if "<USER_REQUEST>" in c:
            req = c.split("<USER_REQUEST>")[1].split("</USER_REQUEST>")[0] if "</USER_REQUEST>" in c else c.split("<USER_REQUEST>")[1]
            print(f"\n[USER] Step {s['step_index']}: {req[:500]}")

# Files read
print("\n=== FILES READ ===")
for s in steps:
    if s.get("type") == "VIEW_FILE" and s.get("status") == "DONE":
        c = s.get("content","")
        if "File Path:" in c:
            fp = c.split("File Path:")[1].split("\n")[0].strip().replace("`","").replace("file:///","")
            tl = c.split("Total Lines:")[1].split("\n")[0].strip() if "Total Lines:" in c else "?"
            tb = c.split("Total Bytes:")[1].split("\n")[0].strip() if "Total Bytes:" in c else "?"
            # Check StartLine/EndLine
            sl = c.split("Showing lines ")[1].split(" to ")[0] if "Showing lines " in c else "?"
            el = c.split(" to ")[1].split("\n")[0] if " to " in c and "Showing lines" in c else "?"
            print(f"  Step {s['step_index']}: {fp} (L:{tl}, B:{tb}, showing {sl}-{el})")

# SMPP / session_load
print("\n=== SMPP/MEMORY ===")
smpp_found = False
for s in steps:
    full = json.dumps(s, ensure_ascii=False)
    if any(kw in full.lower() for kw in ["session_load","smpp","session memory","session_save"]):
        smpp_found = True
        print(f"  Step {s['step_index']} [{s['type']}]: {s.get('content','')[:300]}")
if not smpp_found:
    print("  (None)")

# RUN_COMMAND
print("\n=== RUN COMMANDS ===")
for s in steps:
    if s.get("type") == "RUN_COMMAND":
        print(f"  Step {s['step_index']}: {s.get('content','')[:300]}")

# GREP
print("\n=== GREP SEARCHES ===")
grep_ok = 0; grep_fail = 0
for s in steps:
    if s.get("type") == "GREP_SEARCH":
        c = s.get("content","")
        if "No results found" in c:
            grep_fail += 1
            print(f"  Step {s['step_index']}: No results")
        else:
            grep_ok += 1
            print(f"  Step {s['step_index']}: HAS results ({c[:120]})")
print(f"  Total: {grep_ok} success, {grep_fail} empty")

# CODE_ACTION / WRITE
print("\n=== WRITE ACTIONS ===")
for s in steps:
    if s.get("type") in ["CODE_ACTION","WRITE_FILE"]:
        c = s.get("content","")
        for m in ["file:///","TargetFile"]:
            if m in c:
                idx = c.index(m)
                print(f"  Step {s['step_index']}: {c[idx:idx+180]}")
                break

# Hallucination check
print("\n=== HALLUCINATION MARKERS ===")
h = 0
for s in steps:
    if s.get("type") == "PLANNER_RESPONSE":
        c = s.get("content","")
        for mk in ["XX","20XX","201X","placeholder","PLACEHOLDER","[Author"]:
            if mk in c:
                h += 1
                idx = c.index(mk)
                print(f"  Step {s['step_index']}: ...{c[max(0,idx-40):idx+60]}...")
                break
if h == 0: print("  None detected")

# Model output stats
total_chars = sum(len(s.get("content","")) for s in steps if s.get("type")=="PLANNER_RESPONSE")
resp_count = sum(1 for s in steps if s.get("type")=="PLANNER_RESPONSE")
print(f"\n=== OUTPUT STATS ===")
print(f"  Responses: {resp_count}, Total chars: {total_chars}")

# EPHEMERAL
ephem = sum(1 for s in steps if s.get("type")=="EPHEMERAL_MESSAGE")
print(f"  Ephemeral messages: {ephem}")
