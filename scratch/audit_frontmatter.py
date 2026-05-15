import os
import sys
sys.stdout.reconfigure(encoding='utf-8')

# All rules files
rules = [
    ("N5", "book-writer-agent.md", r"D:\Agent_Hub\agents\Book_Writer_Agent\.agents\rules\book-writer-agent.md"),
    ("N5", "smpp-session-lock.md", r"D:\Agent_Hub\agents\Book_Writer_Agent\.agents\rules\smpp-session-lock.md"),
    ("N5", "harness-engineering-lock.md", r"D:\Agent_Hub\agents\Book_Writer_Agent\.agents\rules\harness-engineering-lock.md"),
    ("N5", "literature-format-lock.md", r"D:\Agent_Hub\agents\Book_Writer_Agent\.agents\rules\literature-format-lock.md"),
    ("N5", "skill-audit-trail.md", r"D:\Agent_Hub\agents\Book_Writer_Agent\.agents\rules\skill-audit-trail.md"),
    ("N5", "chapter-context-isolation.md", r"D:\Agent_Hub\agents\Book_Writer_Agent\.agents\rules\chapter-context-isolation.md"),
    ("N7", "hermes-agent.md", r"d:\hermes-agent\.agents\rules\hermes-agent.md"),
    ("N8", "academic-oracle-agent.md", r"D:\Agent_Hub\agents\Academic_Oracle_Agent\.agents\rules\academic-oracle-agent.md"),
    ("N9", "entropy-guardian.md", r"D:\Agent_Hub\agents\Entropy_Guardian\.agents\rules\entropy-guardian.md"),
]

# All workflow files
workflows = [
    ("N5", "book-writer-agent.md", r"D:\Agent_Hub\agents\Book_Writer_Agent\.agents\workflows\book-writer-agent.md"),
    ("N5", "hard-gate-workflow.md", r"D:\Agent_Hub\agents\Book_Writer_Agent\.agents\workflows\hard-gate-workflow.md"),
    ("N5", "two-stage-review-workflow.md", r"D:\Agent_Hub\agents\Book_Writer_Agent\.agents\workflows\two-stage-review-workflow.md"),
    ("N5", "academic-review-workflow.md", r"D:\Agent_Hub\agents\Book_Writer_Agent\.agents\workflows\academic-review-workflow.md"),
    ("N5", "chapter-writing-plan-template.md", r"D:\Agent_Hub\agents\Book_Writer_Agent\.agents\workflows\chapter-writing-plan-template.md"),
    ("N5", "n5-session.md", r"D:\Agent_Hub\agents\Book_Writer_Agent\.agents\workflows\n5-session.md"),
    ("N7", "hermes-build.md", r"d:\hermes-agent\.agents\workflows\hermes-build.md"),
    ("N7", "hermes-session.md", r"d:\hermes-agent\.agents\workflows\hermes-session.md"),
    ("N7", "evaluator-calibration.md", r"d:\hermes-agent\.agents\workflows\evaluator-calibration.md"),
]

def check_frontmatter(path):
    with open(path, encoding="utf-8") as f:
        lines = f.readlines()
    
    if not lines or lines[0].strip() != "---":
        return {"has_frontmatter": False}
    
    end = -1
    for i in range(1, min(len(lines), 15)):
        if lines[i].strip() == "---":
            end = i
            break
    
    if end == -1:
        return {"has_frontmatter": False}
    
    fm = {}
    for line in lines[1:end]:
        if ":" in line:
            key = line.split(":")[0].strip()
            fm[key] = True
    
    return fm

print("=" * 70)
print("RULES 審計結果")
print("=" * 70)
for node, name, path in rules:
    fm = check_frontmatter(path)
    has_trigger = "trigger" in fm
    has_bad = "alwaysApply" in fm
    status = "✅" if has_trigger and not has_bad else "❌"
    print(f"  {status} [{node}] {name:<35} trigger={has_trigger} alwaysApply={has_bad}")

print()
print("=" * 70)
print("WORKFLOWS 審計結果")
print("=" * 70)
for node, name, path in workflows:
    fm = check_frontmatter(path)
    has_name = "name" in fm
    has_desc = "description" in fm
    has_bad = "source" in fm or "changelog" in fm or "alwaysApply" in fm
    status = "✅" if has_name and has_desc and not has_bad else ("⚠️" if not has_bad else "❌")
    extras = []
    if "source" in fm: extras.append("source")
    if "changelog" in fm: extras.append("changelog")
    if "glob" in fm: extras.append("glob")
    extra_str = f" [冗餘: {', '.join(extras)}]" if extras else ""
    print(f"  {status} [{node}] {name:<35} name={has_name} desc={has_desc}{extra_str}")

print()
print("=" * 70)
print("審計完成")
print("=" * 70)
