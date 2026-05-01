#!/usr/bin/env python3
"""
Emily v13 — Best Moments Selects Reel
Built on the EXACT Zamiyah Client Edit v10 XML generator architecture.
12-clip montage showing the full range of the conversation.
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
    # ── ALL BEST MOMENTS — laid out for review in Premiere ──
    # Each is a short, punchy clip. Review them all, pick your favorites.

    # 1. [02:15] Opening vibe — both laughing
    (134.7, "We've", 138.6, "laughing", "Opening Laugh", "H"),

    # 2. [05:06] Nurse Silly has the best heart
    (305.0, "I'm", 309.2, "level", "Best Heart", "G"),

    # 3. [06:31] Nurse Silly live bit — sulfuric acid
    (393.0, "Oh", 396.5, "acid", "Sulfuric Acid", "G"),

    # 4. [08:55] Tootie Mill — "never let anyone tell me I'm less than"
    (535.9, "I", 538.7, "than", "Never Less Than", "G"),

    # 5. [09:42] Bring the magic to 2026
    (584.4, "I", 588.1, "2026", "Magic 2026", "G"),

    # 6. [10:04] So you are an actual nurse
    (604.0, "So", 607.4, "nurse", "Actual Nurse", "H"),

    # 7. [10:44] I'm super social
    (644.0, "I'm", 645.9, "social", "Super Social", "G"),

    # 8. [10:55] Mom: You're not gonna be a nurse
    (663.0, "my", 666.0, "minute", "Mom Doubted", "G"),

    # 9. [11:09] Carved a unique pathway
    (670.0, "I", 675.3, "else", "Unique Pathway", "G"),

    # 10. [11:17] Wow. That's beautiful.
    (676.7, "Wow", 678.5, "beautiful", "Wow Beautiful", "H"),

    # 11. [11:34] My touch, my care makes a difference
    (694.3, "Knowing", 698.4, "difference", "Touch Care", "G"),

    # 12. [11:43] Mom's advice: treat everyone like family
    (703.7, "she", 710.5, "father", "Moms Advice", "G"),

    # 13. [12:07] Silly's patients — hair, lips, skin
    (727.9, "Their", 735.8, "lotioned", "Patient Care", "G"),

    # 14. [12:31] Nurses are so important
    (751.0, "Nurses", 754.5, "important", "So Important", "H"),

    # 15. [13:54] We say what needs to be said, no love lost
    (833.8, "We", 837.9, "lost", "No Love Lost", "G"),

    # 16. [14:16] Got on my nerves, what's for dinner
    (856.6, "you", 860.1, "dinner", "Whats For Dinner", "G"),

    # 17. [14:21] Yeah I'm not going to leave you
    (860.5, "Yeah", 861.9, "it", "Not Leaving", "H"),

    # 18. [14:22] I had my family to go back to
    (862.9, "I", 870.9, "to", "Family Anchor", "G"),

    # 19. [15:31] Life can be over, I want to leave an impact
    (942.0, "life", 948.3, "impact", "Leave Impact", "G"),

    # 20. [15:58] That's what led me to create Nurse Silly
    (958.0, "that's", 963.1, "passion", "Created Nursilly", "G"),

    # 21. [16:50] You're an incredible auntie
    (1010.0, "So", 1012.5, "much", "Incredible Auntie", "H"),

    # 22. [27:07] I'm so curious what you do day to day
    (1627.0, "But", 1632.2, "new", "Curious Day Job", "H"),

    # 23. [27:18] Department of Corrections + incarcerated patients
    (1638.0, "So", 1646.2, "patients", "Corrections Reveal", "G"),

    # 24. [27:50] Grandma taught me to root for the underdog
    (1670.0, "She", 1671.2, "underdog", "Root Underdog", "G"),

    # 25. [28:02] That's huge — juvenile detention
    (1682.0, "That's", 1689.1, "well", "Thats Huge", "H"),

    # 26. [36:35] Best compliment a child can give
    (2195.0, "What", 2204.0, "them", "Best Compliment", "G"),

    # 27. [36:45] I know I was loved — sane in this world
    (2204.6, "I", 2208.4, "world", "I Was Loved", "G"),

    # 28. [38:13] Nurse Silly born from grieving my brother
    (2294.0, "it", 2304.2, "on", "Origin Grief", "G"),

    # 29. [38:34] Brother's story got cut short
    (2315.0, "knowing", 2325.2, "holds", "Story Cut Short", "G"),

    # 30. [39:53] You are a creative
    (2394.0, "You're", 2395.0, "creative", "Youre Creative", "H"),

    # 31. [40:00] Nurse Silly is an escape for me
    (2400.0, "One", 2407.0, "me", "Escape For Me", "G"),

    # 32. [40:21] I want to hear this — next character?
    (2422.0, "Okay", 2426.0, "now", "Wanna Hear", "H"),

    # 33. [40:53] Tootie: five seconds of my time
    (2454.0, "All", 2461.2, "yourself", "Tootie Drop", "G"),

    # 34. [41:07] Oh my gosh! I got her on my show
    (2468.0, "Oh", 2471.4, "show", "OMG React", "H"),

    # 35. [41:14] That hair — fabulous!
    (2474.7, "That", 2485.5, "answer", "Fabulous", "G"),

    # 36. [41:41] Loving yourself / affirm yourself
    (2502.0, "Who", 2508.0, "yourself", "Affirm Yourself", "G"),

    # 37. [42:05] Can't be moved when you know who you are
    (2525.0, "You", 2528.0, "are", "Know Who You Are", "G"),

    # 38. [42:12] She's great. I love her.
    (2532.0, "She's", 2533.8, "her", "Love Her", "H"),

    # 39. [43:59] Character development together
    (2640.0, "We", 2644.0, "fun", "Collab", "H"),

    # 40. [44:12] She's a news lady too
    (2653.0, "Oh", 2656.0, "too", "News Lady", "G"),

    # 41. [44:26] Okay, we're doing it!
    (2666.0, "Okay", 2668.3, "it", "Doing It", "H"),
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
        
        # Smart padding — weighted to give MORE room to target words
        # 0.35s hard pad, 70/30 weighted midpoint (favor our word)
        PAD = 0.35
        prev_w = None
        for w in words:
            if w["end"] <= fw["start"]:
                prev_w = w
        if prev_w and (fw["start"] - prev_w["end"]) < 2.0:
            gap = fw["start"] - prev_w["end"]
            in_pt = fw["start"] - (gap * 0.7)  # give 70% of gap to our word
        else:
            in_pt = fw["start"] - PAD
        
        next_w = None
        for w in words:
            if w["start"] >= lw["end"] + 0.01:
                next_w = w; break
        if next_w and (next_w["start"] - lw["end"]) < 2.0:
            gap = next_w["start"] - lw["end"]
            out_pt = lw["end"] + (gap * 0.7)  # give 70% of gap to our word
        else:
            out_pt = lw["end"] + PAD
        
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

total_f = sum(s2f(e - s) for s, e, l, c in EDIT)

L = []
L.append('<?xml version="1.0" encoding="UTF-8"?>')
L.append('<!DOCTYPE xmeml>')
L.append('<xmeml version="4">')
L.append(' <sequence>')
L.append('  <name>Emily v13 Best Moments Selects</name>')
L.append(f'  <duration>{total_f}</duration>')
L.append('  <rate><timebase>30</timebase><ntsc>TRUE</ntsc></rate>')
L.append('  <media>')
L.append('   <video>')
L.append('    <format><samplecharacteristics><width>3840</width><height>2160</height></samplecharacteristics></format>')

# V1 — Wide (Cam 1 / C9124)
L.append('    <track>')
seq_cursor = 0
for idx, (s, e, label, cam) in enumerate(EDIT):
    dur_f = s2f(e - s)
    src_in = s2f(s + WIDE_OFFSET)
    src_out = src_in + dur_f
    L.append(f'     <clipitem id="V1_clip_{idx}">')
    L.append(f'      <name>{label}</name>')
    L.append(f'      <enabled>{"TRUE" if cam == "W" else "FALSE"}</enabled>')
    L.append(f'      <duration>{WIDE_DUR_F}</duration>')
    L.append('      <rate><timebase>30</timebase><ntsc>TRUE</ntsc></rate>')
    L.append(f'      <start>{seq_cursor}</start><end>{seq_cursor + dur_f}</end>')
    L.append(f'      <in>{src_in}</in><out>{src_out}</out>')
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
    dur_f = s2f(e - s)
    url, fname, file_dur_f, src_in = get_host_src(s)
    src_out = src_in + dur_f
    fid = "Host_C3_file" if s < 1792.3358 else "Host_C4_file"
    L.append(f'     <clipitem id="V2_clip_{idx}">')
    L.append(f'      <name>{label}</name>')
    L.append(f'      <enabled>{"TRUE" if cam == "H" else "FALSE"}</enabled>')
    L.append(f'      <duration>{file_dur_f}</duration>')
    L.append('      <rate><timebase>30</timebase><ntsc>TRUE</ntsc></rate>')
    L.append(f'      <start>{seq_cursor}</start><end>{seq_cursor + dur_f}</end>')
    L.append(f'      <in>{src_in}</in><out>{src_out}</out>')
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
    dur_f = s2f(e - s)
    url, fname, file_dur_f, src_in = get_guest_src(s)
    src_out = src_in + dur_f
    fid = "Guest_C1_file" if s < 1800.4341 else "Guest_C2_file"
    L.append(f'     <clipitem id="V3_clip_{idx}">')
    L.append(f'      <name>{label}</name>')
    L.append(f'      <enabled>{"TRUE" if cam == "G" else "FALSE"}</enabled>')
    L.append(f'      <duration>{file_dur_f}</duration>')
    L.append('      <rate><timebase>30</timebase><ntsc>TRUE</ntsc></rate>')
    L.append(f'      <start>{seq_cursor}</start><end>{seq_cursor + dur_f}</end>')
    L.append(f'      <in>{src_in}</in><out>{src_out}</out>')
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
    dur_f = s2f(e - s)
    src_in = s2f(s)
    src_out = src_in + dur_f
    L.append(f'     <clipitem id="A1_clip_{idx}">')
    L.append(f'      <name>{label}</name>')
    L.append('      <enabled>TRUE</enabled>')
    L.append(f'      <duration>{MIC1_DUR_F}</duration>')
    L.append('      <rate><timebase>30</timebase><ntsc>TRUE</ntsc></rate>')
    L.append(f'      <start>{seq_cursor}</start><end>{seq_cursor + dur_f}</end>')
    L.append(f'      <in>{src_in}</in><out>{src_out}</out>')
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
    dur_f = s2f(e - s)
    src_in = s2f(s)
    src_out = src_in + dur_f
    L.append(f'     <clipitem id="A2_clip_{idx}">')
    L.append(f'      <name>{label}</name>')
    L.append('      <enabled>TRUE</enabled>')
    L.append(f'      <duration>{MIC2_DUR_F}</duration>')
    L.append('      <rate><timebase>30</timebase><ntsc>TRUE</ntsc></rate>')
    L.append(f'      <start>{seq_cursor}</start><end>{seq_cursor + dur_f}</end>')
    L.append(f'      <in>{src_in}</in><out>{src_out}</out>')
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

out_comp = f"{BASE}/Emily_v13_Selects.xml"
with open(out_comp, "w") as f: f.write("\n".join(L))
print(f"\n✅ Generated: {out_comp}")
print(f"   {total_dur:.1f}s | {len(EDIT)} segments | {total_f} frames")
