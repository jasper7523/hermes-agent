"""Compare Ch2.6 (success) vs Ch3.1 (failures) transcripts - focused analysis."""
import json
import sys
import os
from pathlib import Path

# Fix encoding
sys.stdout.reconfigure(encoding='utf-8')

BASE = Path(r"C:\Users\promy\.gemini\antigravity-ide\brain")

conversations = {
    "Ch2.6_success": "22567875-d234-47b8-9055-5fc2a7418581",
    "Ch3.1_attempt1": "92c8b12a-8318-4b70-9075-b3a143254c7f",
    "Ch3.1_attempt2": "32dbf097-0165-4d70-a560-c7891d6bb8b0",
    "Ch3.1_attempt3": "a61b758d-e428-4aaa-86bc-79ce77c456e3",
}

for label, cid in conversations.items():
    log_path = BASE / cid / ".system_generated" / "logs" / "transcript.jsonl"
    if not log_path.exists():
        print(f"\n=== {label}: FILE NOT FOUND ===")
        continue
    
    steps = []
    with open(log_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    steps.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
    
    print(f"\n{'='*60}")
    print(f"=== {label} ({cid[:12]}...) ===")
    print(f"Total steps: {len(steps)}")
    
    # Count types
    type_counts = {}
    for s in steps:
        t = s.get("type", "UNKNOWN")
        type_counts[t] = type_counts.get(t, 0) + 1
    
    print(f"Step types: {json.dumps(type_counts, indent=2, ensure_ascii=False)}")
    
    # Extract view_file calls to see what files were read
    view_files = []
    for s in steps:
        if s.get("type") == "VIEW_FILE" and s.get("status") == "DONE":
            content = s.get("content", "")
            if "File Path:" in content:
                fp = content.split("File Path:")[1].split("\n")[0].strip()
                fp = fp.replace("`", "").replace("file:///", "")
                view_files.append(fp)
    
    print(f"\nFiles read ({len(view_files)} total):")
    for vf in view_files:
        print(f"  - {vf}")
    
    # Extract run_command calls
    run_cmds = []
    for s in steps:
        if s.get("type") == "RUN_COMMAND":
            content = s.get("content", "")[:200]
            # Try to find command line
            tool_calls = s.get("tool_calls", [])
            for tc in tool_calls:
                args = tc.get("arguments", {})
                cmd = args.get("CommandLine", "")
                if cmd:
                    run_cmds.append(f"  Step {s.get('step_index')}: {cmd[:150]}")
            if not tool_calls:
                run_cmds.append(f"  Step {s.get('step_index')}: [output] {content[:100]}")
    
    print(f"\nRun commands ({len(run_cmds)}):")
    for rc in run_cmds:
        print(rc)
    
    # Check for SMPP / session_load / memory references
    smpp_steps = []
    for s in steps:
        content_str = json.dumps(s, ensure_ascii=False)
        if any(kw in content_str.lower() for kw in ["session_load", "smpp", "memory\\scripts", "memory/scripts"]):
            step_content = s.get("content", "")[:150]
            smpp_steps.append(f"  Step {s.get('step_index')} [{s.get('type')}]: {step_content}")
    
    print(f"\nSMPP/Memory steps ({len(smpp_steps)}):")
    for ss in smpp_steps:
        print(ss)

    # Check for errors
    error_steps = []
    for s in steps:
        if s.get("status") == "ERROR":
            content = s.get("content", "")[:200]
            error_steps.append(f"  Step {s.get('step_index')} [{s.get('type')}]: {content}")
    
    print(f"\nError steps ({len(error_steps)}):")
    for es in error_steps:
        print(es)
    
    # Check for WRITE_FILE / CODE_ACTION - what was actually produced
    write_steps = []
    for s in steps:
        if s.get("type") in ["CODE_ACTION", "WRITE_FILE"]:
            content = s.get("content", "")
            # Extract target file
            if "TargetFile" in content:
                tf = content.split("TargetFile")[1][:200]
                write_steps.append(f"  Step {s.get('step_index')}: {tf[:150]}")
            elif "file:" in content.lower():
                idx = content.lower().find("file:")
                write_steps.append(f"  Step {s.get('step_index')}: {content[idx:idx+150]}")
            else:
                write_steps.append(f"  Step {s.get('step_index')}: {content[:100]}")
    
    print(f"\nWrite/Code actions ({len(write_steps)}):")
    for ws in write_steps:
        print(ws)
    
    # Look for grep_search
    grep_steps = []
    for s in steps:
        if s.get("type") == "GREP_SEARCH":
            content = s.get("content", "")[:200]
            grep_steps.append(f"  Step {s.get('step_index')}: {content[:150]}")
    
    print(f"\nGrep searches ({len(grep_steps)}):")
    for gs in grep_steps:
        print(gs)
