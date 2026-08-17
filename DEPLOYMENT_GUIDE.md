# Sedna Cloud — Deployment & Synchronization Guidelines

## 📌 Zorunlu Deployment Kuralı

Sedna Cloud projesinde yapılan **HER** frontend (`index.html`) veya backend (`sedna_sync.py`) kod değişikliği sonrasında, değişiklikler vakit kaybetmeksizin **Society Makinesi (`192.168.0.128`)** üzerindeki canlı üretim dizinine deploy edilecektir:

- **Canlı Sunucu Dizini:** `/home/society/Masaüstü/sedna_cloud_backup/`
- **Hedef Dosyalar:**
  1. `/home/society/Masaüstü/sedna_cloud_backup/index.html`
  2. `/home/society/Masaüstü/sedna_cloud_backup/dashboard/index.html` (Alt dizin senkronizasyonu)
  3. `/home/society/Masaüstü/sedna_cloud_backup/sedna_sync.py`

---

## 🚀 Standart Otomatik Deploy Süreci

Kod düzenlemesi biter bitmez aşağıdaki script vasıtasıyla SSH/SFTP üzerinden sunucuya otomatik aktarım sağlanacaktır:

```bash
python "c:\Users\gokha\OneDrive\Desktop\triple-cassini\eski projeler\scratch\deploy_to_society_server.py"
```

### Sunucu Erişim Bilgileri:
- **IP:** `192.168.0.128`
- **Kullanıcı:** `society`
- **SSH Port:** `22`

---

## ⚙️ İş Mantığı (Business Logic) & Arama Kuralları

1. **Boş Odalar (Kapasite İçi) Hesabı:**
   - Formul: `Toplam Satılabilir (Forecast=1) Oda (111) - In-House Odalar - Bugün Giriş Bekleyen (Arrival Assigned) Odalar - Arızalı/Blokeli (OOO/OOS/CS) Odalar`
   - Bu hesaplama sayesinde Sedna Masaüstü raporu ile Cloud dashboard'un Boş Oda sayısı birebir eşitlenir.

2. **Arama & Konaklayan (In-House) Sekme Mantığı:**
   - "Konaklayanlar (In-House)" sekmesinde arama yapılırken, henüz giriş yapmamış ileri tarihli rezervasyonlar kesinlikle listelenmez (`CheckinDate <= Bugün` veya `Status == 2` şartı aranır).
   - İleri tarihli rezervasyonlar sadece **"Gelecekler (Arrivals)"** sekmesinde gösterilir.
3. **Senkronizasyon Sıklığı (5 Dakika):**
   - Sunucu tarafındaki `sedna_sync.py` cron zamanlaması: `*/5 * * * *` (Her 5 dakikada bir).
   - Frontend `index.html` tarafındaki otomatik yenileme (auto-refresh) süresi: `300000 ms` (Her 5 dakikada bir).
