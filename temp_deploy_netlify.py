import shutil, subprocess

# 1. Copy index.html to dashboard/index.html
shutil.copy('index.html', 'dashboard/index.html')
print('Copied index.html to dashboard/index.html')

# 2. Git commit and push to GitHub (which triggers Netlify deploy)
cmd = "git add index.html dashboard/index.html sedna_sync.py && git commit -m 'Deploy: Fix eodPax future dates for Netlify and dashboard' && git push origin master"
res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
print('GIT PUSH STDOUT:', res.stdout)
print('GIT PUSH STDERR:', res.stderr)
