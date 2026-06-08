"""Check what literature_review files were read in each Ch3.1 attempt."""
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

BASE = Path(r"C:\Users\promy\.gemini\antigravity-ide\brain")

conversations = {
    "Ch3.1_attempt1": "92c8b12a-8318-4b70-9075-b3a143254c7f",
    "Ch3.1_attempt2": "32dbf097-0165-4d70-a560-c7891d6bb8b0",
    "Ch3.1_attempt3": "a61b758d-e428-4aaa-86bc-79ce77c456e3",
}

for label, cid in conversations.items():
    log_path = BASE / cid / ".system_generated" / "logs" / "transcript.jsonl"
    
    steps = []
    with open(log_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    steps.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
    
    print(f"\n{'='*70}")
    print(f"=== {label} ===")
    
    # USER指定的文獻清單
    for s in steps:
        if s.get("type") == "USER_INPUT":
            content = s.get("content", "")
            if "literature_review" in content:
                req = content
                if "<USER_REQUEST>" in req:
                    req = req.split("<USER_REQUEST>")[1]
                    if "</USER_REQUEST>" in req:
                        req = req.split("</USER_REQUEST>")[0]
                print(f"\n[USER references] Step {s['step_index']}: {req[:500]}")
    
    # 實際讀取的 view_file
    print("\n[VIEW_FILE - literature_review files]:")
    for s in steps:
        if s.get("type") == "VIEW_FILE":
            content = s.get("content", "")
            if "literature_review" in content or "raw_ch" in content or "outline_ch" in content:
                if "File Path:" in content:
                    fp = content.split("File Path:")[1].split("\n")[0].strip()
                    # Get total lines
                    tl = ""
                    if "Total Lines:" in content:
                        tl = content.split("Total Lines:")[1].split("\n")[0].strip()
                    tb = ""
                    if "Total Bytes:" in content:
                        tb = content.split("Total Bytes:")[1].split("\n")[0].strip()
                    print(f"  Step {s['step_index']}: {fp} (Lines:{tl}, Bytes:{tb})")
    
    # GREP searches and what they searched for
    print("\n[GREP searches]:")
    for s in steps:
        if s.get("type") == "GREP_SEARCH":
            content = s.get("content", "")
            # Try to find the query from tool_calls
            tool_calls = s.get("tool_calls", [])
            for tc in tool_calls:
                args = tc.get("arguments", {})
                query = args.get("Query", "")
                search_path = args.get("SearchPath", "")
                if query or search_path:
                    print(f"  Step {s['step_index']}: Query='{query}' Path='{search_path}'")
            if not tool_calls:
                # Check content for results
                result_preview = content[:200]
                print(f"  Step {s['step_index']}: {result_preview}")
    
    # Check for hallucination instances (江XX, 20XX, etc.)
    print("\n[Hallucination indicators]:")
    halluc_count = 0
    for s in steps:
        if s.get("type") == "PLANNER_RESPONSE":
            content = s.get("content", "")
            for marker in ["XX", "20XX", "201X", "江XX", "placeholder", "PLACEHOLDER", "[Author"]:
                if marker in content:
                    halluc_count += 1
                    idx = content.index(marker)
                    context = content[max(0,idx-50):idx+80]
                    print(f"  Step {s['step_index']}: ...{context}...")
                    break
    if halluc_count == 0:
        print("  None detected")
    
    # Total model output chars
    total_model_chars = sum(len(s.get("content", "")) for s in steps if s.get("type") == "PLANNER_RESPONSE")
    print(f"\n[TOTAL MODEL OUTPUT]: {total_model_chars} chars")
