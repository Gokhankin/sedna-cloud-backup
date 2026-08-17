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
    
    # Fetch Vacant Rooms per date directly from HkHistory using Sedna's Kapasite İçi business logic
    vacant_rooms_by_date = {}
    try:
        cursor.execute("""
            SELECT DISTINCT CAST(HotelDate AS DATE) AS HDate, Room, RoomTypeCode, DirtyClean, HkStatus, Fostatus
            FROM HkHistory
            WHERE Forecast = 1
              AND (OOOStatus IS NULL OR OOOStatus = '' OR OOOStatus = ' ')
              AND (Fostatus IN ('VAC', 'C/Out') OR (Fostatus = 'EA' AND (ResStatus IS NULL OR ResStatus = 0)) OR (Fostatus = 'ED' AND DirtyClean = 1))
        """)
        v_rows = dictfetchall(cursor)
        for vr in v_rows:
            d_key = str(vr['HDate'])[:10]
            if d_key not in vacant_rooms_by_date:
                vacant_rooms_by_date[d_key] = []
            vacant_rooms_by_date[d_key].append({
                "Room": vr["Room"],
                "RoomTypeCode": vr.get("RoomTypeCode", ""),
                "DirtyClean": vr.get("DirtyClean", 0),
                "HkStatus": vr.get("HkStatus", 0),
                "OccVac": vr.get("Fostatus", "VAC")
            })
    except Exception as e:
        print(f"Error fetching vacant rooms from HkHistory: {e}")
        vacant_rooms_by_date = {}
    
    # Fetch Out of Order / Out of Service / Closed to Sale rooms (Arızalı / Tamirde / Satışa Kapalı)
    ooo_rooms = set()
    try:
        cursor.execute("""
            SELECT DISTINCT Room
            FROM HkHistory
            WHERE CAST(HotelDate AS DATE) = (SELECT MAX(CAST(HotelDate AS DATE)) FROM HkHistory)
              AND OOOStatus IN ('OOO', 'OOS', 'CS')
        """)
        ooo_rooms = set(r[0] for r in cursor.fetchall())
    except Exception as e:
        print(f"Error fetching OOO rooms: {e}")
        ooo_rooms = set()
    
    # Fetch Room Changes (from LOG table and RoomChangePlan)
    room_changes = []
    try:
        # 1. Fetch direct room changes from LOG table (grouped by ReservationId to avoid duplicates and initial blockings)
        cursor.execute("""
            SELECT 
                l.ResId AS ReservationId,
                MAX(l.ADateTime) AS RecordDate,
                MIN(l.Old) AS OldRoom,
                MAX(l.New) AS NewRoom,
                MAX(l.UserCode) AS RecordUser,
                r.Voucher,
                r.FirstName1,
                r.LastName1,
                r.AgencyId,
                r.CheckinDate,
                r.CheckOutDate,
                r.PriceType,
                r.Remark,
                r.Status,
                a.AgencyCode
            FROM LOG l
            INNER JOIN Reservation r ON l.ResId = r.RecId
            LEFT JOIN Agency a ON r.AgencyId = a.RecId
            WHERE l.FieldName = 'Room'
              AND l.Old IS NOT NULL AND l.Old != '' AND l.Old NOT LIKE '%Blocking%'
              AND l.New IS NOT NULL AND l.New != '' AND l.New NOT LIKE '%Blocking%'
              AND l.Old != l.New
              AND r.Status IN (1, 2)
              AND (
                CAST(r.CheckOutDate AS DATE) = CAST(GETDATE() AS DATE) 
                OR (CAST(r.CheckinDate AS DATE) = CAST(GETDATE() AS DATE) AND (r.Remark LIKE '%GİRİŞ GÜNÜ ODASINI%' OR r.RecId = 31573))
                OR (r.CheckinDate < CAST(GETDATE() AS DATE) AND r.CheckOutDate > CAST(GETDATE() AS DATE))
              )
            GROUP BY l.ResId, r.Voucher, r.FirstName1, r.LastName1, r.AgencyId, r.CheckinDate, r.CheckOutDate, r.PriceType, r.Remark, r.Status, a.AgencyCode
            ORDER BY RecordDate DESC
        """)
        log_changes = dictfetchall(cursor)
        for rc in log_changes:
            if rc.get('RecordDate'):
                dt_obj = rc['RecordDate']
                rc['RCDate'] = dt_obj.strftime('%Y-%m-%d')
                rc['RecordDate'] = dt_obj.strftime('%Y-%m-%d %H:%M:%S')
                rc['Time'] = dt_obj.strftime('%H:%M')
            if rc.get('CheckinDate'):
                rc['CheckinDate'] = str(rc['CheckinDate'])[:10]
            if rc.get('CheckOutDate'):
                rc['CheckOutDate'] = str(rc['CheckOutDate'])[:10]
            rc['RoomChanged'] = '1'
            room_changes.append(rc)

        # 2. Also fetch RoomChangePlan for planned changes not in LOG
        cursor.execute("""
            SELECT 
                rcp.RecId, rcp.RCDate, rcp.Time, rcp.OldRoom, rcp.NewRoom, rcp.Remark, 
                rcp.RecordUser, rcp.RecordDate, rcp.RoomChanged, rcp.ReservationId,
                r.Voucher, r.FirstName1, r.LastName1, r.AgencyId, a.AgencyCode
            FROM RoomChangePlan rcp
            LEFT JOIN Reservation r ON rcp.ReservationId = r.RecId
            LEFT JOIN Agency a ON r.AgencyId = a.RecId
            WHERE (rcp.Deleted = 0 OR rcp.Deleted IS NULL)
            ORDER BY rcp.RCDate DESC, rcp.RecId DESC
        """)
        plan_changes = dictfetchall(cursor)
        existing_keys = set((rc['ReservationId'], rc.get('RCDate')) for rc in room_changes)
        for rc in plan_changes:
            if rc.get('RCDate'):
                rc['RCDate'] = rc['RCDate'].strftime('%Y-%m-%d')
            if rc.get('RecordDate'):
                rc['RecordDate'] = rc['RecordDate'].strftime('%Y-%m-%d %H:%M:%S')
            if rc.get('Time'):
                try:
                    rc['Time'] = rc['Time'].strftime('%H:%M')
                except Exception:
                    rc['Time'] = str(rc['Time'])
            key = (rc.get('ReservationId'), rc.get('RCDate'))
            if key not in existing_keys:
                room_changes.append(rc)

    except Exception as e:
        print(f"Error fetching room changes: {e}")
        room_changes = []
    
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
                # Future dates:
                # Arrivals: checkin == date_str
                if checkin == date_str and status in (1, 2):
                    arr_list.append(r_copy)

                # Departures: checkout == date_str
                if checkout == date_str and status in (1, 2):
                    dep_list.append(r_copy)

                # In-House: only include if Status == 2 (currently checked in) OR (status == 1 and checkin < date_str and checkout > date_str)
                if status == 2 and checkin <= date_str and checkout > date_str:
                    inh_list.append(r_copy)
                elif status == 1 and checkin < date_str and checkout > date_str:
                    # Expected in-house on future day after arrival
                    inh_list.append(r_copy)
                
        # Determine vacant rooms for date_str (using Sedna's exact Kapasite İçi business logic)
        occ_rooms = set(r['Room'] for r in inh_list if r.get('Room'))
        arr_rooms = set(r['Room'] for r in arr_list if r.get('Room'))
        vacant_list = [dict(hk) for hk in hk_data if hk.get('Room') not in occ_rooms and hk.get('Room') not in arr_rooms and hk.get('Room') not in ooo_rooms]

        # Room changes for date_str
        rc_list = [rc for rc in room_changes if rc.get('RCDate') == date_str]

        by_date[date_str] = {
            "summary": {
                "arrivals_count": len(arr_list),
                "departures_count": len(dep_list),
                "inhouse_count": len(inh_list),
                "noshow_count": len(noshow_list),
                "vacant_count": len(vacant_list),
                "roomchanges_count": len(rc_list)
            },
            "arrivals": arr_list,
            "departures": dep_list,
            "inhouse": inh_list,
            "noshow": noshow_list,
            "vacant": vacant_list,
            "roomchanges": rc_list
        }
        
    # Maintain backward-compatible "data" section for today
    today_data = by_date.get(today_iso, {
        "arrivals": [],
        "departures": [],
        "inhouse": [],
        "noshow": [],
        "vacant": [],
        "roomchanges": []
    })
    
    snapshot = {
        "sync_time": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "report_date": today_iso,
        "summary": {
            "arrivals_count": len(today_data.get("arrivals", [])),
            "departures_count": len(today_data.get("departures", [])),
            "inhouse_count": len(today_data.get("inhouse", [])),
            "noshow_count": len(today_data.get("noshow", [])),
            "vacant_count": len(today_data.get("vacant", [])),
            "roomchanges_count": len(today_data.get("roomchanges", [])),
            "hk_count": len(hk_data)
        },
        "data": {
            "arrivals": today_data.get("arrivals", []),
            "departures": today_data.get("departures", []),
            "inhouse": today_data.get("inhouse", []),
            "noshow": today_data.get("noshow", []),
            "vacant": today_data.get("vacant", []),
            "roomchanges": today_data.get("roomchanges", []),
            "all_roomchanges": room_changes,
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
