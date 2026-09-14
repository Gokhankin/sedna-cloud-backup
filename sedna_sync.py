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
    
    # Calculate range: yesterday to today + 7 days
    today_date = today_dt.date()
    min_date_str = (today_date - timedelta(days=1)).strftime('%Y%m%d')
    max_date_str = (today_date + timedelta(days=7)).strftime('%Y%m%d')
    
    # Fetch Reservations in date range
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
        ORDER BY Room
    """)
    hk_data = dictfetchall(cursor)
    
    # Fetch Closed / OOO / OOS / CS rooms per date directly from DailyDetail (Status IN 2, 3, 4)
    closed_rooms_by_date = {}
    try:
        cursor.execute("""
            SELECT StayDate, Room
            FROM DailyDetail
            WHERE StayDate >= ? AND StayDate <= ?
              AND Status IN (2, 3, 4)
              AND ReservationId = 0
        """, (min_date_str, max_date_str))
        for row in cursor.fetchall():
            s_d = row[0].strftime('%Y-%m-%d') if hasattr(row[0], 'strftime') else str(row[0])[:10]
            if s_d not in closed_rooms_by_date:
                closed_rooms_by_date[s_d] = set()
            closed_rooms_by_date[s_d].add(row[1])
    except Exception as e:
        print(f"Error fetching closed rooms: {e}")
        closed_rooms_by_date = {}
    
    # Fetch Room Changes directly using Sedna's official RoomChangeList SP + RoomChangePlan
    room_changes = []
    try:
        # 1. Fetch from official RoomChangeList for date range
        for i in range(-1, 8):
            d_loop = today_date + timedelta(days=i)
            d_loop_str = d_loop.strftime('%Y-%m-%d')
            try:
                cursor.execute("""
                    SET DATEFORMAT ymd;
                    EXEC [dbo].[RoomChangeList] @CompanyCode = 'CLUBADAKOY', @HotelDate = ?
                """, (d_loop_str,))
                for row_dict in dictfetchall(cursor):
                    rc_item = {
                        "ReservationId": row_dict.get('RecId'),
                        "Voucher": row_dict.get('Voucher'),
                        "FirstName1": row_dict.get('FirstName1'),
                        "LastName1": row_dict.get('LastName1'),
                        "OldRoom": row_dict.get('DailyRoom'),
                        "NewRoom": row_dict.get('Room'),
                        "RecordUser": row_dict.get('RecordUser') or 'Sedna',
                        "RecordDate": d_loop_str,
                        "RCDate": d_loop_str,
                        "Time": "",
                        "CheckinDate": str(row_dict.get('CheckinDate'))[:10] if row_dict.get('CheckinDate') else '',
                        "CheckOutDate": str(row_dict.get('CheckOutDate'))[:10] if row_dict.get('CheckOutDate') else '',
                        "AgencyCode": row_dict.get('AgencyCode'),
                        "RoomChanged": '1'
                    }
                    room_changes.append(rc_item)
            except Exception as e:
                print(f"Error executing RoomChangeList for {d_loop_str}: {e}")

        # 2. Also fetch RoomChangePlan for planned changes
        cursor.execute("""
            SELECT 
                rcp.RecId, rcp.RCDate, rcp.Time, rcp.OldRoom, rcp.NewRoom, rcp.Remark, 
                rcp.RecordUser, rcp.RecordDate, rcp.RoomChanged, rcp.ReservationId,
                r.Voucher, r.FirstName1, r.LastName1, r.AgencyId, a.AgencyCode
            FROM RoomChangePlan rcp
            LEFT JOIN Reservation r ON rcp.ReservationId = r.RecId
            LEFT JOIN Agency a ON r.AgencyId = a.RecId
            WHERE (rcp.Deleted = 0 OR rcp.Deleted IS NULL)
              AND CONVERT(VARCHAR(8), rcp.RCDate, 112) >= ?
            ORDER BY rcp.RCDate DESC, rcp.RecId DESC
        """, (min_date_str,))
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
    
    # Fetch exact Sedna General Forecast Analysis totals per date directly from official SQL Stored Procedure
    forecast_by_date = {}
    try:
        d_begin = (today_dt - timedelta(days=1)).strftime('%m/%d/%Y')
        d_end = (today_dt + timedelta(days=7)).strftime('%m/%d/%Y')
        sp_query = """
            SET NOCOUNT ON;
            SET DATEFORMAT mdy;
            EXEC [dbo].[0101001_GeneralForecastAnalysis_OR]
                @DateBegin = ?,
                @DateEnd = ?,
                @CompanyRecId = 1,
                @Section = '',
                @Agency = '',
                @Company = '',
                @Source = '',
                @Individual = '',
                @AgencyGroup = '',
                @MainMarket = '',
                @SubMarket = '',
                @Market = '',
                @Nationality = '',
                @PriceType = '',
                @RoomType = '',
                @BedType = '',
                @Board = '',
                @StayType = '',
                @VipType = '',
                @OOO = 1,
                @CS = 1,
                @CB = 1,
                @PM = 1,
                @Share = 1,
                @Option = -1,
                @Definite = -1,
                @Tentative = -1,
                @Connection = 1,
                @HotelCode = ''
        """
        cursor.execute(sp_query, (d_begin, d_end))
        cols = [col[0] for col in cursor.description]
        for row in cursor.fetchall():
            row_dict = dict(zip(cols, row))
            s_date = row_dict['StayDate'].strftime('%Y-%m-%d') if hasattr(row_dict['StayDate'], 'strftime') else str(row_dict['StayDate'])[:10]
            adult = int(row_dict.get('Adult') or 0)
            paid_ch = int(row_dict.get('PaidChild') or 0)
            free_ch = int(row_dict.get('FreeChild') or 0)
            baby = int(row_dict.get('Baby') or 0)
            tot_pax = adult + paid_ch + free_ch + baby
            forecast_by_date[s_date] = {
                "forecast_rooms": int(row_dict.get('Sold_Room') or 0),
                "forecast_pax": tot_pax,
                "adult": adult,
                "cin_room": int(row_dict.get('Cin_Room') or 0),
                "cout_room": int(row_dict.get('Cout_Room') or 0),
                "cap": int(row_dict.get('Cap') or 111)
            }
        print('Forecast SP executed successfully:', forecast_by_date)
    except Exception as e:
        print(f"Error executing forecast SP: {e}")
        forecast_by_date = {}

    # Generate multi-day lists (Yesterday, Today, and Next 7 Days)
    by_date = {}
    
    for i in range(-1, 8):
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
            
            # Check if this reservation is marked as No-Show
            v = (r_copy.get('Voucher') or '').upper()
            rem = (r_copy.get('Remark') or '').upper()
            res_rem = (r_copy.get('ResRemark') or '').upper()
            ns_keywords = ['NOSHOW', 'NO-SHOW', 'NO SHOW', 'GELMEDI', 'GELMEDİ', 'NO_SHOW']
            is_ns = (status == 5) or any(any(kw in field for kw in ns_keywords) for field in [v, rem, res_rem])
            
            if is_ns:
                if checkin <= date_str and checkout >= date_str:
                    noshow_list.append(r_copy)
            
            if date_d < today_date:
                # Past dates (Yesterday):
                # Arrivals: checkin == date_str
                if checkin == date_str and status in (1, 2, 3):
                    arr_list.append(r_copy)
                # Departures: checkout == date_str
                if checkout == date_str and status in (2, 3):
                    dep_list.append(r_copy)
                # Inhouse on past date:
                if status in (1, 2, 3) and checkin <= date_str and checkout > date_str:
                    inh_list.append(r_copy)
            elif date_str == today_iso:
                # Arrivals today (Giriş Beklenen): CheckinDate == date_str AND Status == 1
                if checkin == date_str and status == 1:
                    arr_list.append(r_copy)
                    
                # Departures today (Çıkış Beklenen): CheckOutDate == date_str AND Status == 2
                if checkout == date_str and status == 2:
                    dep_list.append(r_copy)
                    
                # In-House today (Konaklayan / Odada): Status == 2
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

                # In-House / Occupied on future date: CheckinDate <= date_str AND CheckOutDate > date_str AND Status IN (1, 2)
                if status in (1, 2) and checkin <= date_str and checkout > date_str:
                    inh_list.append(r_copy)
                
        # Determine vacant rooms for date_str matching Sedna Ön Büro Kapasite İçi Boş Odalar
        closed_set = closed_rooms_by_date.get(date_str, set())
        occ_rooms = set(r['Room'] for r in inh_list if r.get('Room'))
        arr_rooms = set(r['Room'] for r in arr_list if r.get('Room'))
        vacant_list = [
            dict(hk) for hk in hk_data 
            if hk.get('Room') not in occ_rooms 
            and hk.get('Room') not in arr_rooms 
            and hk.get('Room') not in closed_set
        ]

        # Room changes for date_str
        rc_list = [rc for rc in room_changes if rc.get('RCDate') == date_str]

        fc_info = forecast_by_date.get(date_str, {})
        # EOD numbers are 100% from Sedna SQL General Forecast Analysis SP
        eod_room_count = fc_info.get("forecast_rooms", len(inh_list))
        eod_pax_count = fc_info.get("forecast_pax", sum(int(r.get('Pax') or 0) for r in inh_list))

        by_date[date_str] = {
            "summary": {
                "arrivals_count": len(arr_list),
                "departures_count": len(dep_list),
                "inhouse_count": len(inh_list),
                "noshow_count": len(noshow_list),
                "vacant_count": len(vacant_list),
                "roomchanges_count": len(rc_list),
                "eod_room_count": eod_room_count,
                "eod_pax_count": eod_pax_count
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
            "eod_room_count": forecast_by_date.get(today_iso, {}).get("forecast_rooms", max(0, len(today_data.get("inhouse", [])) + len(today_data.get("arrivals", [])) - len(today_data.get("departures", [])))),
            "eod_pax_count": forecast_by_date.get(today_iso, {}).get("forecast_pax", today_data.get("summary", {}).get("eod_pax_count", 0)),
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
    print(f"Today's counts -> Arrivals: {len(today_data['arrivals'])} | Departures: {len(today_data['departures'])} | In-House: {len(today_data['inhouse'])} | Vacant: {len(today_data['vacant'])} | RoomChanges: {len(today_data['roomchanges'])} | EOD Pax: {snapshot['summary']['eod_pax_count']}")
    
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
