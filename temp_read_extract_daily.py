
with open('sedna_sync.py', 'r', encoding='utf-8') as f:
    code = f.read()

import re
idx = code.find('def extract_daily_data():')
print(code[idx:idx+4000].encode('ascii', 'replace').decode('ascii'))
