#!/usr/bin/env python3
"""
Emily v35 — Soundbox Hook (Draft 1)
Built on the Zamiyah Client Edit XML generator architecture.
Implements specific emotional trajectory requested via Gemini prompt + Text Slugs.
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
    # --- EMILY (GUEST) BEST CLIPS ---
    (305.0, "I'm", 309.2, 'level', 'Best Heart', 'G'),
    (393.0, 'Oh', 396.5, 'acid', 'Sulfuric Acid', 'G'),
    (535.9, 'I', 538.7, 'than', 'Never Less Than', 'G'),
    (584.4, 'I', 588.1, '2026', 'Magic 2026', 'G'),
    (644.0, "I'm", 645.9, 'social', 'Super Social', 'G'),
    (663.0, 'my', 666.0, 'minute', 'Mom Doubted', 'G'),
    (670.0, 'I', 675.3, 'else', 'Unique Pathway', 'G'),
    (694.3, 'Knowing', 698.4, 'difference', 'Touch Care', 'G'),
    (703.7, 'she', 710.5, 'father', 'Moms Advice', 'G'),
    (727.9, 'Their', 735.8, 'lotioned', 'Patient Care', 'G'),
    (833.8, 'We', 837.9, 'lost', 'No Love Lost', 'G'),
    (856.6, 'you', 860.1, 'dinner', 'Whats For Dinner', 'G'),
    (862.9, 'I', 870.9, 'to', 'Family Anchor', 'G'),
    (942.0, 'life', 948.3, 'impact', 'Leave Impact', 'G'),
    (958.0, "that's", 963.1, 'passion', 'Created Nursilly', 'G'),
    (1638.0, 'So', 1646.2, 'patients', 'Corrections Reveal', 'G'),
    (1670.0, 'She', 1671.2, 'underdog', 'Root Underdog', 'G'),
    (2195.0, 'What', 2204.0, 'them', 'Best Compliment', 'G'),
    (2204.6, 'I', 2208.4, 'world', 'I Was Loved', 'G'),
    (2400.0, 'One', 2407.0, 'me', 'Escape For Me', 'G'),
    (2454.0, 'All', 2461.2, 'yourself', 'Tootie Drop', 'G'),
    (2474.7, 'That', 2485.5, 'answer', 'Fabulous', 'G'),
    (2502.0, 'Who', 2508.0, 'yourself', 'Affirm Yourself', 'G'),
    (2525.0, 'You', 2528.0, 'are', 'Know Who You Are', 'G'),
    (2653.0, 'Oh', 2656.0, 'too', 'News Lady', 'G'),

    # --- LILLANI (HOST) BEST CLIPS ---
    (134.7, "We've", 138.6, 'laughing', 'Opening Laugh', 'H'),
    (143.0, 'Her', 150.5, 'furniture', 'Lillani Intro', 'H'),
    (157.0, "We're", 162.0, 'life', 'Her Mission', 'H'),
    (604.0, 'So', 607.4, 'nurse', 'Actual Nurse', 'H'),
    (609.5, 'And', 615.5, 'story', 'How Become Nurse', 'H'),
    (676.7, 'Wow', 678.5, 'beautiful', 'Wow Beautiful', 'H'),
    (679.5, 'What', 693.4, 'moments', 'Good Feelings', 'H'),
    (751.0, 'Nurses', 754.5, 'important', 'So Important', 'H'),
    (754.6, 'I', 763.7, 'go', 'Dont Realize', 'H'),
    (783.1, 'I', 791.1, 'mean', 'World Of You', 'H'),
    (860.5, 'Yeah', 861.9, 'it', 'Not Leaving', 'H'),
    (984.0, 'This', 988.6, 'it', 'Not Tomorrow', 'H'),
    (1010.0, 'So', 1012.5, 'much', 'Incredible Auntie', 'H'),
    (1627.0, 'But', 1632.2, 'new', 'Curious Day Job', 'H'),
    (1682.0, "That's", 1689.1, 'well', 'Thats Huge', 'H'),
    (1729.0, 'I', 1732.4, 'that', 'Love That Do', 'H'),
    (2364.6, "I'm", 2369.7, 'that', 'Sorry Sharing', 'H'),
    (2394.0, "You're", 2395.0, 'creative', 'Youre Creative', 'H'),
    (2422.0, 'Okay', 2426.0, 'now', 'Wanna Hear', 'H'),
    (2468.0, 'Oh', 2471.4, 'show', 'OMG React', 'H'),
    (2532.0, "She's", 2533.8, 'her', 'Love Her', 'H'),
    (2626.0, 'You', 2632.0, 'once', 'I Have Character', 'H'),
    (2640.0, 'We', 2644.0, 'fun', 'Collab', 'H'),
    (2666.0, 'Okay', 2668.3, 'it', 'Doing It', 'H'),
    (2670.4, "I'm", 2671.5, 'came', 'Happy You Came', 'H'),
]


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
# Add duration of two 10s text slugs
total_f = sum(s2f(e) - s2f(s) for s, e, l, c in EDIT) + 600

L = []
L.append('<?xml version="1.0" encoding="UTF-8"?>')
L.append('<!DOCTYPE xmeml>')
L.append('<xmeml version="4">')
L.append(' <sequence>')
L.append('  <name>Emily v35 Hook</name>')
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
    L.append('      <name>C9124.MP4</name>')
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
    L.append(f'      <name>{fname}</name>')
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
    L.append(f'      <name>{fname}</name>')
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

# A1 — MIC1 (Host audio — always enabled, fractured to match video)
L.append('   </video>')
L.append('   <audio>')
L.append('    <track>')
seq_cursor = 0
for idx, (s, e, label, cam) in enumerate(EDIT):
    src_in_f = s2f(s)
    src_out_f = s2f(e)
    dur_f = src_out_f - src_in_f
    L.append(f'     <clipitem id="A1_clip_{idx}">')
    L.append('      <name>MIC1.WAV</name>')
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
    L.append('      <name>MIC2.WAV</name>')
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

out_comp = f"{BASE}/Emily_v35_Selects.xml"
with open(out_comp, "w") as f: f.write("\n".join(L))
print(f"\n✅ Generated: {out_comp}")
print(f"   {total_dur:.1f}s | {len(EDIT)} segments | {total_f} frames")
