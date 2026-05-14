import json
import re

log_path = r"C:\Users\promy\.gemini\antigravity\brain\07f4332c-8f93-4c80-8e83-d3344ba7e077\.system_generated\logs\overview.txt"
targets = ["outline_ch2_2.md", "Please search for_ (1) the DOJ Evaluation of Corpo.md"]

with open(log_path, 'r', encoding='utf-8-sig') as f:
    for line in f:
        for t in targets:
            if t in line and "write_to_file" in line:
                match = re.search(r'(\{.*\})', line)
                if match:
                    try:
                        d = json.loads(match.group(1))
                        calls = d.get('tool_calls', [])
                        for c in calls:
                            if c.get('name') == 'write_to_file':
                                args = c.get('args', {})
                                if 'CodeContent' in args:
                                    out_path = fr"D:\Agent_Hub\agents\Book_Writer_Agent\data\workspace\book\ch 2.2\{t}"
                                    with open(out_path, 'w', encoding='utf-8') as out:
                                        out.write(args['CodeContent'])
                                    print(f"Successfully restored {out_path}")
                                    break
                    except Exception as e:
                        pass
