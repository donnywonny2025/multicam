#!/usr/bin/env python3
"""
Emily v26 — 2-Minute Hook (breathing room + laugh beats)
Built on the Zamiyah Client Edit XML generator architecture.
Expanded: MEET → FUN + laugh → family bridge → heart → comedy → mission → TOOTIE.
"""
import json, os
from urllib.parse import quote

BASE = "/Volumes/WORK 2TB/WORK 2026/SANDBOX/Emily"
AUDIO_BASE = "/Volumes/WORK 2TB/WORK 2026/SANDBOX/Audio Organized/Nurse Interview Session (Feb 17)"
MIC1_PATH = f"{AUDIO_BASE}/MIC1.WAV"
MIC2_PATH = f"{AUDIO_BASE}/MIC2.WAV"
TRANSCRIPT_PATH = f"{BASE}/Master_MIC1_Transcript.json"

# Camera offsets (seconds from MIC1 timeline zero to source file start)
# These are the SAME offsets from v6 but expressed as camera offsets
# Positive = camera started AFTER mic, so src_in = transcript_time + offset
WIDE_OFFSET = 9.0102   # Cam 1 / C9124.MP4 started 9s before MIC timeline
HOST_CLIPS = [
    ("C0003.MP4", "Cam 2", 4.5544, 0, 1792.3358),     # offset, tl_start, tl_end
    ("C0004.MP4", "Cam 2", -1792.3358, 1792.3358, 99999),
]
GUEST_CLIPS = [
    ("C0001.MP4", "Cam 3", 2.2166, 0, 1800.4341),
    ("C0002.MP4", "Cam 3", -1800.4341, 1800.4341, 99999),
]

# ============================================================
# NARRATIVE ANCHORS — All timestamps are MIC1/transcript time
# format: (rough_in, first_word, rough_out, last_word, label, active_cam)
# active_cam: H=Host(V2), G=Guest(V3), W=Wide(V1)
# ============================================================
EDIT_ANCHORS = [
    # ── v26: 2-MINUTE HOOK — let them breathe, add laughs ──
    #
    # OPEN: The vibe
    # 1. W: Wide — the set, both of them, the energy
    (134.7, "We've", 138.6, "laughing", "Open Laughing", "W"),
    # 2. H: Lilliani introduces Emily by name
    (143.0, "Her", 148.5, "branded", "Meet Emily", "H"),
    #
    # FUN: She's creative
    # 3. G: "I have a really creative mind"
    (319.3, "have", 320.7, "mind", "Creative Mind", "G"),
    # 4. G: "We learn a lesson, we laugh, and have a blast" (NEW)
    (278.0, "learn", 282.8, "blast", "We Have A Blast", "G"),
    # 5. H: Lilliani wants to see it
    (338.6, "can", 341.2, "character", "Can I See", "H"),
    # 6. G: The punchline
    (394.6, "That", 396.5, "acid", "Sulfuric Acid", "G"),
    # 7. W: "That was fun" — LAUGH BEAT, shared joy (NEW)
    (424.0, "That", 425.5, "fun", "That Was Fun", "W"),
    # 8. W: Shared energy — "keep going!"
    (390.6, "Keep", 392.8, "going", "Keep Going", "W"),
    #
    # BRIDGE: Fun to real
    # 9. G: "I'm super social"
    (644.7, "I'm", 645.9, "social", "Super Social", "G"),
    # 10. G: Mom doubted her
    (664.0, "you're", 666.0, "minute", "Mom No Temper", "G"),
    # 11. G: "I carved my own path"
    (670.0, "definitely", 675.4, "else", "Carved Path", "G"),
    #
    # HEART: Real question → real answer
    # 12. H: "What gives you the good feelings?"
    (688.9, "what", 693.4, "moments", "Good Feelings", "H"),
    # 13. G: "Knowing that my touch, my care makes a difference"
    (693.7, "Knowing", 698.9, "difference", "Touch Care", "G"),
    #
    # FAMILY: She's real, relatable
    # 14. G: "Got on my nerves, what's for dinner"
    (857.0, "got", 860.1, "dinner", "Whats For Dinner", "G"),
    #
    # POSITIVE: Her mission
    # 15. G: "I want to bring that magic to 2026"
    (583.0, "we", 588.1, "2026", "Magic 2026", "G"),
    # 16. G: "You can't be moved when you know who you are"
    (2525.2, "You", 2529.9, "are", "Know Who You Are", "G"),
    #
    # TOOTIE PAYOFF
    # 17. H: "I want to hear this"
    (2420.5, "Okay", 2423.7, "this", "Wanna Hear", "H"),
    # 18. G: Tootie — "That hair, fabulous!"
    (2474.7, "That", 2477.2, "fabulous", "Fabulous", "G"),
    # 19. H: "Oh my gosh, I got her on my show!"
    (2468.0, "gosh", 2471.4, "show", "OMG React", "H"),
    #
    # CLOSE
    # 20. W: "She's great, I love her"
    (2531.0, "She's", 2534.2, "her", "Love Her", "W"),
    # 21. H: "Okay, we're doing it!"
    (2665.5, "Okay", 2668.3, "it", "Doing It", "H"),
]

# ============================================================
# Word-anchor resolver (EXACT Zamiyah v2 code)
# ============================================================
def _load_words():
    with open(TRANSCRIPT_PATH) as f:
        d = json.load(f)
    words = sorted([w for s in d.get("segments", []) for w in s.get("words", [])],
                   key=lambda w: w["start"])
    print(f"📝 Transcript loaded: {len(words)} words")
    return words

def resolve_anchors(anchors, words):
    resolved = []
    errors = []
    
    for first_t, first_w, last_t, last_w, label, cam in anchors:
        fw = None
        for w in words:
            if abs(w["start"] - first_t) < 4.0 and w["word"].lower().strip(".,!? ") == first_w.lower():
                fw = w; break
        if not fw:
            errors.append(f"❌ [{label}] First word '{first_w}' not found near {first_t}s")
            continue
        
        lw = None
        for w in words:
            if abs(w["start"] - last_t) < 4.0 and w["word"].lower().strip(".,!? ") == last_w.lower():
                lw = w; break
        if not lw:
            errors.append(f"❌ [{label}] Last word '{last_w}' not found near {last_t}s")
            continue
        
        # Breathing room — let them finish their thoughts
        # Start: 0.20s before first word
        # End: 0.35s after last word (room to land naturally)
        START_PAD = 0.20
        END_PAD = 0.35
        
        prev_w = None
        for w in words:
            if w["end"] <= fw["start"]:
                prev_w = w
        if prev_w and (fw["start"] - prev_w["end"]) < 2.0:
            gap = fw["start"] - prev_w["end"]
            in_pt = fw["start"] - min(gap * 0.5, START_PAD)
        else:
            in_pt = fw["start"] - START_PAD
        
        next_w = None
        for w in words:
            if w["start"] >= lw["end"] + 0.01:
                next_w = w; break
        if next_w and (next_w["start"] - lw["end"]) < 2.0:
            gap = next_w["start"] - lw["end"]
            out_pt = lw["end"] + min(gap * 0.4, END_PAD)  # 40% of gap, max 0.35s
        else:
            out_pt = lw["end"] + END_PAD
        
        resolved.append((in_pt, out_pt, label, cam))
        print(f"  ✅ [{label}] {in_pt:.2f} → {out_pt:.2f} ({out_pt-in_pt:.2f}s) [{cam}]")
    
    if errors:
        for e in errors: print(e)
        raise SystemExit(1)
    
    return resolved

# ============================================================
# Filler removal (EXACT Zamiyah v2 code)
# ============================================================
filler_set = {"um","uh","ums","uhs","hmm","mhm","mmm","ah","hm","mm"}

def intelligent_filler_removal(edit_list, words):
    new_edit = []
    splits = 0; trims = 0
    
    for start, end, label, cam in edit_list:
        seg_words = [w for w in words if w["start"] >= start and w["end"] <= end]
        real = [w for w in seg_words if w["word"].lower().strip(".,!? ") not in filler_set]
        fillers = [w for w in seg_words if w["word"].lower().strip(".,!? ") in filler_set]
        
        if not real:
            new_edit.append((start, end, label, cam)); continue
        
        for f_w in fillers:
            pre_gap = f_w["start"] - max((w["end"] for w in seg_words if w["end"] < f_w["start"]), default=start)
            post_gap = min((w["start"] for w in seg_words if w["start"] > f_w["end"]), default=end) - f_w["end"]
            if pre_gap > 0.3 and post_gap > 0.3:
                pre_real = [w for w in real if w["end"] <= f_w["start"]]
                post_real = [w for w in real if w["start"] >= f_w["end"]]
                if pre_real and post_real:
                    new_edit.append((start, (f_w["start"] + pre_real[-1]["end"])/2, label, cam))
                    new_edit.append(((f_w["end"] + post_real[0]["start"])/2, end, label, cam))
                    splits += 1; break
            elif f_w == seg_words[0] and post_gap > 0.1:
                start = (f_w["end"] + real[0]["start"]) / 2; trims += 1
            elif f_w == seg_words[-1] and pre_gap > 0.1:
                end = (real[-1]["end"] + f_w["start"]) / 2; trims += 1
        else:
            new_edit.append((start, end, label, cam))
    
    print(f"🧠 FILLER: {splits} splits, {trims} trims → {len(new_edit)} segments")
    return new_edit

# ============================================================
# Pipeline
# ============================================================
ALL_WORDS = _load_words()
print("\n1. Resolving Word Anchors...")
EDIT = resolve_anchors(EDIT_ANCHORS, ALL_WORDS)
print("\n2. Scrubbing Fillers...")
EDIT = intelligent_filler_removal(EDIT, ALL_WORDS)

# Read-through
print(f"\n{'='*60}")
print("  📖 SIZZLE HOOK READ-THROUGH")
print(f"{'='*60}\n")
total_dur = 0
for s, e, label, cam in EDIT:
    seg_w = [w for w in ALL_WORDS if w["start"] >= s - 0.1 and w["end"] <= e + 0.1]
    real = [w for w in seg_w if w["word"].lower().strip(".,!? ") not in filler_set]
    text = " ".join(w["word"] for w in real).strip()
    dur = e - s
    total_dur += dur
    print(f"  [{cam}] ({dur:.1f}s) {label}: {text}")
print(f"\n  ─── {total_dur:.1f}s total ───")

# ============================================================
# Build FCP7 XML — EXACT Zamiyah v2 generator pattern
# ============================================================
def s2f(seconds):
    """Drop-frame 29.97fps conversion — matches Zamiyah exactly."""
    return int(round(seconds * 30000 / 1001))

# Source file URLs
wide_url = f"file://localhost{quote(os.path.join(BASE, 'Cam 1/C9124.MP4'))}"
host_c3_url = f"file://localhost{quote(os.path.join(BASE, 'Cam 2/C0003.MP4'))}"
host_c4_url = f"file://localhost{quote(os.path.join(BASE, 'Cam 2/C0004.MP4'))}"
guest_c1_url = f"file://localhost{quote(os.path.join(BASE, 'Cam 3/C0001.MP4'))}"
guest_c2_url = f"file://localhost{quote(os.path.join(BASE, 'Cam 3/C0002.MP4'))}"
mic1_url = f"file://localhost{quote(MIC1_PATH)}"
mic2_url = f"file://localhost{quote(MIC2_PATH)}"

# Source durations (frames) — hardcoded from ffprobe
import subprocess
def get_dur_f(path):
    r = subprocess.run(['/opt/homebrew/bin/ffprobe', '-v', 'quiet', '-show_entries',
                        'format=duration', '-of', 'csv=p=0', path],
                       capture_output=True, text=True)
    return s2f(float(r.stdout.strip()))

WIDE_DUR_F = get_dur_f(os.path.join(BASE, "Cam 1/C9124.MP4"))
HOST_C3_DUR_F = get_dur_f(os.path.join(BASE, "Cam 2/C0003.MP4"))
HOST_C4_DUR_F = get_dur_f(os.path.join(BASE, "Cam 2/C0004.MP4"))
GUEST_C1_DUR_F = get_dur_f(os.path.join(BASE, "Cam 3/C0001.MP4"))
GUEST_C2_DUR_F = get_dur_f(os.path.join(BASE, "Cam 3/C0002.MP4"))
MIC1_DUR_F = get_dur_f(MIC1_PATH)
MIC2_DUR_F = get_dur_f(MIC2_PATH)

def get_host_src(t_sec):
    """Get correct host clip and source in-point for a given transcript time."""
    if t_sec < 1792.3358:
        return host_c3_url, "C0003.MP4", HOST_C3_DUR_F, s2f(t_sec + 4.5544)
    else:
        return host_c4_url, "C0004.MP4", HOST_C4_DUR_F, s2f(t_sec - 1792.3358)

def get_guest_src(t_sec):
    """Get correct guest clip and source in-point for a given transcript time."""
    if t_sec < 1800.4341:
        return guest_c1_url, "C0001.MP4", GUEST_C1_DUR_F, s2f(t_sec + 2.2166)
    else:
        return guest_c2_url, "C0002.MP4", GUEST_C2_DUR_F, s2f(t_sec - 1800.4341)

# Use independent frame anchoring: compute seq duration from s2f(e) - s2f(s)
# to avoid rounding drift from s2f(e-s)
total_f = sum(s2f(e) - s2f(s) for s, e, l, c in EDIT)

L = []
L.append('<?xml version="1.0" encoding="UTF-8"?>')
L.append('<!DOCTYPE xmeml>')
L.append('<xmeml version="4">')
L.append(' <sequence>')
L.append('  <name>Emily v26 Hook</name>')
L.append(f'  <duration>{total_f}</duration>')
L.append('  <rate><timebase>30</timebase><ntsc>TRUE</ntsc></rate>')
L.append('  <media>')
L.append('   <video>')
L.append('    <format><samplecharacteristics><width>3840</width><height>2160</height></samplecharacteristics></format>')

# V1 — Wide (Cam 1 / C9124)
L.append('    <track>')
seq_cursor = 0
for idx, (s, e, label, cam) in enumerate(EDIT):
    src_in_f = s2f(s + WIDE_OFFSET)
    src_out_f = s2f(e + WIDE_OFFSET)
    dur_f = src_out_f - src_in_f
    L.append(f'     <clipitem id="V1_clip_{idx}">')
    L.append(f'      <name>{label}</name>')
    L.append(f'      <enabled>{"TRUE" if cam == "W" else "FALSE"}</enabled>')
    L.append(f'      <duration>{WIDE_DUR_F}</duration>')
    L.append('      <rate><timebase>30</timebase><ntsc>TRUE</ntsc></rate>')
    L.append(f'      <start>{seq_cursor}</start><end>{seq_cursor + dur_f}</end>')
    L.append(f'      <in>{src_in_f}</in><out>{src_out_f}</out>')
    L.append('      <file id="Wide_file">')
    L.append('       <name>C9124.MP4</name>')
    L.append(f'       <pathurl>{wide_url}</pathurl>')
    L.append(f'       <duration>{WIDE_DUR_F}</duration>')
    L.append('       <rate><timebase>30</timebase><ntsc>TRUE</ntsc></rate>')
    L.append('       <media><video><samplecharacteristics><width>3840</width><height>2160</height></samplecharacteristics></video><audio><samplecharacteristics><depth>16</depth><samplerate>48000</samplerate></samplecharacteristics><channelcount>2</channelcount></audio></media>')
    L.append('      </file>')
    L.append('     </clipitem>')
    seq_cursor += dur_f
L.append('    </track>')

# V2 — Host (Cam 2 / C0003 + C0004)
L.append('    <track>')
seq_cursor = 0
for idx, (s, e, label, cam) in enumerate(EDIT):
    url, fname, file_dur_f, src_in_f = get_host_src(s)
    _, _, _, src_out_f = get_host_src(e)
    # If e crosses file boundary, recalc
    if s < 1792.3358 and e >= 1792.3358:
        src_out_f = s2f(e + HOST_CLIPS[1][2])  # use second clip offset
    dur_f = src_out_f - src_in_f
    fid = "Host_C3_file" if s < 1792.3358 else "Host_C4_file"
    L.append(f'     <clipitem id="V2_clip_{idx}">')
    L.append(f'      <name>{label}</name>')
    L.append(f'      <enabled>{"TRUE" if cam == "H" else "FALSE"}</enabled>')
    L.append(f'      <duration>{file_dur_f}</duration>')
    L.append('      <rate><timebase>30</timebase><ntsc>TRUE</ntsc></rate>')
    L.append(f'      <start>{seq_cursor}</start><end>{seq_cursor + dur_f}</end>')
    L.append(f'      <in>{src_in_f}</in><out>{src_out_f}</out>')
    L.append(f'      <file id="{fid}">')
    L.append(f'       <name>{fname}</name>')
    L.append(f'       <pathurl>{url}</pathurl>')
    L.append(f'       <duration>{file_dur_f}</duration>')
    L.append('       <rate><timebase>30</timebase><ntsc>TRUE</ntsc></rate>')
    L.append('       <media><video><samplecharacteristics><width>3840</width><height>2160</height></samplecharacteristics></video><audio><samplecharacteristics><depth>16</depth><samplerate>48000</samplerate></samplecharacteristics><channelcount>2</channelcount></audio></media>')
    L.append('      </file>')
    L.append('     </clipitem>')
    seq_cursor += dur_f
L.append('    </track>')

# V3 — Guest (Cam 3 / C0001 + C0002)
L.append('    <track>')
seq_cursor = 0
for idx, (s, e, label, cam) in enumerate(EDIT):
    url, fname, file_dur_f, src_in_f = get_guest_src(s)
    _, _, _, src_out_f = get_guest_src(e)
    if s < 1800.4341 and e >= 1800.4341:
        src_out_f = s2f(e + GUEST_CLIPS[1][2])
    dur_f = src_out_f - src_in_f
    fid = "Guest_C1_file" if s < 1800.4341 else "Guest_C2_file"
    L.append(f'     <clipitem id="V3_clip_{idx}">')
    L.append(f'      <name>{label}</name>')
    L.append(f'      <enabled>{"TRUE" if cam == "G" else "FALSE"}</enabled>')
    L.append(f'      <duration>{file_dur_f}</duration>')
    L.append('      <rate><timebase>30</timebase><ntsc>TRUE</ntsc></rate>')
    L.append(f'      <start>{seq_cursor}</start><end>{seq_cursor + dur_f}</end>')
    L.append(f'      <in>{src_in_f}</in><out>{src_out_f}</out>')
    L.append(f'      <file id="{fid}">')
    L.append(f'       <name>{fname}</name>')
    L.append(f'       <pathurl>{url}</pathurl>')
    L.append(f'       <duration>{file_dur_f}</duration>')
    L.append('       <rate><timebase>30</timebase><ntsc>TRUE</ntsc></rate>')
    L.append('       <media><video><samplecharacteristics><width>3840</width><height>2160</height></samplecharacteristics></video><audio><samplecharacteristics><depth>16</depth><samplerate>48000</samplerate></samplecharacteristics><channelcount>2</channelcount></audio></media>')
    L.append('      </file>')
    L.append('     </clipitem>')
    seq_cursor += dur_f
L.append('    </track>')
L.append('   </video>')

# A1 — MIC1 (Host audio — always enabled, fractured to match video)
L.append('   <audio>')
L.append('    <track>')
seq_cursor = 0
for idx, (s, e, label, cam) in enumerate(EDIT):
    src_in_f = s2f(s)
    src_out_f = s2f(e)
    dur_f = src_out_f - src_in_f
    L.append(f'     <clipitem id="A1_clip_{idx}">')
    L.append(f'      <name>{label}</name>')
    L.append('      <enabled>TRUE</enabled>')
    L.append(f'      <duration>{MIC1_DUR_F}</duration>')
    L.append('      <rate><timebase>30</timebase><ntsc>TRUE</ntsc></rate>')
    L.append(f'      <start>{seq_cursor}</start><end>{seq_cursor + dur_f}</end>')
    L.append(f'      <in>{src_in_f}</in><out>{src_out_f}</out>')
    L.append('      <file id="MIC1_file">')
    L.append('       <name>MIC1.WAV</name>')
    L.append(f'       <pathurl>{mic1_url}</pathurl>')
    L.append(f'       <duration>{MIC1_DUR_F}</duration>')
    L.append('       <rate><timebase>30</timebase><ntsc>TRUE</ntsc></rate>')
    L.append('       <media><audio><samplecharacteristics><depth>16</depth><samplerate>48000</samplerate></samplecharacteristics><channelcount>2</channelcount></audio></media>')
    L.append('      </file>')
    L.append('      <sourcetrack><mediatype>audio</mediatype><trackindex>1</trackindex></sourcetrack>')
    L.append('     </clipitem>')
    seq_cursor += dur_f
L.append('    </track>')

# A2 — MIC2 (Guest audio — always enabled, fractured to match video)
L.append('    <track>')
seq_cursor = 0
for idx, (s, e, label, cam) in enumerate(EDIT):
    src_in_f = s2f(s)
    src_out_f = s2f(e)
    dur_f = src_out_f - src_in_f
    L.append(f'     <clipitem id="A2_clip_{idx}">')
    L.append(f'      <name>{label}</name>')
    L.append('      <enabled>TRUE</enabled>')
    L.append(f'      <duration>{MIC2_DUR_F}</duration>')
    L.append('      <rate><timebase>30</timebase><ntsc>TRUE</ntsc></rate>')
    L.append(f'      <start>{seq_cursor}</start><end>{seq_cursor + dur_f}</end>')
    L.append(f'      <in>{src_in_f}</in><out>{src_out_f}</out>')
    L.append('      <file id="MIC2_file">')
    L.append('       <name>MIC2.WAV</name>')
    L.append(f'       <pathurl>{mic2_url}</pathurl>')
    L.append(f'       <duration>{MIC2_DUR_F}</duration>')
    L.append('       <rate><timebase>30</timebase><ntsc>TRUE</ntsc></rate>')
    L.append('       <media><audio><samplecharacteristics><depth>16</depth><samplerate>48000</samplerate></samplecharacteristics><channelcount>2</channelcount></audio></media>')
    L.append('      </file>')
    L.append('      <sourcetrack><mediatype>audio</mediatype><trackindex>1</trackindex></sourcetrack>')
    L.append('     </clipitem>')
    seq_cursor += dur_f
L.append('    </track>')

L.append('   </audio>')
L.append('  </media>')
L.append(' </sequence>')
L.append('</xmeml>')

out_comp = f"{BASE}/Emily_v26_Hook.xml"
with open(out_comp, "w") as f: f.write("\n".join(L))
print(f"\n✅ Generated: {out_comp}")
print(f"   {total_dur:.1f}s | {len(EDIT)} segments | {total_f} frames")
