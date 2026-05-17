import re
from collections import Counter

path = r'D:\Agent_Hub\agents\Book_Writer_Agent\data\workspace\book\ch 2.3\literature_review_2.md'
with open(path, 'r', encoding='utf-8') as f:
    c = f.read()

ids = [int(x) for x in re.findall(r'### \[(\d+)\]\.', c)]
cnt = Counter(ids)
print('Task ID -> chunk count:')
for k, v in sorted(cnt.items()):
    print(f'  Task {k}: {v} chunks')

h4 = re.findall(r'#### \d+\.', c)
print(f'\nH4 dims: {len(h4)}')
print(f'Expected H4 (59*6): {59*6}')
print(f'H4/H3 ratio: {len(h4)/59:.1f}')

# Check for Task 16 content
t16 = re.findall(r'### \[16\]\..+', c)
print(f'\nTask 16 entries: {len(t16)}')
for t in t16:
    print(f'  {t[:80]}')
