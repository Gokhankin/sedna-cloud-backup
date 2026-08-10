import os
import pyodbc
import base64

def load_env():
    """
    .env dosyasını otomatik okuyarak os.environ içerisine yükler.
    Şifreli / Base64 formatlı değişkenleri de çözerek güvenliği sağlar.
    """
    env_path = os.path.join(os.path.dirname(__file__), '.env')
    if os.path.exists(env_path):
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    k, v = line.split('=', 1)
                    os.environ[k.strip()] = v.strip()

# Dosya import edildiğinde otomatik yükle
load_env()

def get_db_connection_string():
    """
    Ortam değişkenlerinden SQL Server bağlantı cümlesini oluşturur.
    """
    driver = os.getenv("DB_DRIVER", "{ODBC Driver 18 for SQL Server}")
    server = os.getenv("DB_SERVER", "192.168.0.41,1433")
    database = os.getenv("DB_NAME", "SednaAdakoy")
    user = os.getenv("DB_USER", "gokhan")
    pwd = os.getenv("DB_PASSWORD", "Ad!!2025!!")
    
    # Şifre b64: prefix ile şifrelenmişse otomatik çöz
    if pwd.startswith("b64:"):
        try:
            pwd = base64.b64decode(pwd[4:]).decode('utf-8')
        except Exception:
            pass
            
    trust_cert = os.getenv("DB_TRUST_CERT", "yes")
    return f"DRIVER={driver};SERVER={server};DATABASE={database};UID={user};PWD={pwd};TrustServerCertificate={trust_cert};"

def get_db_connection():
    """
    SQL Server bağlantısı döndürür.
    """
    conn_str = get_db_connection_string()
    return pyodbc.connect(conn_str)

def get_firebase_url():
    """
    Firebase Realtime Database URL adresini auth parametresi ile döndürür.
    """
    base_url = os.getenv("FIREBASE_URL", "https://adakoy-default-rtdb.firebaseio.com/daily_snapshot.json")
    secret = os.getenv("FIREBASE_SECRET", "egKsRyn2xGkgNJJV7R2GbRQ2nYAZ7LLPcRzhjZYy").strip()
    if secret and "auth=" not in base_url:
        sep = "&" if "?" in base_url else "?"
        base_url = f"{base_url}{sep}auth={secret}"
    return base_url
