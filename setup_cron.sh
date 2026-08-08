#!/bin/bash
DIR="/home/society/Masaüstü/sedna_cloud_backup"
CRON_CMD="*/15 * * * * cd \"$DIR\" && /usr/bin/python3 sedna_sync.py >> sync.log 2>&1"

# Check if it already exists
if crontab -l 2>/dev/null | grep -q "sedna_sync.py"; then
    echo "Cron job already exists!"
else
    (crontab -l 2>/dev/null; echo "$CRON_CMD") | crontab -
    echo "Cron job added successfully!"
fi
