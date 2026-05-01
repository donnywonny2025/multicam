with open('/Volumes/WORK 2TB/WORK 2026/SANDBOX/Emily/sync_scripts/autocut_v31_hook.py', 'r') as f:
    text = f.read()

# Make sure we only insert it if it doesn't already exist
if "L.append('   </video>')" not in text:
    text = text.replace("    L.append('   <audio>')", "    L.append('   </video>')\n    L.append('   <audio>')", 1)
    text = text.replace("L.append('   <audio>')", "L.append('   </video>')\nL.append('   <audio>')", 1)

with open('/Volumes/WORK 2TB/WORK 2026/SANDBOX/Emily/sync_scripts/autocut_v31_hook.py', 'w') as f:
    f.write(text)

