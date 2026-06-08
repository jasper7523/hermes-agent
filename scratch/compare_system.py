"""Compare EXACT system-level context: per-project rules injected at conversation start.
Focus on what the IDE/system injected (not user prompt)."""
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
    steps = []
    with open(log_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try: steps.append(json.loads(line))
                except: pass

    print(f"\n{'='*70}")
    print(f"=== {label} ===")
    
    # Step 0: Show EVERYTHING outside USER_REQUEST (system injected context)
    for s in steps:
        if s.get("type") == "USER_INPUT" and s.get("step_index", -1) == 0:
            c = s.get("content","")
            
            # Remove USER_REQUEST to see what system injected
            if "<USER_REQUEST>" in c and "</USER_REQUEST>" in c:
                before_req = c[:c.index("<USER_REQUEST>")]
                after_req = c[c.index("</USER_REQUEST>")+len("</USER_REQUEST>"):]
                system_context = before_req + after_req
            else:
                system_context = c
            
            print(f"\n[SYSTEM CONTEXT] {len(system_context)} chars total")
            
            # Show all xml-like sections
            import re
            tags = re.findall(r'<(\w+[^>]*)>', system_context)
            print(f"  XML tags found: {tags}")
            
            # Show the full system context (it should contain rules, etc.)
            # Just show first 3000 chars and last 1000 chars
            print(f"\n--- FIRST 3000 chars ---")
            print(system_context[:3000])
            print(f"\n--- LAST 1000 chars ---")
            print(system_context[-1000:])
            break
    
    # Also check CONVERSATION_HISTORY steps
    for s in steps:
        if s.get("type") == "CONVERSATION_HISTORY":
            c = s.get("content","")
            print(f"\n[CONV_HISTORY] Step {s['step_index']}: {len(c)} chars")
            # Check if it contains per-project rules
            if "RULE[" in c or "user_rules" in c.lower():
                print(f"  Contains RULE blocks!")
                rules = re.findall(r'<RULE\[([^\]]+)\]>', c)
                print(f"  Rules: {rules}")
            break
