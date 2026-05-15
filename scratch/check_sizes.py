import os

files = [
    ("N5 book-writer-agent.md", r"D:\Agent_Hub\agents\Book_Writer_Agent\.agents\rules\book-writer-agent.md"),
    ("N7 hermes-agent.md", r"d:\hermes-agent\.agents\rules\hermes-agent.md"),
    ("N8 academic-oracle-agent.md", r"D:\Agent_Hub\agents\Academic_Oracle_Agent\.agents\rules\academic-oracle-agent.md"),
    ("N9 entropy-guardian.md", r"D:\Agent_Hub\agents\Entropy_Guardian\.agents\rules\entropy-guardian.md"),
]

for name, path in files:
    with open(path, encoding="utf-8") as f:
        lines = f.readlines()
    size = os.path.getsize(path)
    print(f"{name}: {len(lines)} lines, {size} bytes ({size/1024:.1f} KB)")
