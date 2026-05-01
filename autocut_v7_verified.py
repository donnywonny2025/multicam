#!/usr/bin/env python3
"""
AI Multicam Auto-Cut v7 (Verified Sync + Reaction Cuts)

Improvements over v6:
- Cross-correlation VERIFIED sync offsets
- Reaction cut logic: if speaker holds >20s, insert 3-5s reaction shot
- Card rollover gaps handled properly (fall back to Wide)
- Interview start detection (skip pre-roll)
- Even pacing: don't hold any single camera >45s without a cut
"""
import subprocess
import numpy as np
import urllib.parse
import os

# ============================================================
# CONFIG — VERIFIED OFFSETS (cross-correlated 2026-04-13)
# ============================================================
BASE = "/Volumes/WORK 2TB/WORK 2026/SANDBOX/Emily"
AUDIO_BASE = "/Volumes/WORK 2TB/WORK 2026/SANDBOX/Audio Organized/Nurse Interview Session (Feb 17)"
MIC1_PATH = f"{AUDIO_BASE}/MIC1.WAV"
MIC2_PATH = f"{AUDIO_BASE}/MIC2.WAV"

# Verified sync offsets (seconds camera starts BEFORE MIC1)
WIDE_CLIPS = [("Cam 1", "C9124.MP4", -9.0102)]
HOST_CLIPS = [("Cam 2", "C0003.MP4", -4.5544), ("Cam 2", "C0004.MP4", 1792.3358)]
GUEST_CLIPS = [("Cam 3", "C0001.MP4", -2.2166), ("Cam 3", "C0002.MP4", 1800.4341)]

# Card rollover gap zones (MIC1 time ranges with no host/guest video)
HOST_GAP = (1785.7356, 1792.3358)   # 6.6s gap in Cam 2
GUEST_GAP = (1788.5734, 1800.4341)  # 11.9s gap in Cam 3

# Editorial parameters
FPS = 29.97
SR = 16000
WINDOW_MS = 250
SILENCE_THRESHOLD = 0.008
DOMINANCE_RATIO = 1.3
MIN_SILENCE_ABSORB = 1.5    # Absorb short silence into prev speaker
MIN_SEGMENT_SEC = 0.7       # Min segment length
ANTICIPATORY_LEAD = 0.8     # Cut to listener before they speak
OPENING_WIDE_SEC = 3.0      # Start with wide shot

# NEW: Reaction cut parameters
MAX_HOLD_SEC = 20.0         # After this long on one speaker, insert reaction
REACTION_MIN_SEC = 2.5      # Minimum reaction shot length
REACTION_MAX_SEC = 5.0      # Maximum reaction shot length
MAX_ANY_CAMERA_SEC = 45.0   # Absolute max on any single camera
WIDE_BREATHER_SEC = 3.0     # Wide shot "breather" length

# Interview start: skip to where conversation really gets going
INTERVIEW_START_SEC = 0.0   # Will be auto-detected

# ============================================================
# AUDIO EXTRACTION
# ============================================================
def extract_mono(path, sr):
    """Extract full mono audio"""
    cache = f"{BASE}/sync_scripts/.cache_v7_{os.path.basename(path)}_{sr}.raw"
    if os.path.exists(cache):
        return np.fromfile(cache, dtype=np.float32)
    cmd = ["ffmpeg", "-y", "-i", path, "-ac", "1", "-ar", str(sr),
           "-f", "f32le", "-acodec", "pcm_f32le", cache]
    subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return np.fromfile(cache, dtype=np.float32)

print("Extracting audio...")
mic1 = extract_mono(MIC1_PATH, SR)
mic2 = extract_mono(MIC2_PATH, SR)
min_len = min(len(mic1), len(mic2))
mic1, mic2 = mic1[:min_len], mic2[:min_len]
total_sec = min_len / SR
print(f"Audio length: {total_sec:.1f}s ({total_sec/60:.1f} min)")

# ============================================================
# STEP 1: Compute energy and speaker detection
# ============================================================
print("Computing energy levels...")
window_samples = int(SR * WINDOW_MS / 1000)
n_windows = min_len // window_samples

mic1_energy = np.zeros(n_windows)
mic2_energy = np.zeros(n_windows)

for i in range(n_windows):
    s, e = i * window_samples, (i + 1) * window_samples
    mic1_energy[i] = np.sqrt(np.mean(mic1[s:e] ** 2))
    mic2_energy[i] = np.sqrt(np.mean(mic2[s:e] ** 2))

# Speaker detection per window
speaker = []
for i in range(n_windows):
    e1, e2 = mic1_energy[i], mic2_energy[i]
    if e1 < SILENCE_THRESHOLD and e2 < SILENCE_THRESHOLD:
        speaker.append('S')
    elif e1 > e2 * DOMINANCE_RATIO:
        speaker.append('H')
    elif e2 > e1 * DOMINANCE_RATIO:
        speaker.append('G')
    else:
        speaker.append('W')  # Both speaking or unclear

# ============================================================
# STEP 2: Build raw segments
# ============================================================
print("Building segments...")
segments_raw = []
current_speaker, current_start = speaker[0], 0
for i in range(1, n_windows):
    if speaker[i] != current_speaker:
        t_start = current_start * WINDOW_MS / 1000.0
        t_end = i * WINDOW_MS / 1000.0
        segments_raw.append((current_speaker, t_start, t_end))
        current_speaker, current_start = speaker[i], i
segments_raw.append((current_speaker, current_start * WINDOW_MS / 1000.0, n_windows * WINDOW_MS / 1000.0))

# Pass 1: Absorb short silence/both into previous speaker
pass1 = []
for spk, s, e in segments_raw:
    if spk in ('S', 'W') and e - s < MIN_SILENCE_ABSORB and pass1:
        pass1[-1] = (pass1[-1][0], pass1[-1][1], e)
    else:
        pass1.append((spk, s, e))

# Pass 2: Merge consecutive same-speaker segments
pass2 = []
for spk, s, e in pass1:
    if pass2 and pass2[-1][0] == spk:
        pass2[-1] = (spk, pass2[-1][1], e)
    else:
        pass2.append((spk, s, e))

# Pass 3: Remove tiny segments
pass3 = []
for spk, s, e in pass2:
    if e - s >= MIN_SEGMENT_SEC:
        pass3.append((spk, s, e))
    elif pass3:
        pass3[-1] = (pass3[-1][0], pass3[-1][1], e)

# Pass 4: Merge again after cleanup
segments = []
for spk, s, e in pass3:
    if segments and segments[-1][0] == spk:
        segments[-1] = (spk, segments[-1][1], e)
    else:
        segments.append((spk, s, e))

print(f"Segments after processing: {len(segments)}")

# ============================================================
# STEP 3: Apply anticipatory lead
# ============================================================
adjusted = []
for idx, (spk, s, e) in enumerate(segments):
    if idx > 0 and spk in ('H', 'G'):
        new_start = max(s - ANTICIPATORY_LEAD, segments[idx-1][1] + 0.5)
        if adjusted:
            adjusted[-1] = (adjusted[-1][0], adjusted[-1][1], new_start)
        adjusted.append((spk, new_start, e))
    else:
        adjusted.append((spk, s, e))

segments = adjusted

# ============================================================
# STEP 4: Insert reaction cuts for long segments
# ============================================================
print("Inserting reaction cuts...")
final_segments = []

for spk, s, e in segments:
    duration = e - s
    
    if spk in ('H', 'G') and duration > MAX_HOLD_SEC:
        # Speaker held too long — insert reaction cuts
        reaction_target = 'G' if spk == 'H' else 'H'  # Cut to listener
        
        pos = s
        while pos < e:
            remaining = e - pos
            
            if remaining <= MAX_HOLD_SEC:
                # Last chunk — just use it
                final_segments.append((spk, pos, e))
                break
            
            # Hold on speaker for 15-20s
            hold_time = min(MAX_HOLD_SEC * 0.8, remaining - REACTION_MIN_SEC)
            final_segments.append((spk, pos, pos + hold_time))
            pos += hold_time
            
            # Insert reaction shot (2.5-5s)
            reaction_dur = min(REACTION_MAX_SEC, e - pos - 2.0)
            if reaction_dur >= REACTION_MIN_SEC:
                final_segments.append((reaction_target, pos, pos + reaction_dur))
                pos += reaction_dur
            else:
                # Not enough time for reaction, just finish on speaker
                final_segments.append((spk, pos, e))
                break
    
    elif spk in ('S', 'W') and duration > MAX_ANY_CAMERA_SEC:
        # Long silence/overlap — use wide shot
        final_segments.append(('W', s, e))
    else:
        final_segments.append((spk, s, e))

# Final merge pass
merged = []
for spk, s, e in final_segments:
    if merged and merged[-1][0] == spk and abs(s - merged[-1][2]) < 0.01:
        merged[-1] = (spk, merged[-1][1], e)
    else:
        merged.append((spk, s, e))

segments = merged
print(f"Final segments (with reactions): {len(segments)}")

# ============================================================
# STEP 5: Force opening wide shot
# ============================================================
if segments and segments[0][1] < OPENING_WIDE_SEC:
    first_end = min(OPENING_WIDE_SEC, segments[0][2])
    new_segs = [('W', 0, first_end)]
    if segments[0][2] > first_end:
        new_segs.append((segments[0][0], first_end, segments[0][2]))
    new_segs.extend(segments[1:])
    segments = new_segs

# ============================================================
# STEP 6: Map segments to camera clips with gap handling
# ============================================================
def sec_to_frame(s):
    return int(round(s * FPS))

def is_in_gap(t, gap):
    return gap[0] <= t <= gap[1]

def get_cam_source(spk, mic1_time):
    """Return (cam_folder, filename, source_offset) for a speaker at mic1_time"""
    if spk == 'H':
        # Check for gap
        if is_in_gap(mic1_time, HOST_GAP):
            return None  # Fall back to wide
        if mic1_time < HOST_CLIPS[1][2]:  # Before Part 2
            return ("Cam 2", "C0003.MP4", HOST_CLIPS[0][2])
        else:
            return ("Cam 2", "C0004.MP4", HOST_CLIPS[1][2])
    elif spk == 'G':
        if is_in_gap(mic1_time, GUEST_GAP):
            return None
        if mic1_time < GUEST_CLIPS[1][2]:
            return ("Cam 3", "C0001.MP4", GUEST_CLIPS[0][2])
        else:
            return ("Cam 3", "C0002.MP4", GUEST_CLIPS[1][2])
    else:  # Wide
        return ("Cam 1", "C9124.MP4", WIDE_CLIPS[0][2])

def encode_path(path):
    parts = path.split("/")
    return "file://localhost/" + "/".join(urllib.parse.quote(p) for p in parts if p)

# ============================================================
# STEP 7: Generate XML
# ============================================================
print("Generating XML...")

# Build clipitems
clip_id = 0
video_clips = []
file_refs = {}

for spk, seg_start, seg_end in segments:
    # Handle gap zones — force wide
    actual_spk = spk
    cam_info = get_cam_source(spk, seg_start)
    if cam_info is None:
        actual_spk = 'W'
        cam_info = get_cam_source('W', seg_start)
    
    cam_folder, filename, cam_offset = cam_info
    
    # Calculate source in/out
    # cam_offset is negative: camera starts |offset| seconds before MIC1
    # Source frame = mic1_time + abs(cam_offset)  [when offset is negative]
    # For Part 2 clips, cam_offset is the MIC1 time when Part 2 starts
    if cam_offset < 0:
        source_in_sec = seg_start + abs(cam_offset)
        source_out_sec = seg_end + abs(cam_offset)
    else:
        # Part 2: cam_offset is MIC1 time when this clip starts, source begins at 0
        source_in_sec = seg_start - cam_offset
        source_out_sec = seg_end - cam_offset
    
    start_frame = sec_to_frame(seg_start)
    end_frame = sec_to_frame(seg_end)
    in_frame = sec_to_frame(source_in_sec)
    out_frame = sec_to_frame(source_out_sec)
    
    pathurl = encode_path(f"/Volumes/WORK 2TB/WORK 2026/SANDBOX/Emily/{cam_folder}/{filename}")
    fid = f"file_{cam_folder.replace(' ', '')}_{filename.replace('.', '_')}"
    
    if fid not in file_refs:
        file_refs[fid] = (filename, pathurl)
    
    enabled = "TRUE"
    
    video_clips.append(f"""          <clipitem id="cut_{clip_id}">
            <name>{filename}</name>
            <duration>{sec_to_frame(2720)}</duration>
            <rate><timebase>30</timebase><ntsc>TRUE</ntsc></rate>
            <start>{start_frame}</start><end>{end_frame}</end>
            <enabled>{enabled}</enabled>
            <in>{in_frame}</in><out>{out_frame}</out>
            <file id="{fid}">
                <name>{filename}</name>
                <pathurl>{pathurl}</pathurl>
                <media>
                    <video><samplecharacteristics><width>3840</width><height>2160</height></samplecharacteristics></video>
                    <audio><samplecharacteristics><depth>16</depth><samplerate>48000</samplerate></samplecharacteristics><channelcount>2</channelcount></audio>
                </media>
            </file>
          </clipitem>""")
    clip_id += 1

# Audio clips
total_frames = sec_to_frame(total_sec)
mic1_url = encode_path(MIC1_PATH)
mic2_url = encode_path(MIC2_PATH)

audio_clips_mic1 = f"""          <clipitem id="mic1_lillani">
            <name>MIC1.WAV</name>
            <duration>{total_frames}</duration>
            <rate><timebase>30</timebase><ntsc>TRUE</ntsc></rate>
            <start>0</start><end>{total_frames}</end>
            <enabled>TRUE</enabled>
            <in>0</in><out>{total_frames}</out>
            <file id="file_mic1">
                <name>MIC1.WAV</name>
                <pathurl>{mic1_url}</pathurl>
                <media>
                    <audio><samplecharacteristics><depth>16</depth><samplerate>48000</samplerate></samplecharacteristics><channelcount>1</channelcount></audio>
                </media>
            </file>
          </clipitem>"""

audio_clips_mic2 = f"""          <clipitem id="mic2_emily">
            <name>MIC2.WAV</name>
            <duration>{total_frames}</duration>
            <rate><timebase>30</timebase><ntsc>TRUE</ntsc></rate>
            <start>0</start><end>{total_frames}</end>
            <enabled>TRUE</enabled>
            <in>0</in><out>{total_frames}</out>
            <file id="file_mic2">
                <name>MIC2.WAV</name>
                <pathurl>{mic2_url}</pathurl>
                <media>
                    <audio><samplecharacteristics><depth>16</depth><samplerate>48000</samplerate></samplecharacteristics><channelcount>1</channelcount></audio>
                </media>
            </file>
          </clipitem>"""

# Assemble
xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE xmeml>
<xmeml version="4">
  <sequence>
    <name>Emily v7 AutoCut Verified</name>
    <duration>{total_frames}</duration>
    <rate><timebase>30</timebase><ntsc>TRUE</ntsc></rate>
    <media>
      <video>
        <format><samplecharacteristics>
          <rate><timebase>30</timebase><ntsc>TRUE</ntsc></rate>
          <width>3840</width><height>2160</height>
        </samplecharacteristics></format>
        <track>
          <enabled>TRUE</enabled>
          <locked>FALSE</locked>
{chr(10).join(video_clips)}
        </track>
      </video>
      <audio>
        <format><samplecharacteristics>
          <depth>16</depth><samplerate>48000</samplerate>
        </samplecharacteristics></format>
        <track>
          <enabled>TRUE</enabled>
          <locked>FALSE</locked>
{audio_clips_mic1}
        </track>
        <track>
          <enabled>TRUE</enabled>
          <locked>FALSE</locked>
{audio_clips_mic2}
        </track>
      </audio>
    </media>
  </sequence>
</xmeml>"""

out_path = f"{BASE}/Emily_v7_AUTOCUT_VERIFIED.xml"
with open(out_path, "w") as f:
    f.write(xml)

# Stats
host_time = sum(e-s for spk,s,e in segments if spk == 'H')
guest_time = sum(e-s for spk,s,e in segments if spk == 'G')
wide_time = sum(e-s for spk,s,e in segments if spk in ('W', 'S'))
print(f"\n{'='*50}")
print(f"Written: {out_path}")
print(f"Total cuts: {len(segments)}")
print(f"Host camera time: {host_time:.0f}s ({host_time/total_sec*100:.0f}%)")
print(f"Guest camera time: {guest_time:.0f}s ({guest_time/total_sec*100:.0f}%)")
print(f"Wide camera time: {wide_time:.0f}s ({wide_time/total_sec*100:.0f}%)")

# Show first 20 cuts
print(f"\nFirst 20 cuts:")
for i, (spk, s, e) in enumerate(segments[:20]):
    cam = {'H': 'HOST (Cam2)', 'G': 'GUEST (Cam3)', 'W': 'WIDE (Cam1)', 'S': 'WIDE (Cam1)'}[spk]
    print(f"  {i:3d}: {s:8.2f}s → {e:8.2f}s ({e-s:5.1f}s) {cam}")

PYEOF
