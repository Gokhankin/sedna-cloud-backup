
with open('index.html', 'r', encoding='utf-8') as f:
    html = f.read()

import re
matches = [m.start() for m in re.finditer(r'matris|matrix|plan|room|grid|renderRoom|renderMatrix', html, re.IGNORECASE)]
print(f"Found {len(matches)} matches in index.html")
for idx in matches[:20]:
    print(html[max(0, idx-30):min(len(html), idx+150)].encode('ascii', 'replace').decode('ascii'))
    print("-" * 50)
