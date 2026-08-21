import json

with open('daily_snapshot.json', 'r', encoding='utf-8') as f:
    snap = json.load(f)

by_date = snap.get('by_date', {})

pdf_pax = {
    '2026-08-21': 149,
    '2026-08-22': 128,
    '2026-08-23': 91,
    '2026-08-24': 90,
    '2026-08-25': 79,
    '2026-08-26': 82,
    '2026-08-27': 83,
    '2026-08-28': 77,
}

print(f"{'Tarih':<12} | {'PDF TotalPax':<15} | {'Hesaplanan InHouse Pax Sum':<30} | {'Fark':<10}")
print("-" * 75)

for d, v in sorted(by_date.items()):
    inh = v.get('inhouse', [])
    calc_pax = sum(int(g.get('Pax') or 0) for g in inh)
    calc_pax_childs = sum(int(g.get('Pax') or 0) + int(g.get('Childs') or 0) for g in inh)
    pdf_v = pdf_pax.get(d, 'N/A')
    diff = calc_pax - pdf_v if isinstance(pdf_v, int) else 'N/A'
    print(f"{d:<12} | {pdf_v:<15} | PaxSum: {calc_pax:<5} (Pax+Child: {calc_pax_childs}) | {diff:<10}")
