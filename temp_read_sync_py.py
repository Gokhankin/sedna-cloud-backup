
with open('sedna_sync.py', 'r', encoding='utf-8') as f:
    code = f.read()

print("Length of sedna_sync.py:", len(code))
# Print sections related to forecast or daily_snapshot or occupancy
import re
matches = [m.start() for m in re.finditer(r'forecast|occ|daily|sold|checkin|status', code, re.IGNORECASE)]
print(f"Found {len(matches)} matches")
for idx in matches[:20]:
    print(code[max(0, idx-50):min(len(code), idx+200)].encode('ascii', 'replace').decode('ascii'))
    print("-" * 50)
