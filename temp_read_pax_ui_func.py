
with open('index.html', 'r', encoding='utf-8') as f:
    html = f.read()

import re
idx = html.find('let inhousePax = 0;')
print(html[idx:idx+1500].encode('ascii', 'replace').decode('ascii'))
