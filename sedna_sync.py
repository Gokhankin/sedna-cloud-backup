import pyodbc
import json
from datetime import datetime, timedelta
import os
import requests
from config import get_db_connection, get_firebase_url

def dictfetchall(cursor):
    "Return all rows from a cursor as a dict"
    columns = [col[0] for col in cursor.description]
    return [
        dict(zip(columns, row))
        for row in cursor.fetchall()
    ]

def extract_daily_data():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    today_dt = datetime.now()
    today_iso = today_dt.strftime('%Y-%m-%d')
    
    # Calculate range: today to today + 7 days
    today_date = today_dt.date()
    min_date_str = today_date.strftime('%Y%m%d')
    max_date_str = (today_date + timedelta(days=7)).strftime('%Y%m%d')
    
    # Fetch Reservations in date range
    # CheckinDate <= today+7 AND CheckOutDate >= today
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
    
    # Format dates and decimal values in-place
    for r in reservations:
        if r.get('CheckinDate'):
            r['CheckinDate'] = r['CheckinDate'].strftime('%Y-%m-%d')
        if r.get('CheckOutDate'):
            r['CheckOutDate'] = r['CheckOutDate'].strftime('%Y-%m-%d')
        if 'ExtraFolioBalance' in r and r['ExtraFolioBalance'] is not None:
            r['ExtraFolioBalance'] = float(r['ExtraFolioBalance'])
            
    # Fetch Housekeeping Status (ForeCast = 1 returns exactly the 111 sellable rooms)
    cursor.execute("""
        SELECT Room, RoomTypeCode, DirtyClean, HkStatus, OccVac 
        FROM Room 
        WHERE ForeCast = 1
    """)
    hk_data = dictfetchall(cursor)
    
    # Generate multi-day lists
    by_date = {}
    
    for i in range(8):
        date_d = today_date + timedelta(days=i)
        date_str = date_d.strftime('%Y-%m-%d')
        
        arr_list = []
        dep_list = []
        inh_list = []
        noshow_list = []
        
        for r in reservations:
            checkin = r.get('CheckinDate')
            checkout = r.get('CheckOutDate')
            status = r.get('Status')
            
            # Copy to avoid side-effects if we modify fields
            r_copy = dict(r)
            
            # Helper to check if it's a no-show
            v = (r_copy.get('Voucher') or '').upper()
            f = (r_copy.get('FirstName1') or '').upper()
            l = (r_copy.get('LastName1') or '').upper()
            rem = (r_copy.get('Remark') or '').upper()
            res_rem = (r_copy.get('ResRemark') or '').upper()
            
            ns_keywords = ['NOSHOW', 'NO-SHOW', 'NO SHOW', 'GELMEDI', 'GELMEDİ', 'NO_SHOW']
            is_ns = any(any(kw in field for kw in ns_keywords) for field in [v, f, l, rem, res_rem])
            
            if is_ns:
                if checkin <= date_str and checkout >= date_str:
                    noshow_list.append(r_copy)
                continue  # Exclude no-shows from active lists
            
            if date_str == today_iso:
                # Arrivals today: CheckinDate == date_str AND Status == 1 (Bekleyen Girişler - Henüz Check-in yapılmamış)
                if status == 1 and checkin == date_str:
                    arr_list.append(r_copy)
                    
                # Departures today: CheckOutDate == date_str AND Status == 2 (Henüz Check-out yapılmamış In-House misafirler)
                if status == 2 and checkout == date_str:
                    dep_list.append(r_copy)
                    
                # In-House today: Status == 2 (checked in)
                if status == 2:
                    inh_list.append(r_copy)
            else:
                # Future dates: include active reservations (Status 1 and 2)
                if status in (1, 2) and checkin == date_str:
                    arr_list.append(r_copy)

                if status in (1, 2) and checkout == date_str:
                    dep_list.append(r_copy)

                if status in (1, 2) and checkin <= date_str and checkout > date_str:
                    inh_list.append(r_copy)
                
        by_date[date_str] = {
            "summary": {
                "arrivals_count": len(arr_list),
                "departures_count": len(dep_list),
                "inhouse_count": len(inh_list),
                "noshow_count": len(noshow_list)
            },
            "arrivals": arr_list,
            "departures": dep_list,
            "inhouse": inh_list,
            "noshow": noshow_list
        }
        
    # Maintain backward-compatible "data" section for today
    today_data = by_date.get(today_iso, {
        "arrivals": [],
        "departures": [],
        "inhouse": [],
        "noshow": []
    })
    
    snapshot = {
        "sync_time": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "report_date": today_iso,
        "summary": {
            "arrivals_count": len(today_data["arrivals"]),
            "departures_count": len(today_data["departures"]),
            "inhouse_count": len(today_data["inhouse"]),
            "noshow_count": len(today_data["noshow"]),
            "hk_count": len(hk_data)
        },
        "data": {
            "arrivals": today_data["arrivals"],
            "departures": today_data["departures"],
            "inhouse": today_data["inhouse"],
            "noshow": today_data["noshow"],
            "hk": hk_data
        },
        "by_date": by_date
    }
    
    output_path = os.path.join(os.path.dirname(__file__), 'daily_snapshot.json')
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(snapshot, f, ensure_ascii=False, indent=2)
        
    print(f"Data extracted successfully! Snapshot saved to {output_path}")
    print(f"Today's counts -> Arrivals: {len(today_data['arrivals'])} | Departures: {len(today_data['departures'])} | In-House: {len(today_data['inhouse'])}")
    
    # Push to Firebase Realtime Database
    firebase_url = get_firebase_url()
    print(f"Pushing data to Firebase: {firebase_url}")
    try:
        response = requests.put(firebase_url, json=snapshot)
        if response.status_code == 200:
            print("Successfully pushed to Firebase Cloud!")
        else:
            print(f"Failed to push to Firebase. Status Code: {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"Error pushing to Firebase: {e}")
        
    return snapshot

if __name__ == "__main__":
    extract_daily_data()
