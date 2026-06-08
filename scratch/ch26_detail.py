"""Show Ch2.6 Steps 4-5 in FULL DETAIL to understand model's decision."""
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

# Show Steps 2-6 raw JSON keys and full content
for s in steps:
    idx = s.get("step_index", -1)
    if idx < 2 or idx > 18: continue
    
    print(f"\n{'='*60}")
    print(f"Step {idx}: type={s.get('type')}, status={s.get('status')}")
    print(f"Keys: {list(s.keys())}")
    
    c = s.get("content","")
    if s.get("type") == "PLANNER_RESPONSE":
        print(f"Content ({len(c)} chars): [{c}]")
        # Check for tool_calls
        if s.get("tool_calls"):
            print(f"Tool calls: {json.dumps(s['tool_calls'], ensure_ascii=False)[:500]}")
    elif s.get("type") == "RUN_COMMAND":
        print(f"Content ({len(c)} chars): {c[:500]}")
    elif s.get("type") == "VIEW_FILE":
        if "File Path:" in c:
            fp = c.split("File Path:")[1].split("\n")[0].strip()
            print(f"File: {fp}")
    elif s.get("type") == "EPHEMERAL_MESSAGE":
        print(f"Content ({len(c)} chars): {c[:200]}")
    elif s.get("type") == "CONVERSATION_HISTORY":
        print(f"Content ({len(c)} chars): {c[:200]}")
