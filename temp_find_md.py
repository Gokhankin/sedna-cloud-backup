import os

files = os.listdir('.')
md_files = [f for f in files if f.endswith('.md')]
print("Markdown files in directory:", md_files)
