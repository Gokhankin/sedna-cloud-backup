import sys
from datetime import datetime, timedelta
from sedna_sync import get_db_connection, dictfetchall

conn = get_db_connection()
cursor = conn.cursor()

today_dt = datetime.now()
today_date = today_dt.date()
min_date_str = today_date.strftime('%Y%m%d')
max_date_str = (today_date + timedelta(days=10)).strftime('%Y%m%d')

query = """
    SELECT 
        r.Voucher, r.GroupNo, r.RecId,
        r.FirstName1, r.LastName1,
        r.CheckinDate, r.CheckOutDate,
        r.Room, r.RoomType, r.Board,
        r.Pax, r.Childs, r.AgencyId, r.ExtraFolioBalance,
        r.ResRemark, r.FlightArrival, r.FlightDeparture,
        r.Status,
        a.AgencyCode
    FROM Reservation r
    LEFT JOIN Agency a ON r.AgencyId = a.RecId
    WHERE r.StatusCode IN (0, 1, 2, 3)
      AND r.CheckinDate <= ? 
      AND r.CheckOutDate >= ?
"""

cursor.execute(query, (max_date_str, min_date_str))
reservations = dictfetchall(cursor)

for r in reservations:
    if r.get('CheckinDate'):
        r['CheckinDate'] = r['CheckinDate'].strftime('%Y-%m-%d')
    if r.get('CheckOutDate'):
        r['CheckOutDate'] = r['CheckOutDate'].strftime('%Y-%m-%d')

pdf_pdf_sold = {
    '2026-08-21': 83,
    '2026-08-22': 72,
    '2026-08-23': 52,
    '2026-08-24': 50,
    '2026-08-25': 43,
    '2026-08-26': 46,
    '2026-08-27': 46,
    '2026-08-28': 44,
}

print(f"{'Tarih':<12} | {'PDF Sold':<10} | {'Eski Inhouse':<12} | {'Yeni Inhouse':<12} | {'Fark (Yeni - PDF)':<18}")
print("-" * 75)

for i in range(8):
    date_d = today_date + timedelta(days=i)
    date_str = date_d.strftime('%Y-%m-%d')
    
    old_inh = []
    new_inh = []
    
    for r in reservations:
        checkin = r.get('CheckinDate')
        checkout = r.get('CheckOutDate')
        status = r.get('Status')
        
        # Check no-show
        v = (r.get('Voucher') or '').upper()
        f = (r.get('FirstName1') or '').upper()
        l = (r.get('LastName1') or '').upper()
        rem = (r.get('Remark') or '').upper()
        res_rem = (r.get('ResRemark') or '').upper()
        ns_keywords = ['NOSHOW', 'NO-SHOW', 'NO SHOW', 'GELMEDI', 'GELMED?', 'NO_SHOW']
        if any(any(kw in field for kw in ns_keywords) for field in [v, f, l, rem, res_rem]):
            continue
            
        # Old logic:
        if date_str == today_date.strftime('%Y-%m-%d'):
            if status == 2:
                old_inh.append(r)
        else:
            if status == 2 and checkin <= date_str and checkout > date_str:
                old_inh.append(r)
            elif status == 1 and checkin < date_str and checkout > date_str:
                old_inh.append(r)
                
        # New correct logic:
        # A reservation is in-house / occupied for date_str if:
        # CheckinDate <= date_str AND CheckOutDate > date_str AND Status IN (1, 2)
        if status in (1, 2) and checkin <= date_str and checkout > date_str:
            new_inh.append(r)
            
    pdf_val = pdf_pdf_sold.get(date_str, 'N/A')
    diff = len(new_inh) - pdf_val if isinstance(pdf_val, int) else 'N/A'
    print(f"{date_str:<12} | {str(pdf_val):<10} | {len(old_inh):<12} | {len(new_inh):<12} | {str(diff):<18}")

conn.close()
