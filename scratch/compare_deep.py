"""Deep compare: system prompt, ephemeral, and per-project rules between Ch2.6 and Ch3.1."""
import json, sys, re
from pathlib import Path
sys.stdout.reconfigure(encoding='utf-8')

BASE = Path(r"C:\Users\promy\.gemini\antigravity-ide\brain")

convos = {
    "Ch2.6": "ac8c1334-319b-4971-85b3-14cb36445cdf",
    "Ch3.1_a1": "92c8b12a-8318-4b70-9075-b3a143254c7f",
    "Ch3.1_a2": "32dbf097-0165-4d70-a560-c7891d6bb8b0",
    "Ch3.1_a3": "a61b758d-e428-4aaa-86bc-79ce77c456e3",
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
    
    # 1. First EPHEMERAL_MESSAGE content - this often contains rules
    ephem_steps = [s for s in steps if s.get("type") == "EPHEMERAL_MESSAGE"]
    if ephem_steps:
        first_ephem = ephem_steps[0]
        c = first_ephem.get("content", "")
        print(f"\n[First EPHEMERAL] Step {first_ephem['step_index']}: {len(c)} chars")
        
        # Check for specific keywords
        keywords = ["smpp-session-lock", "hard-gate", "RULE[", "harness-engineering", 
                    "view_file_cache_guard", "n5-harness", "token-guard",
                    "academic-book-writer", "academic-pipeline",
                    "expression-guard", "shared-dna", "two-stage",
                    "footnote", "legal-section"]
        for kw in keywords:
            if kw.lower() in c.lower():
                idx = c.lower().index(kw.lower())
                ctx = c[max(0,idx-30):idx+100].replace('\n', ' ').strip()
                print(f"  ✅ '{kw}': ...{ctx[:120]}...")
            
        # Count total tokens in first ephemeral
        print(f"  Word count (approx tokens): {len(c.split())}")
    else:
        print("  No EPHEMERAL messages found")
    
    # 2. All EPHEMERAL content total
    total_ephem = sum(len(s.get("content","")) for s in ephem_steps)
    print(f"\n[All EPHEMERAL] Count: {len(ephem_steps)}, Total chars: {total_ephem}")
    
    # 3. Step 0 USER_INPUT - check for injected rules  
    for s in steps:
        if s.get("type") == "USER_INPUT" and s.get("step_index", -1) == 0:
            c = s.get("content", "")
            
            # Check for skills, workflows, plugins sections
            sections = {
                "skills": (c.lower().find("<skills>"), c.lower().find("</skills>")),
                "workflows": (c.lower().find("<workflows>"), c.lower().find("</workflows>")),
                "plugins": (c.lower().find("<plugins>"), c.lower().find("</plugins>")),
                "user_rules": (c.lower().find("<user_rules>"), c.lower().find("</user_rules>")),
                "mcp_servers": (c.lower().find("<mcp_servers>"), c.lower().find("</mcp_servers>")),
            }
            
            print(f"\n[Step 0 sections]:")
            for name, (start, end) in sections.items():
                if start >= 0:
                    length = (end - start) if end >= 0 else "?"
                    print(f"  {name}: start={start}, length={length}")
                else:
                    print(f"  {name}: NOT FOUND")
            
            # Show USER_REQUEST part
            if "<USER_REQUEST>" in c:
                req = c.split("<USER_REQUEST>")[1]
                if "</USER_REQUEST>" in req:
                    req = req.split("</USER_REQUEST>")[0]
                print(f"\n[USER_REQUEST]: {len(req)} chars")
            
            # Total Step 0 length
            print(f"[Step 0 total]: {len(c)} chars")
            break
    
    # 4. What files were read BEFORE first Gate A output
    gate_a_step = None
    for s in steps:
        if s.get("type") == "PLANNER_RESPONSE":
            c = s.get("content", "")
            if ("Gate A" in c or "認知對齊" in c) and len(c) > 500:
                gate_a_step = s.get("step_index")
                print(f"\n[Gate A output] Step {gate_a_step}: {len(c)} chars")
                break
    
    if gate_a_step:
        pre_gate_files = []
        pre_gate_context = 0
        for s in steps:
            if s.get("step_index", 999) >= gate_a_step:
                break
            pre_gate_context += len(s.get("content",""))
            if s.get("type") == "VIEW_FILE":
                c = s.get("content","")
                if "File Path:" in c:
                    fp = c.split("File Path:")[1].split("\n")[0].strip().replace("`","").replace("file:///","")
                    fname = fp.split("/")[-1] if "/" in fp else fp.split("\\")[-1]
                    tb = c.split("Total Bytes:")[1].split("\n")[0].strip() if "Total Bytes:" in c else "?"
                    tl = c.split("Total Lines:")[1].split("\n")[0].strip() if "Total Lines:" in c else "?"
                    sl = ""
                    if "Showing lines " in c:
                        sl = c.split("Showing lines ")[1].split("\n")[0]
                    pre_gate_files.append(f"{fname} (B:{tb}, L:{tl}, {sl})")
        
        print(f"[Pre-Gate-A context]: {pre_gate_context} chars ({pre_gate_context//1000}K)")
        print(f"[Pre-Gate-A files read]: {len(pre_gate_files)}")
        for pf in pre_gate_files:
            print(f"  - {pf}")
