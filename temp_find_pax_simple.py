
with open('index.html', 'r', encoding='utf-8') as f:
    html = f.read()

import re
matches = [m.start() for m in re.finditer(r'pax', html, re.IGNORECASE)]
print(f"Found {len(matches)} matches")
for idx in matches[:10]:
    print(html[max(0, idx-40):min(len(html), idx+100)].encode('ascii', 'replace').decode('ascii'))
    print("-" * 40)
