with open('/Volumes/WORK 2TB/WORK 2026/SANDBOX/Emily/sync_scripts/autocut_v29_hook.py', 'r') as f:
    v29 = f.read()

with open('/Volumes/WORK 2TB/WORK 2026/SANDBOX/Emily/sync_scripts/anchor_out.txt', 'r') as f:
    anchors = f.read()

# in v29, find EDIT_ANCHORS = [
start_idx = v29.find('EDIT_ANCHORS = [')
# find def _load_words
end_idx = v29.find('def _load_words')

new_text = v29[:start_idx] + anchors + '\n\n' + v29[end_idx:]

new_text = new_text.replace('Emily v29', 'Emily v35')
new_text = new_text.replace('Emily_v29_Hook.xml', 'Emily_v35_Selects.xml')

with open('/Volumes/WORK 2TB/WORK 2026/SANDBOX/Emily/sync_scripts/autocut_v35_selects.py', 'w') as f:
    f.write(new_text)

