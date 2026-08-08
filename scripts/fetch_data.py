import pyodbc
from datetime import datetime

def query_daily_data():
    conn_str = "DRIVER={ODBC Driver 18 for SQL Server};SERVER=192.168.0.41,1433;DATABASE=SednaAdakoy;UID=gokhan;PWD=Ad!!2025!!;TrustServerCertificate=yes;"
    conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()
    
    today = datetime.now().strftime('%Y-%m-%d 00:00:00')
    
    print(f"--- Querying Data for {today} ---")
    try:
        # Check Arrivals
        cursor.execute(f"SELECT StatusCode, COUNT(*) FROM Reservation WHERE CheckinDate = '{today}' GROUP BY StatusCode")
        print("Arrivals by StatusCode:", cursor.fetchall())
        
        # Check Departures
        cursor.execute(f"SELECT StatusCode, COUNT(*) FROM Reservation WHERE CheckOutDate = '{today}' GROUP BY StatusCode")
        print("Departures by StatusCode:", cursor.fetchall())
        
        # Check In-House (Checkin <= today, CheckOut > today)
        cursor.execute(f"SELECT StatusCode, COUNT(*) FROM Reservation WHERE CheckinDate <= '{today}' AND CheckOutDate > '{today}' GROUP BY StatusCode")
        print("In-House by StatusCode:", cursor.fetchall())
        
    except Exception as e:
        print("Error:", e)
        
    # Also get the exact columns to be sure
    cursor.execute("SELECT TOP 1 * FROM Reservation")
    columns = [column[0] for column in cursor.description]
    print("\nColumns in Reservation:")
    print(columns)

if __name__ == "__main__":
    query_daily_data()
