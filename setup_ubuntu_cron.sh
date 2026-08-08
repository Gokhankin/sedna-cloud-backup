#!/bin/bash

echo "🚀 Ubuntu için Sedna -> Firebase Senkronizasyon Kurulumu"

# 1. Gerekli Python kütüphanelerini kur
echo "📦 Python kütüphaneleri kuruluyor..."
sudo apt-get update
sudo apt-get install -y python3-pip unixodbc-dev
pip3 install pyodbc requests

# Not: Eğer Ubuntu'da Microsoft ODBC Sürücüsü yoksa, aşağıdaki komutlarla kurulmalıdır:
# curl https://packages.microsoft.com/keys/microsoft.asc | sudo tee /etc/apt/trusted.gpg.d/microsoft.asc
# curl https://packages.microsoft.com/config/ubuntu/$(lsb_release -rs)/prod.list | sudo tee /etc/apt/sources.list.d/mssql-release.list
# sudo apt-get update
# sudo ACCEPT_EULA=Y apt-get install -y msodbcsql18

# 2. Çalışma dizinini ayarla
WORK_DIR="/home/$USER/sedna_cloud_backup"
mkdir -p $WORK_DIR
cp sedna_sync.py $WORK_DIR/

# 3. Cron Job (Zamanlanmış Görev) Ekle
echo "⏱️ Cron job (Zamanlanmış görev) ayarlanıyor..."
CRON_CMD="*/15 * * * * /usr/bin/python3 $WORK_DIR/sedna_sync.py >> $WORK_DIR/sync.log 2>&1"

# Mevcut crontab'ı kontrol et, eğer ekli değilse ekle
(crontab -l 2>/dev/null | grep -Fv "sedna_sync.py"; echo "$CRON_CMD") | crontab -

echo "✅ Kurulum tamamlandı! Script her 15 dakikada bir otomatik çalışacak."
echo "📜 Logları izlemek için: tail -f $WORK_DIR/sync.log"
