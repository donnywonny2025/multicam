with open('/Volumes/WORK 2TB/WORK 2026/SANDBOX/Emily/sync_scripts/autocut_v30_hook.py', 'r') as f:
    text = f.read()

# I will replace:
#     L.append('    </track>')
#     L.append('   <audio>')
# with:
#     L.append('    </track>')
#     L.append('   </video>')
#     L.append('   <audio>')

text = text.replace("    L.append('   <audio>')", "    L.append('   </video>')\n    L.append('   <audio>')")

with open('/Volumes/WORK 2TB/WORK 2026/SANDBOX/Emily/sync_scripts/autocut_v30_hook.py', 'w') as f:
    f.write(text)
