with open('/Volumes/WORK 2TB/WORK 2026/SANDBOX/Emily/sync_scripts/autocut_v35_selects.py', 'r') as f:
    text = f.read()

# Separate the script at L = []
parts = text.split("L = []\nL.append('<?xml")
head = parts[0]
xml_logic = "L.append('<?xml" + parts[1]

# We need to turn xml_logic into:
# def build_sequence_xml(EDIT_LIST, sequence_name):
#     L = []
#     ... and replace EDIT with EDIT_LIST...
#     return L

xml_logic = xml_logic.replace("total_f = sum(s2f(e) - s2f(s) for s, e, l, c in EDIT) + 600", "total_f = sum(s2f(e) - s2f(s) for s, e, l, c in EDIT_LIST) + 600")
xml_logic = xml_logic.replace("<name>Emily v35 Selects</name>", "<name>{sequence_name}</name>")
# The loop references `EDIT` directly! We need to replace `in EDIT):` with `in EDIT_LIST):`
xml_logic = xml_logic.replace("in EDIT):", "in EDIT_LIST):")

# Remove the headers and footers of xmeml
xml_logic = xml_logic.replace("L.append('<?xml version=\"1.0\" encoding=\"UTF-8\"?>')", "")
xml_logic = xml_logic.replace("L.append('<!DOCTYPE xmeml>')", "")
xml_logic = xml_logic.replace("L.append('<xmeml version=\"4\">')", "")
xml_logic = xml_logic.replace("L.append('</xmeml>')", "")

# Remove the file write out at the bottom
xml_logic = xml_logic.split("out_comp =")[0]

func_def = "def build_sequence_xml(EDIT_LIST, sequence_name):\n    L = []\n"
for line in xml_logic.split('\n'):
    func_def += "    " + line + "\n"
func_def += "    return L\n"

# Define the new anchors
new_anchors = """
HOOK_ANCHORS = [
    (134.7, "We've", 138.6, 'laughing', 'Opening Laugh', 'H'),
    (143.0, 'Her', 150.5, 'furniture', 'Lillani Intro', 'H'),
    (2454.0, 'All', 2461.2, 'yourself', 'Tootie Drop', 'G'),
    (2474.7, 'That', 2485.5, 'answer', 'Fabulous', 'G'),
    (393.0, 'Oh', 396.5, 'acid', 'Sulfuric Acid', 'G'),
    (2502.0, 'Who', 2508.0, 'yourself', 'Affirm Yourself', 'G'),
    (2525.0, 'You', 2528.0, 'are', 'Know Who You Are', 'G'),
    (584.4, 'I', 588.1, '2026', 'Magic 2026', 'G')
]
HOOK_EDIT = resolve_anchors(HOOK_ANCHORS, ALL_WORDS)
HOOK_EDIT = intelligent_filler_removal(HOOK_EDIT, ALL_WORDS)
"""

footers = """
L_main = []
L_main.append('<?xml version="1.0" encoding="UTF-8"?>')
L_main.append('<!DOCTYPE xmeml>')
L_main.append('<xmeml version="4">')

L_main.extend(build_sequence_xml(EDIT, "Sequence A: Emily Selects Roll"))
L_main.extend(build_sequence_xml(HOOK_EDIT, "Sequence B: The Positive Hook"))

L_main.append('</xmeml>')

out_comp = f"{BASE}/Emily_v36_FunHook.xml"
with open(out_comp, "w") as f: f.write("\\n".join(L_main))
print(f"\\n✅ Generated: {out_comp} with TWO Sequences!")
"""

# Modify the head so it doesn't do `out_comp = ...`
new_text = head + func_def + new_anchors + footers

with open('/Volumes/WORK 2TB/WORK 2026/SANDBOX/Emily/sync_scripts/autocut_v36_opening.py', 'w') as f:
    f.write(new_text)

print("Generated V36 python script.")
