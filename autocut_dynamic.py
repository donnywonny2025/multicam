#!/usr/bin/env python3
"""
AI Multicam Auto-Cut v5 (Dynamic)
Applies transcript-aware editorial rules with dynamic reaction triggers.
Lays down a 3-track stack where all tracks are cut simultaneously.
"""
import subprocess, numpy as np, json, os, re
from urllib.parse import quote

# ============================================================
# CONFIG
# ============================================================
BASE = "/Volumes/WORK 2TB/WORK 2026/SANDBOX/Emily"
AUDIO_BASE = "/Volumes/WORK 2TB/WORK 2026/SANDBOX/Audio Organized/Nurse Interview Session (Feb 17)"
MIC1_PATH = f"{AUDIO_BASE}/MIC1.WAV"  # Host (Lillani)
MIC2_PATH = f"{AUDIO_BASE}/MIC2.WAV"  # Guest (Emily)
TRANSCRIPT_PATH = f"{BASE}/Master_MIC1_Transcript.json"

WIDE_CLIPS = [("Cam 1", "C9124.MP4", -9.0102)]
HOST_CLIPS = [("Cam 2", "C0003.MP4", -4.5544), ("Cam 2", "C0004.MP4", 1792.3358)]
GUEST_CLIPS = [("Cam 3", "C0001.MP4", -2.2166), ("Cam 3", "C0002.MP4", 1800.4341)]

# Editorial constraints (REFINED for v5 Dynamic)
WINDOW_MS = 250
MIN_SILENCE_ABSORB = 1.5   # Snappier silence handling
MIN_INTERJECTION = 0.7     # Lowered to catch more quick reactions
RAPID_THRESHOLD = 2.5      # Snappier back-and-forth before going wide
OPENING_WIDE_SEC = 4.0     # Faster intro
SR = 16000
ANTICIPATORY_LEAD = 0.8    # Parameterized lead time for answers

print("Extracting MIC1 (Lillani)...")
def extract_mono(path, sr=16000):
    tmp = "/tmp/_autocut_v5_tmp.raw"
    subprocess.run(["ffmpeg", "-y", "-i", path, "-vn", "-ac", "1", "-ar", str(sr), "-f", "s16le", tmp], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    data = np.fromfile(tmp, dtype=np.int16).astype(np.float32) / 32768.0
    os.remove(tmp)
    return data

mic1 = extract_mono(MIC1_PATH, SR)
mic2 = extract_mono(MIC2_PATH, SR)
min_len = min(len(mic1), len(mic2))
mic1, mic2 = mic1[:min_len], mic2[:min_len]

# ============================================================
# STEP 2: Compute energy
# ============================================================
window_samples = int(SR * WINDOW_MS / 1000)
n_windows = min_len // window_samples
mic1_energy = np.zeros(n_windows)
mic2_energy = np.zeros(n_windows)

for i in range(n_windows):
    s, e = i * window_samples, (i + 1) * window_samples
    mic1_energy[i] = np.sqrt(np.mean(mic1[s:e] ** 2))
    mic2_energy[i] = np.sqrt(np.mean(mic2[s:e] ** 2))

# ============================================================
# STEP 3: Audio Classifications
# ============================================================
SILENCE_THRESHOLD = 0.008
DOMINANCE_RATIO = 1.3
speaker = []
for i in range(n_windows):
    e1, e2 = mic1_energy[i], mic2_energy[i]
    if e1 < SILENCE_THRESHOLD and e2 < SILENCE_THRESHOLD: speaker.append('S')
    elif e1 > e2 * DOMINANCE_RATIO: speaker.append('H')
    elif e2 > e1 * DOMINANCE_RATIO: speaker.append('G')
    else: speaker.append('W')

# Mechanical segmentation
segments_mech = []
current_speaker, current_start = speaker[0], 0
for i in range(1, n_windows):
    if speaker[i] != current_speaker:
        segments_mech.append((current_speaker, current_start * WINDOW_MS / 1000.0, i * WINDOW_MS / 1000.0))
        current_speaker, current_start = speaker[i], i
segments_mech.append((current_speaker, current_start * WINDOW_MS / 1000.0, n_windows * WINDOW_MS / 1000.0))

# Pass 1: Absorb short silence
pass1 = []
for spk, s, e in segments_mech:
    if spk in ('S', 'W') and e - s < MIN_SILENCE_ABSORB and pass1:
        pass1[-1] = (pass1[-1][0], pass1[-1][1], e)
    else:
        pass1.append((spk, s, e))

# Pass 2: Merge consecutive
pass2 = []
for spk, s, e in pass1:
    if pass2 and pass2[-1][0] == spk:
        pass2[-1] = (pass2[-1][0], pass2[-1][1], e)
    else:
        pass2.append((spk, s, e))

# ============================================================
# STEP 4: AI INTELLIGENCE LAYER (DYNAMIC V5)
# ============================================================
print("Analyzing transcript for dynamic triggers...")
with open(TRANSCRIPT_PATH, "r") as f:
    ts_data = json.load(f)

# Build a list of context triggers
questions = []
laughs = []
emily_mentions = [] # Times when Lillani mentions Emily

for t_seg in ts_data.get('segments', []):
    txt = t_seg.get('text', '').strip()
    seg_s, seg_e = t_seg.get('start', 0), t_seg.get('end', 0)
    
    if '?' in txt:
        questions.append((seg_s, seg_e))
    
    if '[laugh' in txt.lower() or 'haha' in txt.lower() or 'funny' in txt.lower():
        laughs.append((seg_s, seg_e))
        
    # Mention triggers (looking for Emily/Nurse Silly in Lillani's speech)
    # We assume MIC1 transcript roughly tracks Lillani, though it picks up both.
    # We'll filter for Lillani dominance in the window shortly.
    lower_txt = txt.lower()
    if any(k in lower_txt for k in ["emily", "silly", "you"]):
        emily_mentions.append((seg_s, seg_e))

pass3_ai = []
for i, (spk, s, e) in enumerate(pass2):
    dur = e - s
    
    # 1. QUESTION ANTICIPATION
    is_answering_question = False
    if i > 0 and pass2[i-1][0] != spk and spk in ('H','G'):
        prev_e = pass2[i-1][2]
        for (q_s, q_e) in questions:
            if prev_e - 4.0 <= q_e <= prev_e + 1.0:
                is_answering_question = True
                break
    
    if is_answering_question and dur > 2.0 and pass3_ai:
        early_cut = max(pass3_ai[-1][1], s - ANTICIPATORY_LEAD)
        pass3_ai[-1] = (pass3_ai[-1][0], pass3_ai[-1][1], early_cut)
        s = early_cut

    # 2. EMILY MENTION TRIGGER (Reaction shot)
    # If Lillani is talking and mentions Emily/You, we should potentially cut to Emily for a reaction
    if spk == 'H' and dur > 3.0:
        for (m_s, m_e) in emily_mentions:
            if s <= m_s <= e - 2.0:
                # We found a mention mid-segment! Let's slice it.
                # Cut to Guest for 1.5s then back to Host
                pass3_ai.append(('H', s, m_s))
                pass3_ai.append(('G', m_s, m_s + 1.5))
                s = m_s + 1.5
                # Continue checking the rest of the segment duration
    
    # 3. REACTION PADDING (Laughs)
    # If someone laughs, hold on them for an extra 1.2s
    for (l_s, l_e) in laughs:
        if s <= l_s <= e:
            e = min(e + 1.2, min_len/SR) # Pad the end index
            # This padding might overlap with the next speaker, which is fine (reaction shot)
            break

    # 4. INTERJECTION FILTER
    if dur < MIN_INTERJECTION:
        if pass3_ai:
            pass3_ai[-1] = (pass3_ai[-1][0], pass3_ai[-1][1], e)
            continue
            
    pass3_ai.append((spk, s, e))

# Final Merge of same speakers after AI tweaking
pass4 = []
for spk, s, e in pass3_ai:
    if pass4 and pass4[-1][0] == spk:
        pass4[-1] = (pass4[-1][0], pass4[-1][1], e)
    else:
        pass4.append((spk, s, e))

# Step 5: Rapid Fire -> WIDE
merged = []
i = 0
while i < len(pass4):
    spk, s, e = pass4[i]
    rc = 0
    j = i
    while j < len(pass4) and (pass4[j][2] - pass4[j][1]) < RAPID_THRESHOLD:
        rc += 1
        j += 1
    if rc >= 3:
        merged.append(('W', pass4[i][1], pass4[j-1][2]))
        i = j
    else:
        merged.append((spk, s, e))
        i += 1

# Flatten
final_merged = []
for spk, s, e in merged:
    if final_merged and final_merged[-1][0] == spk:
        final_merged[-1] = (final_merged[-1][0], final_merged[-1][1], e)
    else:
        final_merged.append((spk, s, e))
merged = final_merged

if merged:
    first_spk, first_s, first_e = merged[0]
    if first_e - first_s > OPENING_WIDE_SEC:
        merged[0] = (first_spk, OPENING_WIDE_SEC, first_e)
        merged.insert(0, ('W', 0.0, OPENING_WIDE_SEC))
    else:
        merged[0] = ('W', first_s, first_e)

print(f"Final cut count (AI passed): {len(merged)}")

# ============================================================
# STEP 5: Generate 3-Track Premiere XML
# ============================================================
def sec_to_frames(sec): return int(round(sec * 23.976))

def ffprobe_frames(path):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path], capture_output=True, text=True)
    sec = float(r.stdout.strip())
    return sec, int(round(sec * 23.976))

print("Building file registry...")
track_configs = [
    ("V1", "W", WIDE_CLIPS),   # Track 1 is WIDE
    ("V2", "H", HOST_CLIPS),   # Track 2 is HOST (Lillani)
    ("V3", "G", GUEST_CLIPS)   # Track 3 is GUEST (Emily)
]

file_registry = {}
file_entries = {}
fid_counter = 0

for t_idx, (trk_id, spk_flag, c_list) in enumerate(track_configs):
    rgs = []
    for folder, name, offset in c_list:
        path = f"{BASE}/{folder}/{name}"
        dur_s, dur_f = ffprobe_frames(path)
        url = "file://localhost" + quote(path)
        if offset < 0:
            tl_s, src_off, tl_e = 0, -offset, dur_s + offset
        else:
            tl_s, src_off, tl_e = offset, 0, offset + dur_s
        fid = f"file_{fid_counter}"
        file_entries[fid] = (name, url, dur_f)
        rgs.append((tl_s, tl_e, src_off, fid, dur_f))
        fid_counter += 1
    file_registry[trk_id] = rgs

def find_src(trk_id, t_sec):
    for tl_s, tl_e, src_off, fid, dur_f in file_registry[trk_id]:
        if tl_s <= t_sec < tl_e: return fid, src_off + (t_sec - tl_s)
    return None, None

print("Generating v5 Dynamic 3-Track XML...")
seq_dur = sec_to_frames(min_len / SR)
L = ['<?xml version="1.0" encoding="UTF-8"?>', '<!DOCTYPE xmeml>', '<xmeml version="4">', '  <sequence>', '    <name>Emily Dynamic Cut v5 - 3 Track</name>', f'    <duration>{seq_dur}</duration>', '    <rate><timebase>24</timebase><ntsc>TRUE</ntsc></rate>', '    <media>', '      <video>', '        <format><samplecharacteristics>', '          <rate><timebase>24</timebase><ntsc>TRUE</ntsc></rate>', '          <width>3840</width><height>2160</height>', '        </samplecharacteristics></format>']

clip_counter = 0
spk_to_track = {'W': 'V1', 'S': 'V1', 'H': 'V2', 'G': 'V3'}

for trk_idx, (trk_id, spk_flag, _) in enumerate(track_configs):
    L.append('        <track>')
    L.append('          <enabled>TRUE</enabled>')
    L.append('          <locked>FALSE</locked>')
    for (active_spk, s, e) in merged:
        fid, src_s = find_src(trk_id, s)
        if fid is None: continue
        name, url, dur_f = file_entries[fid]
        tl_s_f, tl_e_f = sec_to_frames(s), sec_to_frames(e)
        in_f = sec_to_frames(src_s)
        out_f = in_f + (tl_e_f - tl_s_f)
        if out_f > dur_f:
            out_f = dur_f
            tl_e_f = tl_s_f + (out_f - in_f)
        if tl_e_f <= tl_s_f: continue
        is_active = (spk_to_track[active_spk] == trk_id)
        L.append(f'          <clipitem id="cut_{clip_counter}">')
        L.append(f'            <name>{name}</name>')
        L.append(f'            <duration>{dur_f}</duration>')
        L.append('            <rate><timebase>24</timebase><ntsc>TRUE</ntsc></rate>')
        L.append(f'            <start>{tl_s_f}</start><end>{tl_e_f}</end>')
        L.append(f'            <enabled>{"TRUE" if is_active else "FALSE"}</enabled>')
        L.append(f'            <in>{in_f}</in><out>{out_f}</out>')
        L.append(f'            <file id="{fid}">')
        L.append(f'                <name>{name}</name>')
        L.append(f'                <pathurl>{url}</pathurl>')
        L.append('                <media>')
        L.append('                    <video><samplecharacteristics><width>3840</width><height>2160</height></samplecharacteristics></video>')
        L.append('                    <audio><samplecharacteristics><depth>16</depth><samplerate>48000</samplerate></samplecharacteristics><channelcount>2</channelcount></audio>')
        L.append('                </media>')
        L.append('            </file>')
        L.append('          </clipitem>')
        clip_counter += 1
    L.append('        </track>')
L.append('      </video>')

# AUDIO TRACKS
L.append('      <audio>')
L.append('        <numchannels>2</numchannels>')
L.append('        <format><samplecharacteristics><depth>16</depth><samplerate>48000</samplerate></samplecharacteristics></format>')

for mic_idx, (m_id, m_path) in enumerate([("MIC1.WAV", MIC1_PATH), ("MIC2.WAV", MIC2_PATH)]):
    m_dur_s, m_dur_f = ffprobe_frames(m_path)
    url = "file://localhost" + quote(m_path)
    L.append('        <track>')
    L.append(f'          <clipitem id="mic_{mic_idx}">')
    L.append(f'            <name>{m_id}</name>')
    L.append(f'            <duration>{m_dur_f}</duration>')
    L.append('            <rate><timebase>24</timebase><ntsc>TRUE</ntsc></rate>')
    L.append(f'            <start>0</start><end>{m_dur_f}</end>')
    L.append(f'            <in>0</in><out>{m_dur_f}</out>')
    L.append(f'            <file id="file_mic_{mic_idx}">')
    L.append(f'                <name>{m_id}</name>')
    L.append(f'                <pathurl>{url}</pathurl>')
    L.append('                <media><audio><samplecharacteristics><depth>16</depth><samplerate>48000</samplerate></samplecharacteristics><channelcount>2</channelcount></audio></media>')
    L.append('            </file>')
    L.append('          </clipitem>')
    L.append('        </track>')

L.append('      </audio>')
L.append('    </media>')
L.append('  </sequence>')
L.append('</xmeml>')

xml = "\n".join(L)
out_comp = f"{BASE}/Emily_v5_DYNAMIC_CUT.xml"
with open(out_comp, "w") as f: f.write(xml)
print(f"Wrote: {out_comp}")
print(f"Total edit points across 3 tracks: {clip_counter}")
