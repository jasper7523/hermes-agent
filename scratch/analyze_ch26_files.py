"""Ch2.6 correct - Part 2: files read in first half."""
import json, sys
from pathlib import Path
sys.stdout.reconfigure(encoding='utf-8')

cid = "ac8c1334-319b-4971-85b3-14cb36445cdf"
log_path = Path(r"C:\Users\promy\.gemini\antigravity-lite\brain") if False else Path(r"C:\Users\promy\.gemini\antigravity-ide\brain") / cid / ".system_generated" / "logs" / "transcript.jsonl"

steps = []
with open(log_path, "r", encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if line:
            try: steps.append(json.loads(line))
            except: pass

# ALL Files read with step index
print("=== ALL FILES READ (ordered by step) ===")
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
                sl_el = f" [{sl}]"
            # Get just filename
            fname = fp.split("/")[-1] if "/" in fp else fp.split("\\")[-1]
            print(f"  Step {s['step_index']:3d}: {fname:50s} (L:{tl:>5s}, B:{tb:>7s}{sl_el})")

# Count lit_review reads
print("\n=== LITERATURE REVIEW READS DETAIL ===")
for s in steps:
    if s.get("type") == "VIEW_FILE" and s.get("status") == "DONE":
        c = s.get("content","")
        if "literature_review" in c and "File Path:" in c:
            fp = c.split("File Path:")[1].split("\n")[0].strip().replace("`","").replace("file:///","")
            tl = c.split("Total Lines:")[1].split("\n")[0].strip() if "Total Lines:" in c else "?"
            tb = c.split("Total Bytes:")[1].split("\n")[0].strip() if "Total Bytes:" in c else "?"
            sl_el = ""
            if "Showing lines " in c:
                sl = c.split("Showing lines ")[1].split("\n")[0]
                sl_el = f" [{sl}]"
            fname = fp.split("/")[-1] if "/" in fp else fp.split("\\")[-1]
            print(f"  Step {s['step_index']:3d}: {fname:50s} (L:{tl}, B:{tb}{sl_el})")

# Ch2.6 session_load.py size at that time
print("\n=== session_load.py size at Ch2.6 time ===")
for s in steps:
    c = s.get("content","")
    if "session_load.py" in c and "sizeBytes" in c:
        print(f"  Step {s['step_index']}: {c[:200]}")
        break
