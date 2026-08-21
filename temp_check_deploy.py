import os, subprocess

with open('DEPLOYMENT_GUIDE.md', 'r', encoding='utf-8') as f:
    print("DEPLOYMENT GUIDE:
", f.read())

print("\nGIT REMOTES:")
subprocess.run("cd '{remote_dir}' && git remote -v", shell=True)
