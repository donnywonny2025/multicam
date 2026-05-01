with open('/Volumes/WORK 2TB/WORK 2026/SANDBOX/Emily/sync_scripts/autocut_v30_hook.py', 'r') as f:
    text = f.read()

text = text.replace('v30', 'v31')
text = text.replace('v30:', 'v31:')

with open('/Volumes/WORK 2TB/WORK 2026/SANDBOX/Emily/sync_scripts/autocut_v31_hook.py', 'w') as f:
    f.write(text)

