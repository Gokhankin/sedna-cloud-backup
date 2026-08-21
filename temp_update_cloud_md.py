with open('cloud.md', 'r', encoding='utf-8') as f:
    content = f.read()

new_entry = '''

---

### 🗓️ 21.08.2026 — İleri Tarihli Rezervasyon Forecast & Gün Sonu Pax Hesaplama Mantığı Düzeltmesi

#### 🚨 Tespit Edilen Problemler:
1. **İleri Tarihli Geceleme / Doluluk Sayısı Eksikliği:**
   `sedna_sync.py` betiğinde gelecek günler hesaplanırken `checkin < date_str` şartı bulunuyordu. Bu durum, o gün otele giriş yapacak yeni rezervasyonların (`checkin == date_str`) o gecenin konaklayan doluluğundan ve kişi sayısından (Pax) düşülmesine, dolayısıyla Sedna Desktop `General Forecast Analysis` PDF raporu ile uyuşmamasına neden oluyordu.
2. **Arayüz (UI) Gün Sonu Pax Çift Hesaplama Hatası:**
   `index.html` içerisindeki "Gün Sonu Pax" hesaplaması, gelecek tarihlerde `Konaklayan Pax + Giriş Yapacak Pax - Çıkış Yapacak Pax` formülünü çalıştırıyordu. Gelecek tarihli konaklayan listesinde o gün giriş yapacaklar zaten dahil edilmiş olduğu için formül bu kişileri 2 kez ekleyip çıkışları düşüyor (Örn: 23.08.2026 için `91 + 10 - 47 = 54 Pax`) ve yanlış rakam gösteriyordu.

#### 🛠️ Yapılan Düzeltmeler:
1. **`sedna_sync.py` Geceleme Mantığı Güncellendi:**
   Gelecek tarihlerdeki konaklama şartı `Status IN (1, 2) AND CheckinDate <= date_str AND CheckOutDate > date_str` olarak güncellendi. Giriş günü ile çıkış günü arasındaki tüm geçerli rezervasyonlar o gecenin doluluğuna dahil edildi.
2. **`index.html` EOD Pax Mantığı Güncellendi:**
   `selectedDate > report_date` (gelecek tarihler) durumunda Gün Sonu Pax değeri doğrudan Sedna SQL'deki net konaklama Pax sayısına (Örn: 23.08.2026 için **91 Pax**) sabitlendi.
3. **Sedna Desktop PDF Raporu Doğrulaması:**
   Yapılan düzeltmeler sonucu 21.08.2026 ile 28.08.2026 arasındaki tüm günlerin Dolu Oda (Sold), Giriş (Cin_Room), Çıkış (Cout_Room) ve Gün Sonu Kişi Sayıları (TotalPax) Sedna Desktop `0101001_General Forecast Analysis` PDF raporu ile %100 birebir eşitlendi.
4. **Dağıtım & Senkronizasyon:**
   Değişiklikler yerel sunucuda (`192.168.0.128`), `dashboard/index.html` alt klasöründe ve GitHub (`origin master` / Netlify) canlı ortamında güncellendi.
'''

if '21.08.2026' not in content:
    content += new_entry
    with open('cloud.md', 'w', encoding='utf-8') as f:
        f.write(content)
    print("Updated cloud.md successfully!")
else:
    print("cloud.md already contains 21.08.2026 entry!")
