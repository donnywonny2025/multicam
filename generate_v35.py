import re

# Read V16 to get ALL 48 ANCHORS
with open('/Volumes/WORK 2TB/WORK 2026/SANDBOX/Emily/sync_scripts/autocut_v16_selects.py', 'r') as f:
    v16 = f.read()

# Read V29 to get the safe XML generator logic
with open('/Volumes/WORK 2TB/WORK 2026/SANDBOX/Emily/sync_scripts/autocut_v31_hook.py', 'r') as f:
    v31 = f.read()

# Extract the anchors block from v16
match = re.search(r'EDIT_ANCHORS = \[(.*?)\]\n\ndef _load_words', v16, re.DOTALL)
anchors_text = match.group(1)

# Parse out the tuples
import ast
lines = anchors_text.split('\n')
guest_clips = []
host_clips = []

# Using a quick regex to pull the tuples AND their comments
chunks = []
current_comment = ""
for line in lines:
    line = line.strip()
    if line.startswith("#"):
        current_comment += "\n    " + line
    elif line.startswith("("):
        if line.endswith(","): line = line[:-1]
        try:
            tup = ast.literal_eval(line)
            cam = tup[5]
            if cam == "G":
                guest_clips.append(current_comment + "\n    " + line + ",")
            elif cam == "H":
                host_clips.append(current_comment + "\n    " + line + ",")
            current_comment = ""
        except:
            pass

new_anchors = "EDIT_ANCHORS = [" + "\n    # --- EMILY (GUEST) BEST CLIPS ---"
for c in guest_clips: new_anchors += c
new_anchors += "\n\n    # --- LILLANI (HOST) BEST CLIPS ---"
for c in host_clips: new_anchors += c
new_anchors += "\n]"

# Inject this back into V31 structure
v35 = re.sub(r'EDIT_ANCHORS = \[(.*?)\]', new_anchors, v31, flags=re.DOTALL)
v35 = v35.replace('v31', 'v35')
v35 = v35.replace('v30', 'v35')

# Make sure the OLD padding is used (it is already in V31! start-0.03, end+0.05. Wait...
# I should revert to V29 padding: 0.20 and 0.35.)
v35 = v35.replace('in_pt = fw["start"] - 0.03', 'in_pt = fw["start"] - 0.20')
v35 = v35.replace('out_pt = lw["end"] + 0.05', 'out_pt = lw["end"] + 0.35')

with open('/Volumes/WORK 2TB/WORK 2026/SANDBOX/Emily/sync_scripts/autocut_v35_selects.py', 'w') as f:
    f.write(v35)

