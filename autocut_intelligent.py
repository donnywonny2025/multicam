#!/usr/bin/env python3
"""
AI Multicam Auto-Cut v3 (Intelligent Cut)
Uses multicam_core for shared logic.
"""
import json, os, numpy as np
import multicam_core as core

# ============================================================
# CONFIG
# ============================================================
BASE = "/Volumes/WORK 2TB/WORK 2026/SANDBOX/Emily"
AUDIO_BASE = "/Volumes/WORK 2TB/WORK 2026/SANDBOX/Audio Organized/Nurse Interview Session (Feb 17)"
MIC1_PATH = f"{AUDIO_BASE}/MIC1.WAV"  
MIC2_PATH = f"{AUDIO_BASE}/MIC2.WAV"  
TRANSCRIPT_PATH = f"{BASE}/Master_MIC1_Transcript.json"

WIDE_CLIPS = [("Cam 1", "C9124.MP4", -9.0102)]
HOST_CLIPS = [("Cam 2", "C0003.MP4", -4.5544), ("Cam 2", "C0004.MP4", 1792.3358)]
GUEST_CLIPS = [("Cam 3", "C0001.MP4", -2.2166), ("Cam 3", "C0002.MP4", 1800.4341)]

# Editorial constraints
WINDOW_MS = 250
MIN_SILENCE_ABSORB = 2.0
MIN_INTERJECTION = 1.0
RAPID_THRESHOLD = 3.0
OPENING_WIDE_SEC = 5.0
SR = 16000

print("Extracting MIC1 (Lillani)...")
mic1 = core.extract_mono(MIC1_PATH, SR, "v3_mic1")
mic2 = core.extract_mono(MIC2_PATH, SR, "v3_mic2")
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

SILENCE_THRESHOLD = 0.008
DOMINANCE_RATIO = 1.3
speaker = []
for i in range(n_windows):
    e1, e2 = mic1_energy[i], mic2_energy[i]
    if e1 < SILENCE_THRESHOLD and e2 < SILENCE_THRESHOLD: speaker.append('S')
    elif e1 > e2 * DOMINANCE_RATIO: speaker.append('H')
    elif e2 > e1 * DOMINANCE_RATIO: speaker.append('G')
    else: speaker.append('W')

segments_mech = []
current_speaker, current_start = speaker[0], 0
for i in range(1, n_windows):
    if speaker[i] != current_speaker:
        segments_mech.append((current_speaker, current_start * WINDOW_MS / 1000.0, i * WINDOW_MS / 1000.0))
        current_speaker, current_start = speaker[i], i
segments_mech.append((current_speaker, current_start * WINDOW_MS / 1000.0, n_windows * WINDOW_MS / 1000.0))

pass1 = []
for spk, s, e in segments_mech:
    if spk in ('S', 'W') and e - s < MIN_SILENCE_ABSORB and pass1:
        pass1[-1] = (pass1[-1][0], pass1[-1][1], e)
    else:
        pass1.append((spk, s, e))

pass2 = []
for spk, s, e in pass1:
    if pass2 and pass2[-1][0] == spk:
        pass2[-1] = (pass2[-1][0], pass2[-1][1], e)
    else:
        pass2.append((spk, s, e))

# ============================================================
# STEP 4: AI INTELLIGENCE LAYER
# ============================================================
print("Analyzing transcript for v3 cuts...")
with open(TRANSCRIPT_PATH, "r") as f:
    ts_data = json.load(f)

questions = []
for t_seg in ts_data.get('segments', []):
    txt, seg_s, seg_e = t_seg.get('text', '').strip(), t_seg.get('start', 0), t_seg.get('end', 0)
    if '?' in txt: questions.append((seg_s, seg_e))

pass3_ai = []
for i, (spk, s, e) in enumerate(pass2):
    dur = e - s
    is_answering_question = False
    if i > 0 and pass2[i-1][0] != spk and spk in ('H','G'):
        prev_e = pass2[i-1][2]
        for (q_s, q_e) in questions:
            if prev_e - 4.0 <= q_e <= prev_e + 1.0:
                is_answering_question = True; break
    
    if is_answering_question and dur > 2.0 and pass3_ai:
        early_cut = max(pass3_ai[-1][1], s - 0.6)
        pass3_ai[-1] = (pass3_ai[-1][0], pass3_ai[-1][1], early_cut)
        s = early_cut

    if dur < MIN_INTERJECTION:
        if pass3_ai:
            pass3_ai[-1] = (pass3_ai[-1][0], pass3_ai[-1][1], e)
            continue
    pass3_ai.append((spk, s, e))

pass4 = []
for spk, s, e in pass3_ai:
    if pass4 and pass4[-1][0] == spk: pass4[-1] = (pass4[-1][0], pass4[-1][1], e)
    else: pass4.append((spk, s, e))

merged = []
i = 0
while i < len(pass4):
    spk, s, e = pass4[i]
    rc, j = 0, i
    while j < len(pass4) and (pass4[j][2] - pass4[j][1]) < RAPID_THRESHOLD:
        rc += 1; j += 1
    if rc >= 3:
        merged.append(('W', pass4[i][1], pass4[j-1][2]))
        i = j
    else:
        merged.append((spk, s, e))
        i += 1

final_merged = []
for spk, s, e in merged:
    if final_merged and final_merged[-1][0] == spk: final_merged[-1] = (final_merged[-1][0], final_merged[-1][1], e)
    else: final_merged.append((spk, s, e))
merged = final_merged

if merged:
    first_spk, first_s, first_e = merged[0]
    if first_e - first_s > OPENING_WIDE_SEC:
        merged[0] = (first_spk, OPENING_WIDE_SEC, first_e)
        merged.insert(0, ('W', 0.0, OPENING_WIDE_SEC))
    else:
        merged[0] = ('W', first_s, first_e)

print(f"Final cut count: {len(merged)}")

# ============================================================
# STEP 5: Generate XML
# ============================================================
track_configs = [("V1", "W", WIDE_CLIPS), ("V2", "H", HOST_CLIPS), ("V3", "G", GUEST_CLIPS)]
file_registry = {}
file_entries = {}
fid_counter = 0

for t_idx, (trk_id, spk_flag, c_list) in enumerate(track_configs):
    rgs = []
    for folder, name, offset in c_list:
        path = f"{BASE}/{folder}/{name}"
        dur_s, dur_f = core.ffprobe_frames(path)
        url = "file://localhost" + core.quote(path)
        if offset < 0: tl_s, src_off, tl_e = 0, -offset, dur_s + offset
        else: tl_s, src_off, tl_e = offset, 0, offset + dur_s
        fid = f"file_{fid_counter}"
        file_entries[fid] = (name, url, dur_f)
        rgs.append((tl_s, tl_e, src_off, fid, dur_f))
        fid_counter += 1
    file_registry[trk_id] = rgs

def find_src(trk_id, t_sec):
    for tl_s, tl_e, src_off, fid, dur_f in file_registry[trk_id]:
        if tl_s <= t_sec < tl_e: return fid, src_off + (t_sec - tl_s)
    return None, None

seq_dur_f = core.sec_to_frames(min_len / SR)
L = core.get_xml_header("Emily Intelligent Cut v3 - 3 Track", seq_dur_f)

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
        tl_s_f, tl_e_f = core.sec_to_frames(s), core.sec_to_frames(e)
        in_f = core.sec_to_frames(src_s)
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

L.extend(core.generate_audio_tracks([("MIC1.WAV", MIC1_PATH), ("MIC2.WAV", MIC2_PATH)]))
L.extend(core.get_xml_footer())

out_comp = f"{BASE}/Emily_v3_INTELLIGENT_CUT.xml"
with open(out_comp, "w") as f: f.write("\n".join(L))
print(f"Wrote: {out_comp}")
