import os, shutil, subprocess

# 1. Git commit and tag if git repo
subprocess.run("cd '/home/society/Masaüstü/sedna_cloud_backup' && git add . && git commit -m 'YEDEK: 21.08.2026 Sedna Cloud Backup Before Forecast Fix' && git tag -f '21.08.2026_sedna_cloud_yedek'", shell=True)

# 2. Copy folder backup
if os.path.exists('/home/society/Masaüstü/sedna_cloud_backup_21.08.2026_yedek'):
    shutil.rmtree('/home/society/Masaüstü/sedna_cloud_backup_21.08.2026_yedek')

shutil.copytree('/home/society/Masaüstü/sedna_cloud_backup', '/home/society/Masaüstü/sedna_cloud_backup_21.08.2026_yedek', ignore=shutil.ignore_patterns('venv', '__pycache__', '.git', '*.pyc', '*.log'))

# 3. Create zip file backup
if os.path.exists('/home/society/Masaüstü/sedna_cloud_backup_21.08.2026_yedek.zip'):
    os.remove('/home/society/Masaüstü/sedna_cloud_backup_21.08.2026_yedek.zip')

shutil.make_archive('/home/society/Masaüstü/sedna_cloud_backup_21.08.2026_yedek', 'zip', '/home/society/Masaüstü/sedna_cloud_backup')

print(f"Backup folder created at: /home/society/Masaüstü/sedna_cloud_backup_21.08.2026_yedek")
print(f"Backup zip created at: /home/society/Masaüstü/sedna_cloud_backup_21.08.2026_yedek.zip")
