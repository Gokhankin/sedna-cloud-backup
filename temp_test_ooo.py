import sys
from sedna_sync import get_db_connection, dictfetchall

conn = get_db_connection()
cursor = conn.cursor()

# 1. Total rooms with ForeCast = 1
cursor.execute("SELECT COUNT(*) FROM Room WHERE ForeCast = 1")
total_fc = cursor.fetchone()[0]

# 2. OOO rooms in HkHistory
cursor.execute("""
    SELECT DISTINCT Room, OOOStatus
    FROM HkHistory
    WHERE CAST(HotelDate AS DATE) = (SELECT MAX(CAST(HotelDate AS DATE)) FROM HkHistory)
      AND OOOStatus IN ('OOO', 'OOS', 'CS')
""")
ooo_rows = dictfetchall(cursor)

print(f"Total ForeCast = 1 Rooms in DB: {total_fc}")
print(f"Current OOO / OOS / CS Rooms: {ooo_rows}")
print(f"Net Sellable Capacity: {total_fc - len(ooo_rows)}")

conn.close()
