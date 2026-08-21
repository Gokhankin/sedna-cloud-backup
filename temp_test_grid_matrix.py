import json

with open('daily_snapshot.json', 'r', encoding='utf-8') as f:
    snap = json.load(f)

by_date = snap.get('by_date', {})

print(f"{'Tarih':<12} | {'In-House':<10} | {'Oda No Dolu':<15} | {'Atanmamis Oda':<15}")
print("-" * 60)

for d, v in sorted(by_date.items()):
    inh = v.get('inhouse', [])
    with_room = sum(1 for g in inh if g.get('Room') and str(g.get('Room')).strip())
    without_room = len(inh) - with_room
    print(f"{d:<12} | {len(inh):<10} | {with_room:<15} | {without_room:<15}")
