import pyodbc
import json
from datetime import datetime

def explore_db():
    conn_str = "DRIVER={ODBC Driver 18 for SQL Server};SERVER=192.168.0.41,1433;DATABASE=SednaAdakoy;UID=gokhan;PWD=Ad!!2025!!;TrustServerCertificate=yes;"
    
    try:
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()
        
        today = datetime.now().strftime('%Y-%m-%d 00:00:00')
        
        # Check tables related to reservation
        print("--- Finding Reservation Tables ---")
        cursor.execute("""
            SELECT t.name as TableName, c.name as ColumnName
            FROM sys.tables t
            INNER JOIN sys.columns c ON t.object_id = c.object_id
            WHERE t.name LIKE '%Res%' OR t.name LIKE '%Guest%'
            ORDER BY t.name
        """)
        
        tables = {}
        for row in cursor.fetchall():
            t, c = row
            if t not in tables:
                tables[t] = []
            tables[t].append(c)
            
        # specifically look for columns like CheckIn, CheckOut, Arrival, Departure, SDate, EDate in Res table
        if 'Res' in tables:
            print("Columns in Res table:")
            print([c for c in tables['Res'] if 'date' in c.lower() or 'day' in c.lower() or 'in' in c.lower() or 'out' in c.lower() or 'stat' in c.lower()])
            
            print(f"\n--- Checking Arrival records for {today} ---")
            # Let's try guessing the columns: Name, SDate, EDate, Status
            try:
                cursor.execute(f"SELECT TOP 5 ResName, SDate, EDate, ResStatus FROM Res WHERE SDate = '{today}'")
                for row in cursor.fetchall():
                    print("Arr:", row)
            except Exception as e:
                print("Guess 1 failed:", e)
                try:
                    cursor.execute(f"SELECT TOP 5 ResName, CheckInDate, CheckOutDate, Status FROM Res WHERE CheckInDate = '{today}'")
                    for row in cursor.fetchall():
                        print("Arr2:", row)
                except Exception as e2:
                    print("Guess 2 failed:", e2)

    except Exception as e:
        print("DB Connection Error:", e)

if __name__ == "__main__":
    explore_db()
