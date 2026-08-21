import subprocess

cmd = "git add cloud.md && git commit -m 'docs: update cloud.md with 21.08.2026 forecast and pax fix notes' && git push origin master"
res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
print('GIT PUSH STDOUT:', res.stdout)
print('GIT PUSH STDERR:', res.stderr)
