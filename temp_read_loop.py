
with open('sedna_sync.py', 'r', encoding='utf-8') as f:
    code = f.read()

import re
idx = code.find('for i in range(8):')
print(code[idx:idx+2500].encode('ascii', 'replace').decode('ascii'))
