
with open('index.html', 'r', encoding='utf-8') as f:
    html = f.read()

import re
matches = [m.start() for m in re.finditer(r'by_date|inhouse_count|inhouse|forecast|date-selector|occupancy', html, re.IGNORECASE)]
print(f"Found {len(matches)} matches in index.html")
for idx in matches[:15]:
    print(html[max(0, idx-50):min(len(html), idx+200)].encode('ascii', 'replace').decode('ascii'))
    print("-" * 50)
