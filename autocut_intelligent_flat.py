#!/usr/bin/env python3
"""
AI Multicam Auto-Cut v4 (Intelligent Flat)
Applies transcript-aware editorial rules and exports a SINGLE track
where AI choices are baked into one track for easy playback.
"""
import subprocess, numpy as np, json, os, re
from urllib.parse import quote

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

WINDOW_MS = 250
MIN_SILENCE_ABSORB = 2.0
MIN_INTERJECTION = 1.0
RAPID_THRESHOLD = 3.0
OPENING_WIDE_SEC = 5.0
SR = 16000

print("Extracting MIC1 (Lillani)...")
def extract_mono(path, sr=16000):
    tmp = "/tmp/_autocut_v4_tmp.raw"
    subprocess.run(["ffmpeg", "-y", "-i", path, "-vn", "-ac", "1", "-ar", str(sr), "-f", "s16le", tmp], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    data = np.fromfile(tmp, dtype=np.int16).astype(np.float32) / 32768.0
    os.remove(tmp)
    return data

mic1 = extract_mono(MIC1_PATH, SR)
mic2 = extract_mono(MIC2_PATH, SR)
min_len = min(len(mic1), len(mic2))
mic1, mic2 = mic1[:min_len], mic2[:min_len]

# ============================================================
# STEP 2/3: Compute energy & Speaker Detection
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
print("Analyzing transcript for intelligent cuts...")
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

print(f"Final cut count (AI passed): {len(merged)}")

# ============================================================
# STEP 5: Generate SINGLE-TRACK Premiere XML
# ============================================================
def sec_to_frames(sec): return int(round(sec * 23.976))

def ffprobe_frames(path):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path], capture_output=True, text=True)
    sec = float(r.stdout.strip())
    return sec, int(round(sec * 23.976))

print("Building file registry...")
SPEAKER_TO_CAM = {'H': 'V2', 'G': 'V3', 'W': 'V1', 'S': 'V1'}
all_cam_clips = [("V1", WIDE_CLIPS), ("V2", HOST_CLIPS), ("V3", GUEST_CLIPS)]

file_registry = {}
file_entries = {}
fid_counter = 0

for cam_label, clip_list in all_cam_clips:
    ranges = []
    for folder, name, offset in clip_list:
        path = f"{BASE}/{folder}/{name}"
        dur_sec, dur_frames = ffprobe_frames(path)
        url = "file://localhost" + quote(path)
        if offset < 0:
            ranges.append((0, dur_sec + offset, -offset, f"file_{fid_counter}", dur_frames))
        else:
            ranges.append((offset, offset + dur_sec, 0, f"file_{fid_counter}", dur_frames))
        file_entries[f"file_{fid_counter}"] = (name, url, dur_frames)
        fid_counter += 1
    file_registry[cam_label] = ranges

def find_source_file(cam, time_sec):
    for tl_start, tl_end, src_offset, fid, dur_f in file_registry[cam]:
        if tl_start <= time_sec < tl_end:
            return fid, src_offset + (time_sec - tl_start)
    return None, None

print("Generating v4 Intelligent FLAT XML...")
seq_dur = sec_to_frames(min_len / SR)

L = []
L.append('<?xml version="1.0" encoding="UTF-8"?>')
L.append('<!DOCTYPE xmeml>')
L.append('<xmeml version="4">')
L.append('  <sequence>')
L.append('    <name>Emily Intelligent Cut v4 - Flat Video</name>')
L.append(f'    <duration>{seq_dur}</duration>')
L.append('    <rate><timebase>24</timebase><ntsc>TRUE</ntsc></rate>')
L.append('    <media>')
L.append('      <video>')
L.append('        <format><samplecharacteristics>')
L.append('          <rate><timebase>24</timebase><ntsc>TRUE</ntsc></rate>')
L.append('          <width>3840</width><height>2160</height>')
L.append('        </samplecharacteristics></format>')
L.append('        <track>')

used_files = set()
clip_counter = 0

for spk, start_sec, end_sec in merged:
    cam = SPEAKER_TO_CAM[spk]
    fid, src_start = find_source_file(cam, start_sec)
    
    if fid is None: fid, src_start = find_source_file('V1', start_sec)
    if fid is None: continue
    
    _, src_end = find_source_file(cam if find_source_file(cam, end_sec - 0.1)[0] else 'V1', end_sec - 0.1)
    if src_end is None: src_end = src_start + (end_sec - start_sec)
    
    name, url, dur_f = file_entries[fid]
    tl_start_f = sec_to_frames(start_sec)
    tl_end_f = sec_to_frames(end_sec)
    in_f = sec_to_frames(src_start)
    out_f = in_f + (tl_end_f - tl_start_f)
    
    if out_f > dur_f:
        out_f = dur_f
        tl_end_f = tl_start_f + (out_f - in_f)
    
    if tl_end_f <= tl_start_f: continue
    
    L.append(f'          <clipitem id="cut_{clip_counter}">')
    L.append(f'            <name>{name}</name>')
    L.append(f'            <duration>{dur_f}</duration>')
    L.append('            <rate><timebase>24</timebase><ntsc>TRUE</ntsc></rate>')
    L.append(f'            <start>{tl_start_f}</start><end>{tl_end_f}</end>')
    L.append(f'            <in>{in_f}</in><out>{out_f}</out>')
    L.append(f'            <file id="{fid}">')
    L.append(f'                <name>{name}</name>')
    L.append(f'                <pathurl>{url}</pathurl>')
    L.append('                <media><video><samplecharacteristics><width>3840</width><height>2160</height></samplecharacteristics></video><audio><samplecharacteristics><depth>16</depth><samplerate>48000</samplerate></samplecharacteristics><channelcount>2</channelcount></audio></media>')
    L.append('            </file>')
    L.append('          </clipitem>')
    clip_counter += 1

L.append('        </track>')
L.append('      </video>')

L.append('      <audio>')
L.append('        <numchannels>2</numchannels>')
L.append('        <format><samplecharacteristics><depth>16</depth><samplerate>48000</samplerate></samplecharacteristics></format>')

for mic_idx, (mic_name, mic_path) in enumerate([("MIC1.WAV", MIC1_PATH), ("MIC2.WAV", MIC2_PATH)]):
    mic_dur_sec, mic_dur_f = ffprobe_frames(mic_path)
    url = "file://localhost" + quote(mic_path)
    L.append('        <track>')
    L.append(f'          <clipitem id="mic_{mic_idx}">')
    L.append(f'            <name>{mic_name}</name>')
    L.append(f'            <duration>{mic_dur_f}</duration>')
    L.append('            <rate><timebase>24</timebase><ntsc>TRUE</ntsc></rate>')
    L.append(f'            <start>0</start><end>{mic_dur_f}</end>')
    L.append(f'            <in>0</in><out>{mic_dur_f}</out>')
    L.append(f'            <file id="file_mic_{mic_idx}">')
    L.append(f'                <name>{mic_name}</name>')
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
out_path = f"{BASE}/Emily_v4_INTELLIGENT_FLAT.xml"
with open(out_path, "w") as f:
    f.write(xml)

print(f"\nWrote: {out_path}")
print(f"Total edit points: {clip_counter}")
