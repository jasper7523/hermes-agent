"""Compare initial context between Ch2.6 and Ch3.1 - what changed in 4 days?"""
import json, sys
from pathlib import Path
sys.stdout.reconfigure(encoding='utf-8')

BASE = Path(r"C:\Users\promy\.gemini\antigravity-ide\brain")

convos = {
    "Ch2.6": "ac8c1334-319b-4971-85b3-14cb36445cdf",
    "Ch3.1_a2": "32dbf097-0165-4d70-a560-c7891d6bb8b0",  # Opus, best attempt
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
    print(f"=== {label} ({cid[:12]}) ===")
    
    # 1. Check step 0 USER_INPUT for user_rules content length
    for s in steps:
        if s.get("type") == "USER_INPUT" and s.get("step_index", -1) <= 1:
            c = s.get("content", "")
            print(f"\n[Step {s['step_index']} USER_INPUT] Total length: {len(c)} chars")
            
            # Extract user_rules section
            if "<user_rules>" in c.lower():
                ur_start = c.lower().index("<user_rules>")
                ur_end = c.lower().index("</user_rules>") if "</user_rules>" in c.lower() else len(c)
                user_rules = c[ur_start:ur_end]
                print(f"  user_rules section: {len(user_rules)} chars")
                
                # Check for specific rule files mentioned
                rule_markers = ["RULE[", "smpp", "session-lock", "harness", "n5-harness", 
                               "hard-gate", "academic-book", "Book_Writer"]
                for mk in rule_markers:
                    if mk.lower() in user_rules.lower():
                        # Find context
                        idx = user_rules.lower().index(mk.lower())
                        ctx = user_rules[max(0,idx-20):idx+80]
                        print(f"  Found '{mk}': ...{ctx.strip()}...")
            
            # Extract skills section
            if "<skills>" in c.lower():
                sk_start = c.lower().index("<skills>")
                sk_end = c.lower().index("</skills>") if "</skills>" in c.lower() else len(c)
                print(f"  skills section: {len(c[sk_start:sk_end])} chars")
            
            # Extract workflows
            if "<workflows>" in c.lower():
                wf_start = c.lower().index("<workflows>")
                wf_end = c.lower().index("</workflows>") if "</workflows>" in c.lower() else len(c)
                wf = c[wf_start:wf_end]
                print(f"  workflows section: {len(wf)} chars")
                print(f"  workflows content: {wf[:500]}")
            
            # Check RULE blocks - list all
            import re
            rules = re.findall(r'<RULE\[([^\]]+)\]>', c)
            print(f"  RULE blocks found: {rules}")
            
            break
    
    # 2. SMPP output length
    for s in steps:
        if s.get("type") == "RUN_COMMAND":
            c = s.get("content", "")
            if "Session Memory" in c or "session_load" in c:
                print(f"\n[SMPP output] Step {s['step_index']}: {len(c)} chars")
                # Count lines
                print(f"  Lines: {c.count(chr(10))}")
                break
    
    # 3. First model response - what did it load?
    for s in steps:
        if s.get("type") == "PLANNER_RESPONSE" and len(s.get("content","")) > 50:
            c = s.get("content","")
            print(f"\n[First response] Step {s['step_index']}: {len(c)} chars")
            print(f"  Content: {c[:400]}")
            break
    
    # 4. Total context consumed before Gate A output
    # Sum all content up to first substantive model output
    first_output_step = None
    for s in steps:
        if s.get("type") == "PLANNER_RESPONSE" and len(s.get("content","")) > 200:
            first_output_step = s.get("step_index")
            break
    
    if first_output_step:
        total_input = 0
        for s in steps:
            if s.get("step_index", 999) < first_output_step:
                total_input += len(s.get("content", ""))
        print(f"\n[Context before first output (step {first_output_step})]: {total_input} chars ({total_input//1000}K)")
