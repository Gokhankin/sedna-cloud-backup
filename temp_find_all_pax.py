
with open('index.html', 'r', encoding='utf-8') as f:
    html = f.read()

import re
matches = [m.start() for m in re.finditer(r'pax', html, re.IGNORECASE)]
print(f"Found {len(matches)} matches in index.html")
for idx in matches:
    snippet = html[max(0, idx-40):min(len(html), idx+120)].replace('
', ' ')
    if 'document.getElementById' in snippet or 'innerText' in snippet or 'innerHTML' in snippet or '=' in snippet:
        print(snippet)
        print("-" * 50)
