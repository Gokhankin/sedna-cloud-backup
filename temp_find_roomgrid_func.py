
with open('index.html', 'r', encoding='utf-8') as f:
    html = f.read()

import re
matches = [m.start() for m in re.finditer(r'roomgrid|renderGrid|renderRoomGrid|room-card|buildGrid|updateView', html, re.IGNORECASE)]
print(f"Found {len(matches)} matches in index.html")
for idx in matches[:15]:
    print(html[max(0, idx-50):min(len(html), idx+300)].encode('ascii', 'replace').decode('ascii'))
    print("-" * 50)
