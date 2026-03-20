#!/usr/bin/env python3
"""
AI Multicam Auto-Cut for Premiere Pro.
Compares MIC1 (Lillani/host) vs MIC2 (Emily/guest) waveform energy
to determine who's talking, then generates a single-track XML
that switches camera angles automatically.
"""
import subprocess, numpy as np, json, os
from urllib.parse import quote

# ============================================================
# CONFIG
# ============================================================
BASE = "/Volumes/WORK 2TB/WORK 2026/SANDBOX/Emily"
AUDIO_BASE = "/Volumes/WORK 2TB/WORK 2026/SANDBOX/Audio Organized/Nurse Interview Session (Feb 17)"

MIC1_PATH = f"{AUDIO_BASE}/MIC1.WAV"  # Lillani (host)
MIC2_PATH = f"{AUDIO_BASE}/MIC2.WAV"  # Emily (guest)

# Camera assignments
WIDE_CLIPS = [("Cam 1", "C9124.MP4", -9.0102)]
HOST_CLIPS = [("Cam 2", "C0003.MP4", -4.5544), ("Cam 2", "C0004.MP4", 1792.3358)]
GUEST_CLIPS = [("Cam 3", "C0001.MP4", -2.2166), ("Cam 3", "C0002.MP4", 1800.4341)]

# Editorial style
WINDOW_MS = 250          # Smaller window = more responsive to short interjections
MIN_SILENCE_ABSORB = 2.0 # Silence under this duration gets absorbed into current speaker
MIN_INTERJECTION = 1.0   # Cuts shorter than this are mic bleed, not real speech
RAPID_THRESHOLD = 3.0    # If 3+ consecutive cuts are all under this, use wide instead
OPENING_WIDE_SEC = 5.0   # Start on wide for this long
SR = 16000               # Sample rate for analysis

# ============================================================
# STEP 1: Extract and analyze waveforms
# ============================================================
def extract_mono(path, sr=16000):
    """Extract full audio as mono numpy array."""
    tmp = "/tmp/_autocut_tmp.raw"
    subprocess.run([
        "ffmpeg", "-y", "-i", path, "-vn", "-ac", "1", "-ar", str(sr),
        "-f", "s16le", tmp
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    data = np.fromfile(tmp, dtype=np.int16).astype(np.float32) / 32768.0
    os.remove(tmp)
    return data

print("Extracting MIC1 (Lillani)...")
mic1 = extract_mono(MIC1_PATH, SR)
print(f"  {len(mic1)} samples = {len(mic1)/SR:.1f}s")

print("Extracting MIC2 (Emily)...")
mic2 = extract_mono(MIC2_PATH, SR)
print(f"  {len(mic2)} samples = {len(mic2)/SR:.1f}s")

# Make same length
min_len = min(len(mic1), len(mic2))
mic1 = mic1[:min_len]
mic2 = mic2[:min_len]

# ============================================================
# STEP 2: Compute energy per window
# ============================================================
window_samples = int(SR * WINDOW_MS / 1000)
n_windows = min_len // window_samples

print(f"\nAnalyzing {n_windows} windows ({WINDOW_MS}ms each)...")

mic1_energy = np.zeros(n_windows)
mic2_energy = np.zeros(n_windows)

for i in range(n_windows):
    s = i * window_samples
    e = s + window_samples
    mic1_energy[i] = np.sqrt(np.mean(mic1[s:e] ** 2))  # RMS
    mic2_energy[i] = np.sqrt(np.mean(mic2[s:e] ** 2))

# ============================================================
# STEP 3: Classify each window
# ============================================================
# SPEAKER: 'H' = host (Lillani), 'G' = guest (Emily), 'W' = wide/both, 'S' = silence
SILENCE_THRESHOLD = 0.008
DOMINANCE_RATIO = 1.3  # Lowered: catch more speaker changes including soft interjections

speaker = []
for i in range(n_windows):
    e1 = mic1_energy[i]
    e2 = mic2_energy[i]
    
    if e1 < SILENCE_THRESHOLD and e2 < SILENCE_THRESHOLD:
        speaker.append('S')  # Silence
    elif e1 > e2 * DOMINANCE_RATIO:
        speaker.append('H')  # Host (Lillani)
    elif e2 > e1 * DOMINANCE_RATIO:
        speaker.append('G')  # Guest (Emily)
    else:
        speaker.append('W')  # Both/crosstalk → wide

# ============================================================
# STEP 4: Build cut list with editorial rules
# ============================================================
# RULE 1: If someone is talking, SHOW THEM. Even 1-second interjections.
# RULE 2: Silence/crosstalk gets absorbed into the current speaker (don't cut to wide for a breath).
# RULE 3: Only merge consecutive same-speaker micro-segments.

SPEAKER_TO_CAM = {'H': 'V2', 'G': 'V3', 'W': 'V1', 'S': 'V1'}

# Collapse consecutive same-speaker windows into segments
segments = []
current_speaker = speaker[0]
current_start = 0

for i in range(1, n_windows):
    if speaker[i] != current_speaker:
        start_sec = current_start * WINDOW_MS / 1000
        end_sec = i * WINDOW_MS / 1000
        segments.append((current_speaker, start_sec, end_sec))
        current_speaker = speaker[i]
        current_start = i

segments.append((current_speaker, current_start * WINDOW_MS / 1000, n_windows * WINDOW_MS / 1000))
print(f"Raw segments: {len(segments)}")

# EDITORIAL MERGE PASS 1: Absorb short silence/crosstalk into the surrounding speaker
# If silence or crosstalk is < MIN_SILENCE_ABSORB seconds, give it to the previous speaker
merged_pass1 = []
for spk, start, end in segments:
    dur = end - start
    if spk in ('S', 'W') and dur < MIN_SILENCE_ABSORB and merged_pass1:
        # Short silence/crosstalk → absorb into previous speaker's segment
        prev_spk, prev_start, prev_end = merged_pass1[-1]
        merged_pass1[-1] = (prev_spk, prev_start, end)
    else:
        merged_pass1.append((spk, start, end))

# EDITORIAL MERGE PASS 2: Merge consecutive same-speaker segments
# (created by pass 1 absorbing silence between them)
merged_pass2 = []
for spk, start, end in merged_pass1:
    if merged_pass2 and merged_pass2[-1][0] == spk:
        # Same speaker as previous → extend
        prev_spk, prev_start, prev_end = merged_pass2[-1]
        merged_pass2[-1] = (prev_spk, prev_start, end)
    else:
        merged_pass2.append((spk, start, end))

print(f"After pass 2 (same-speaker merge): {len(merged_pass2)} cuts")

# EDITORIAL MERGE PASS 3: Filter out micro-cuts (< MIN_INTERJECTION)
# These are mic bleed or breathing, not real interjections.
# Absorb them into the previous speaker's segment.
merged_pass3 = []
for spk, start, end in merged_pass2:
    dur = end - start
    if dur < MIN_INTERJECTION and merged_pass3:
        # Too short to be a real interjection — absorb into previous
        prev_spk, prev_start, prev_end = merged_pass3[-1]
        merged_pass3[-1] = (prev_spk, prev_start, end)
    else:
        merged_pass3.append((spk, start, end))

print(f"After pass 3 (micro-cut filter): {len(merged_pass3)} cuts")

# EDITORIAL MERGE PASS 4: Detect rapid back-and-forth → use wide
# If 3+ consecutive cuts are all under RAPID_THRESHOLD seconds,
# collapse them into one wide shot (too fast to cut between close-ups)
merged = []
i = 0
while i < len(merged_pass3):
    spk, start, end = merged_pass3[i]
    
    # Look ahead: are the next few cuts all rapid?
    rapid_count = 0
    j = i
    while j < len(merged_pass3) and (merged_pass3[j][2] - merged_pass3[j][1]) < RAPID_THRESHOLD:
        rapid_count += 1
        j += 1
    
    if rapid_count >= 3:
        # Collapse into one wide shot
        merged.append(('W', merged_pass3[i][1], merged_pass3[j-1][2]))
        i = j
    else:
        merged.append((spk, start, end))
        i += 1

print(f"After pass 4 (rapid dialogue → wide): {len(merged)} cuts")

# Final same-speaker merge (rapid dialogue pass may have created adjacent same-speaker)
final_merged = []
for spk, start, end in merged:
    if final_merged and final_merged[-1][0] == spk:
        prev_spk, prev_start, prev_end = final_merged[-1]
        final_merged[-1] = (prev_spk, prev_start, end)
    else:
        final_merged.append((spk, start, end))
merged = final_merged

# Force opening wide
if merged:
    first_spk, first_start, first_end = merged[0]
    if first_end - first_start > OPENING_WIDE_SEC:
        merged[0] = (first_spk, OPENING_WIDE_SEC, first_end)
        merged.insert(0, ('W', 0, OPENING_WIDE_SEC))
    else:
        merged[0] = ('W', first_start, first_end)

print(f"Final cut count: {len(merged)}")

# Print first 30 cuts as preview
print("\n=== CUT LIST PREVIEW (first 30) ===")
for i, (spk, start, end) in enumerate(merged[:30]):
    cam = SPEAKER_TO_CAM[spk]
    label = {'H': 'Lillani', 'G': 'Emily', 'W': 'Wide', 'S': 'Wide'}[spk]
    print(f"  [{start:7.1f}s - {end:7.1f}s] → {cam} ({label}) [{end-start:.1f}s]")

print(f"\n...and {len(merged)-20} more cuts")
print(f"Total cuts: {len(merged)}")

# ============================================================
# STEP 5: Generate single-track Premiere XML
# ============================================================
def sec_to_frames(s):
    return int(round(s * 23.976))

def ffprobe_frames(path):
    r = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path],
        capture_output=True, text=True
    )
    sec = float(r.stdout.strip())
    return sec, int(round(sec * 23.976))

# Build file registry: for each camera track, which source files cover which timeline range
print("\nBuilding file registry...")
file_registry = {}
all_cam_clips = [
    ("V1", WIDE_CLIPS),
    ("V2", HOST_CLIPS),
    ("V3", GUEST_CLIPS),
]

file_id_counter = 0
file_entries = {}  # file_id -> (name, pathurl, dur_frames)

for cam_label, clip_list in all_cam_clips:
    ranges = []
    for folder, name, offset in clip_list:
        path = f"{BASE}/{folder}/{name}"
        dur_sec, dur_frames = ffprobe_frames(path)
        url = "file://localhost" + quote(path)
        
        if offset < 0:
            timeline_start = 0
            source_offset = -offset  # skip into source
            timeline_end = dur_sec + offset  # shorter on timeline
        else:
            timeline_start = offset
            source_offset = 0
            timeline_end = offset + dur_sec
        
        fid = f"file_{file_id_counter}"
        file_entries[fid] = (name, url, dur_frames)
        ranges.append((timeline_start, timeline_end, source_offset, fid, dur_frames))
        file_id_counter += 1
    
    file_registry[cam_label] = ranges

def find_source_file(cam, time_sec):
    """Find which source file covers this time on this camera."""
    for tl_start, tl_end, src_offset, fid, dur_f in file_registry[cam]:
        if tl_start <= time_sec < tl_end:
            # Source in = src_offset + (time_sec - tl_start)
            source_time = src_offset + (time_sec - tl_start)
            return fid, source_time
    return None, None

# Build XML
print("Generating XML...")
seq_dur = sec_to_frames(min_len / SR)

L = []
L.append('<?xml version="1.0" encoding="UTF-8"?>')
L.append('<!DOCTYPE xmeml>')
L.append('<xmeml version="4">')
L.append('  <sequence>')
L.append('    <name>Emily Interview - AI Rough Cut</name>')
L.append(f'    <duration>{seq_dur}</duration>')
L.append('    <rate><timebase>24</timebase><ntsc>TRUE</ntsc></rate>')
L.append('    <media>')
L.append('      <video>')
L.append('        <format><samplecharacteristics>')
L.append('          <rate><timebase>24</timebase><ntsc>TRUE</ntsc></rate>')
L.append('          <width>3840</width><height>2160</height>')
L.append('        </samplecharacteristics></format>')
L.append('        <track>')

# Write file definitions first (collect unique file IDs used)
used_files = set()
clip_counter = 0

for spk, start_sec, end_sec in merged:
    cam = SPEAKER_TO_CAM[spk]
    fid, src_start = find_source_file(cam, start_sec)
    
    if fid is None:
        # Camera doesn't cover this time — fall back to wide
        fid, src_start = find_source_file('V1', start_sec)
    
    if fid is None:
        continue  # Skip if no coverage at all
    
    _, src_end = find_source_file(cam if find_source_file(cam, end_sec - 0.1)[0] else 'V1', end_sec - 0.1)
    if src_end is None:
        src_end = src_start + (end_sec - start_sec)
    
    name, url, dur_f = file_entries[fid]
    
    tl_start_f = sec_to_frames(start_sec)
    tl_end_f = sec_to_frames(end_sec)
    in_f = sec_to_frames(src_start)
    out_f = in_f + (tl_end_f - tl_start_f)
    
    # Clamp out to file duration
    if out_f > dur_f:
        out_f = dur_f
        tl_end_f = tl_start_f + (out_f - in_f)
    
    if tl_end_f <= tl_start_f:
        continue
    
    used_files.add(fid)
    
    L.append(f'          <clipitem id="cut_{clip_counter}">')
    L.append(f'            <name>{name}</name>')
    L.append(f'            <duration>{dur_f}</duration>')
    L.append('            <rate><timebase>24</timebase><ntsc>TRUE</ntsc></rate>')
    L.append(f'            <start>{tl_start_f}</start><end>{tl_end_f}</end>')
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

# Audio tracks
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
    L.append('                <media>')
    L.append('                    <audio><samplecharacteristics><depth>16</depth><samplerate>48000</samplerate></samplecharacteristics><channelcount>2</channelcount></audio>')
    L.append('                </media>')
    L.append('            </file>')
    L.append('          </clipitem>')
    L.append('        </track>')

L.append('      </audio>')
L.append('    </media>')
L.append('  </sequence>')
L.append('</xmeml>')

xml = "\n".join(L)
out_path = f"{BASE}/Emily_ROUGH_CUT.xml"
with open(out_path, "w") as f:
    f.write(xml)

print(f"\nWrote: {out_path}")
print(f"Total edit points: {clip_counter}")
print(f"XML size: {len(xml)} bytes")
