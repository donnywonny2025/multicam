import json, os, subprocess
import numpy as np
from scipy.io import wavfile
from urllib.parse import quote

BASE = "/Volumes/WORK 2TB/WORK 2026/SANDBOX/Emily"
AUDIO_BASE = "/Volumes/WORK 2TB/WORK 2026/SANDBOX/Audio Organized/Nurse Interview Session (Feb 17)"
MIC1_PATH = f"{AUDIO_BASE}/MIC1.WAV"
MIC2_PATH = f"{AUDIO_BASE}/MIC2.WAV"
TRANSCRIPT_PATH = f"{BASE}/Master_MIC1_Transcript.json"

WIDE_OFFSET = 9.0102   
HOST_CLIPS = [
    ("C0003.MP4", "Cam 2", 4.5544, 0, 1792.3358),     
    ("C0004.MP4", "Cam 2", -1792.3358, 1792.3358, 99999),
]
GUEST_CLIPS = [
    ("C0001.MP4", "Cam 3", 2.2166, 0, 1800.4341),
    ("C0002.MP4", "Cam 3", -1800.4341, 1800.4341, 99999),
]

EDIT_ANCHORS = [
    # ── v33: AUDIO TRANSIENT SNAPPING ──
    # [0:00] The Window (Host Cam/Wide)
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

    # [0:58] The Snap (Wide) -> "Emily Ellis is in the building. Let's dive in"
    (141.0, "We", 142.0, "today", "The Snap", "W"),
]

def _load_words():
    with open(TRANSCRIPT_PATH) as f:
        d = json.load(f)
    words = sorted([w for s in d.get("segments", []) for w in s.get("words", [])],
                   key=lambda w: w["start"])
    return words

print("Loading massive WAV files for transient analysis. This may take a few seconds...")
import warnings
with warnings.catch_warnings():
    warnings.simplefilter('ignore')
    fs1, m1d = wavfile.read(MIC1_PATH)
    if len(m1d.shape) > 1: m1d = m1d[:, 0]
    fs2, m2d = wavfile.read(MIC2_PATH)
    if len(m2d.shape) > 1: m2d = m2d[:, 0]

def snap_in(mic_data, fs, w_start, threshold=800):
    start_i = max(0, int((w_start - 0.75) * fs))
    end_i = int((w_start + 0.75) * fs)
    chunk = mic_data[start_i:end_i]
    window_size = int(fs * 0.02)
    step = int(fs * 0.01)
    
    rms_vals = []
    for i in range(0, len(chunk) - window_size, step):
        window = chunk[i:i+window_size]
        rms = np.sqrt(np.mean(window.astype(np.float32)**2))
        rms_vals.append(rms)
        
    peak_idx = np.argmax(rms_vals)
    # Check if peak is even real speech
    if rms_vals[peak_idx] < threshold:
        return w_start - 0.03 # Fallback
        
    actual = w_start
    for i in range(peak_idx, -1, -1):
        if rms_vals[i] < threshold:
            actual = (start_i + (i + 1) * step) / fs
            break
    # Hard offset the Whisper slack - this is the transient slice
    return actual - 0.02 

def snap_out(mic_data, fs, w_end, threshold=400):
    start_i = max(0, int((w_end - 0.75) * fs))
    end_i = int((w_end + 0.75) * fs)
    chunk = mic_data[start_i:end_i]
    window_size = int(fs * 0.02)
    step = int(fs * 0.01)
    
    rms_vals = []
    for i in range(0, len(chunk) - window_size, step):
        window = chunk[i:i+window_size]
        rms = np.sqrt(np.mean(window.astype(np.float32)**2))
        rms_vals.append(rms)
        
    peak_idx = np.argmax(rms_vals)
    if rms_vals[peak_idx] < threshold:
        return w_end + 0.05
        
    actual = w_end
    for i in range(peak_idx, len(rms_vals)):
        if rms_vals[i] < threshold:
            actual = (start_i + (i - 1) * step) / fs
            break
            
    return actual + 0.08 # Let the trailing breath/consonant fade

def get_active_mic(mic1_data, mic2_data, fs, target_t):
    # Calculate rms of both mics around this point
    start_i = int((target_t - 0.5) * fs)
    end_i = int((target_t + 0.5) * fs)
    c1 = mic1_data[start_i:end_i]
    c2 = mic2_data[start_i:end_i]
    
    r1 = np.sqrt(np.mean(c1.astype(np.float32)**2))
    r2 = np.sqrt(np.mean(c2.astype(np.float32)**2))
    return mic1_data if r1 > r2 else mic2_data

def resolve_anchors(anchors, words):
    resolved = []
    errors = []
    
    for first_t, first_w, last_t, last_w, label, cam in anchors:
        in_pt = None
        out_pt = None
        
        # Absolute precision override mode
        if first_w is None:
            in_pt = first_t
        else:
            fw = None
            for w in words:
                if abs(w["start"] - first_t) < 4.0 and w["word"].lower().strip(".,!? ") == first_w.lower():
                    fw = w; break
            if not fw:
                errors.append(f"❌ [{label}] First word '{first_w}' not found near {first_t}s")
                continue
                
            active_mic = get_active_mic(m1d, m2d, fs1, fw["start"])
            in_pt = snap_in(active_mic, fs1, fw["start"])
            
        if last_w is None:
            out_pt = last_t
        else:
            lw = None
            for w in words:
                if abs(w["start"] - last_t) < 4.0 and w["word"].lower().strip(".,!? ") == last_w.lower():
                    lw = w; break
            if not lw:
                errors.append(f"❌ [{label}] Last word '{last_w}' not found near {last_t}s")
                continue
                
            active_mic = get_active_mic(m1d, m2d, fs1, lw["end"])
            out_pt = snap_out(active_mic, fs1, lw["end"])
            
        if in_pt is not None and out_pt is not None:
            resolved.append((in_pt, out_pt, label, cam))
            if first_w is not None:
                offset_in = in_pt - fw["start"]
                print(f"  ✅ [{label}] Auto-Trimmed: In: {offset_in:+.2f}s | {in_pt:.2f} → {out_pt:.2f}")
            else:
                print(f"  ✅ [{label}] Absolute Override | {in_pt:.2f} → {out_pt:.2f}")

    if errors:
        for e in errors: print(e)
        raise SystemExit(1)
    
    return resolved


filler_set = {"um","uh","ums","uhs","hmm","mhm","mmm","ah","hm","mm"}
def intelligent_filler_removal(edit_list, words):
    new_edit = []
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
                    break
        else:
            new_edit.append((start, end, label, cam))
    return new_edit

ALL_WORDS = _load_words()
print("\n1. Resolving Word Anchors using AUDIO TRANSIENTS...")
EDIT = resolve_anchors(EDIT_ANCHORS, ALL_WORDS)
print("\n2. Scrubbing Fillers...")
EDIT = intelligent_filler_removal(EDIT, ALL_WORDS)

total_dur = sum(e-s for s,e,l,c in EDIT)

def s2f(seconds):
    return int(round(seconds * 30000 / 1001))

wide_url = f"file://localhost{quote(os.path.join(BASE, 'Cam 1/C9124.MP4'))}"
host_c3_url = f"file://localhost{quote(os.path.join(BASE, 'Cam 2/C0003.MP4'))}"
host_c4_url = f"file://localhost{quote(os.path.join(BASE, 'Cam 2/C0004.MP4'))}"
guest_c1_url = f"file://localhost{quote(os.path.join(BASE, 'Cam 3/C0001.MP4'))}"
guest_c2_url = f"file://localhost{quote(os.path.join(BASE, 'Cam 3/C0002.MP4'))}"
mic1_url = f"file://localhost{quote(MIC1_PATH)}"
mic2_url = f"file://localhost{quote(MIC2_PATH)}"

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
    if t_sec < 1792.3358:
        return host_c3_url, "C0003.MP4", HOST_C3_DUR_F, s2f(t_sec + 4.5544)
    else:
        return host_c4_url, "C0004.MP4", HOST_C4_DUR_F, s2f(t_sec - 1792.3358)

def get_guest_src(t_sec):
    if t_sec < 1800.4341:
        return guest_c1_url, "C0001.MP4", GUEST_C1_DUR_F, s2f(t_sec + 2.2166)
    else:
        return guest_c2_url, "C0002.MP4", GUEST_C2_DUR_F, s2f(t_sec - 1800.4341)

total_f = sum(s2f(e) - s2f(s) for s, e, l, c in EDIT) + 600

L = []
L.append('<?xml version="1.0" encoding="UTF-8"?>')
L.append('<!DOCTYPE xmeml>')
L.append('<xmeml version="4">')
L.append(' <sequence>')
L.append('  <name>Emily v33 Transient Snap</name>')
L.append(f'  <duration>{total_f}</duration>')
L.append('  <rate><timebase>30</timebase><ntsc>TRUE</ntsc></rate>')
L.append('  <media>')
L.append('   <video>')
L.append('    <format><samplecharacteristics><width>3840</width><height>2160</height></samplecharacteristics></format>')

# V1
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

# V2
L.append('    <track>')
seq_cursor = 0
for idx, (s, e, label, cam) in enumerate(EDIT):
    url, fname, file_dur_f, src_in_f = get_host_src(s)
    _, _, _, src_out_f = get_host_src(e)
    if s < 1792.3358 and e >= 1792.3358:
        src_out_f = s2f(e + HOST_CLIPS[1][2])
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

# V3
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

# END VIDEO, START AUDIO
L.append('   </video>')
L.append('   <audio>')

# A1
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

# A2
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

out_comp = f"{BASE}/Emily_v33_Transient.xml"
with open(out_comp, "w") as f: f.write("\n".join(L))
print(f"\n✅ Generated: {out_comp}")
print(f"   {total_dur:.1f}s | {len(EDIT)} segments | {total_f} frames")

