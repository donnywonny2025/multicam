with open('/Volumes/WORK 2TB/WORK 2026/SANDBOX/Emily/sync_scripts/autocut_v29_hook.py', 'r') as f:
    text = f.read()

# Split the file exactly by "EDIT_ANCHORS = ["
parts = text.split("EDIT_ANCHORS = [", 1)
pre_anchors = parts[0]
post_chunk = parts[1]

# Split the second half by the closing bracket of EDIT_ANCHORS
# Look for the first "\n]"
sub_parts = post_chunk.split("\n]", 1)
post_anchors = sub_parts[1]

new_anchors = """
    # ── v30: SHACKLES TO TRIUMPH HOOK ──
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
    (141.0, "We", 142.0, "today", "The Snap", "W"),"""

final_text = pre_anchors + "EDIT_ANCHORS = [" + new_anchors + "\n]" + post_anchors

final_text = final_text.replace("v29", "v30")

with open('/Volumes/WORK 2TB/WORK 2026/SANDBOX/Emily/sync_scripts/autocut_v30_hook.py', 'w') as f:
    f.write(final_text)

