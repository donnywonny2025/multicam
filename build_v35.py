import sys

with open('/Volumes/WORK 2TB/WORK 2026/SANDBOX/Emily/sync_scripts/autocut_v16_selects.py', 'r') as f:
    text = f.read()

with open('/Volumes/WORK 2TB/WORK 2026/SANDBOX/Emily/sync_scripts/anchor_out.txt', 'r') as f:
    anchors_text = f.read()

# Find exactly where the EDIT_ANCHORS block begins and ends
start_idx = text.find('EDIT_ANCHORS = [')
end_idx = text.find(']', start_idx) + 1

# Replace the block
new_text = text[:start_idx] + anchors_text + text[end_idx:]

new_text = new_text.replace('Emily v16', 'Emily v35')
new_text = new_text.replace('Emily_v16_Selects.xml', 'Emily_v35_Selects.xml')

with open('/Volumes/WORK 2TB/WORK 2026/SANDBOX/Emily/sync_scripts/autocut_v35_selects.py', 'w') as f:
    f.write(new_text)

print('Generated autocut_v35_selects.py successfully.')
