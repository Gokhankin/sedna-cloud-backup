
with open('index.html', 'r', encoding='utf-8') as f:
    html = f.read()

import re
idx = html.find('function renderRoomGrid()')
print(html[idx:idx+3500].encode('ascii', 'replace').decode('ascii'))
