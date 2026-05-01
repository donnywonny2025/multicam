import re

with open('/Volumes/WORK 2TB/WORK 2026/SANDBOX/Emily/sync_scripts/autocut_v29_hook.py', 'r') as f:
    code = f.read()

new_anchors = """EDIT_ANCHORS = [
    # [0:00] The Window (Lilliani Cam/Wide)
    (142.5, "Her", 149.7, "furniture", "The Window", "W"),

    # [0:08] The Persona (Emily Cam)
    (174.1, "Nurse", 181.8, "health", "The Persona", "G"),

    # [0:15] The Pivot (Wide)
    (1299.5, "when", 1305.6, "corrections", "The Pivot", "W"),

    # [0:22] The Reality (Emily Cam)
    (1647.5, "And", 1654.7, "detention", "The Reality", "G"),

    # [0:28] The Contrast (Emily speaking, Host Reaction) -> L-cut on Lilliani
    (1871.8, "seeing", 1873.7, "adults", "The Contrast 1", "H"),
    (1901.3, "A", 1909.7, "okay", "The Contrast 2", "H"),

    # [0:34] The Trauma (Lilliani Tight)
    (1735.4, "I", 1742.0, "illegally", "Trauma 1", "H"),
    (1792.5, "they", 1793.8, "ankles", "Trauma 2", "H"),
    (1827.3, "it", 1829.2, "traumatizing", "Trauma 3", "H"),

    # [0:41] The Empathy (Emily Reaction) -> Emily nodding
    (1332.1, "I", 1333.7, "underdog", "The Empathy", "G"),

    # [0:48] The Resolve (Wide Shot)
    (469.9, "people", 471.1, "humble", "The Resolve 1", "W"),
    (478.5, "I", 479.9, "am", "The Resolve 2", "W"),

    # [0:52] The Stinger (Emily Tight) -> "The more you affirm yourself..."
    (2506.6, "more", 2508.6, "yourself", "The Stinger 1", "G"),
    (2513.2, "I'm", 2517.8, "girl", "The Stinger 2", "G"),

    # [0:58] The Snap (Wide) -> "Emily Ellis is in the building. Let's dive in" -> mapped to:
    (141.0, "We", 142.0, "today", "The Snap", "W"),
]"""

# Replace the EDIT_ANCHORS block safely
code = re.sub(r'EDIT_ANCHORS = \[\n.*?\]', new_anchors, code, flags=re.DOTALL)

# Update the output file name
code = code.replace('Emily_v29_Hook.xml', 'Emily_v30_Hook.xml')
code = code.replace('Emily v29', 'Emily v30')

with open('/Volumes/WORK 2TB/WORK 2026/SANDBOX/Emily/sync_scripts/autocut_v30_hook.py', 'w') as f:
    f.write(code)
