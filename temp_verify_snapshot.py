import json

with open('daily_snapshot.json', 'r', encoding='utf-8') as f:
    snap = json.load(f)

by_date = snap.get('by_date', {})
print(f"{'Tarih':<12} | {'In-House':<10} | {'Giris':<8} | {'Cikis':<8} | {'Bos Oda':<8}")
print("-" * 55)
for d, v in sorted(by_date.items()):
    s = v.get('summary', {})
    print(f"{d:<12} | {s.get('inhouse_count', 0):<10} | {s.get('arrivals_count', 0):<8} | {s.get('departures_count', 0):<8} | {s.get('vacant_count', 0):<8}")
