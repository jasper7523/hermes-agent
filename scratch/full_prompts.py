"""Extract FULL Step 0 USER_REQUEST for both Ch2.6 and Ch3.1."""
import json, sys
from pathlib import Path
sys.stdout.reconfigure(encoding='utf-8')

BASE = Path(r"C:\Users\promy\.gemini\antigravity-ide\brain")
convos = {
    "Ch2.6": "ac8c1334-319b-4971-85b3-14cb36445cdf",
    "Ch3.1_a2": "32dbf097-0165-4d70-a560-c7891d6bb8b0",
}

for label, cid in convos.items():
    log_path = BASE / cid / ".system_generated" / "logs" / "transcript.jsonl"
    with open(log_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line: continue
            try: s = json.loads(line)
            except: continue
            if s.get("type") == "USER_INPUT" and s.get("step_index", -1) == 0:
                c = s.get("content","")
                if "<USER_REQUEST>" in c:
                    req = c.split("<USER_REQUEST>")[1]
                    if "</USER_REQUEST>" in req:
                        req = req.split("</USER_REQUEST>")[0]
                    print(f"\n{'='*60}")
                    print(f"=== {label} FULL USER_REQUEST ({len(req)} chars) ===")
                    print(req)
                    print(f"{'='*60}")
                break
