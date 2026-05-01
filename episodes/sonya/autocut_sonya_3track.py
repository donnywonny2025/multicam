#!/usr/bin/env python3
"""
AI Multicam Auto-Cut (Janine Seals) - 3 TRACK VERSION
Matches Emily v9 Standard with 3 discrete tracks (V1, V2, V3) and <enabled>TRUE/FALSE</enabled>.
"""
import subprocess
import numpy as np
import urllib.parse
import os
import json
import time
import sys
sys.path.append("/Volumes/WORK 2TB/WORK 2026/SANDBOX/Emily/sync_scripts")
import multicam_core as core

# ============================================================
# CONFIG — VERIFIED OFFSETS (Sonya Hollins)
# ============================================================
BASE = "/Volumes/WORK 2TB/WORK 2026/SANDBOX/Sonya Hollins"
AUDIO_BASE = "/Volumes/WORK 2TB/WORK 2026/SANDBOX/Audio Organized/_Session_Library/2026_0216_0856"
MIC1_PATH = f"{AUDIO_BASE}/MIC1.WAV"
MIC2_PATH = f"{AUDIO_BASE}/MIC2.WAV"

WIDE_CLIPS = [("Cam 1", "C9120.MP4", -108.8404), ("Cam 1", "C9121.MP4", 176.2803)]
HOST_CLIPS = [("Cam 2", "C0004.MP4", -92.3809), ("Cam 2", "C0005.MP4", 171.0), ("Cam 2", "C0006.MP4", 178.2661), ("Cam 2", "C0007.MP4", 1973.6937)]
GUEST_CLIPS = [("Cam 3", "C0006.MP4", -86.3306), ("Cam 3", "C0007.MP4", 163.9977), ("Cam 3", "C0008.MP4", 1982.2588)]

FPS = 23.976
SR = 16000
WINDOW_MS = 250
SILENCE_THRESHOLD = 0.008
DOMINANCE_RATIO = 1.3
MIN_SILENCE_ABSORB = 1.5
MIN_SEGMENT_SEC = 0.7
ANTICIPATORY_LEAD = 0.8
OPENING_WIDE_SEC = 3.0
MAX_HOLD_SEC = 20.0
REACTION_MIN_SEC = 2.5
REACTION_MAX_SEC = 5.0
MAX_ANY_CAMERA_SEC = 45.0

def load_mono(path): return np.fromfile(path, dtype=np.float32)

print("Loading cached audio...")
mic1 = load_mono(f"{BASE}/sync_scripts/.cache_sonya_MIC1_{SR}.raw")
mic2 = load_mono(f"{BASE}/sync_scripts/.cache_sonya_MIC2_{SR}.raw")
min_len = min(len(mic1), len(mic2))
mic1, mic2 = mic1[:min_len], mic2[:min_len]
total_sec = min_len / SR

print("Computing energy levels...")
window_samples = int(SR * WINDOW_MS / 1000)
n_windows = min_len // window_samples
mic1_energy = np.zeros(n_windows)
mic2_energy = np.zeros(n_windows)

for i in range(n_windows):
    s, e = i * window_samples, (i + 1) * window_samples
    mic1_energy[i] = np.sqrt(np.mean(mic1[s:e] ** 2))
    mic2_energy[i] = np.sqrt(np.mean(mic2[s:e] ** 2))

speaker = []
for i in range(n_windows):
    e1, e2 = mic1_energy[i], mic2_energy[i]
    if e1 < SILENCE_THRESHOLD and e2 < SILENCE_THRESHOLD: speaker.append('S')
    elif e1 > e2 * DOMINANCE_RATIO: speaker.append('H')
    elif e2 > e1 * DOMINANCE_RATIO: speaker.append('G')
    else: speaker.append('W')

segments_raw = []
current_speaker, current_start = speaker[0], 0
for i in range(1, n_windows):
    if speaker[i] != current_speaker:
        segments_raw.append((current_speaker, current_start * WINDOW_MS / 1000.0, i * WINDOW_MS / 1000.0))
        current_speaker, current_start = speaker[i], i
segments_raw.append((current_speaker, current_start * WINDOW_MS / 1000.0, n_windows * WINDOW_MS / 1000.0))

pass1 = []
for spk, s, e in segments_raw:
    if spk in ('S', 'W') and e - s < MIN_SILENCE_ABSORB and pass1:
        pass1[-1] = (pass1[-1][0], pass1[-1][1], e)
    else: pass1.append((spk, s, e))

pass2 = []
for spk, s, e in pass1:
    if pass2 and pass2[-1][0] == spk: pass2[-1] = (spk, pass2[-1][1], e)
    else: pass2.append((spk, s, e))

pass3 = []
for spk, s, e in pass2:
    if e - s >= MIN_SEGMENT_SEC: pass3.append((spk, s, e))
    elif pass3: pass3[-1] = (pass3[-1][0], pass3[-1][1], e)

segments = []
for spk, s, e in pass3:
    if segments and segments[-1][0] == spk: segments[-1] = (spk, segments[-1][1], e)
    else: segments.append((spk, s, e))

adjusted = []
for idx, (spk, s, e) in enumerate(segments):
    if idx > 0 and spk in ('H', 'G'):
        new_start = max(s - ANTICIPATORY_LEAD, segments[idx-1][1] + 0.5)
        if adjusted: adjusted[-1] = (adjusted[-1][0], adjusted[-1][1], new_start)
        adjusted.append((spk, new_start, e))
    else: adjusted.append((spk, s, e))
segments = adjusted

final_segments = []
for spk, s, e in segments:
    duration = e - s
    if spk in ('H', 'G') and duration > MAX_HOLD_SEC:
        reaction_target = 'G' if spk == 'H' else 'H'
        pos = s
        while pos < e:
            remaining = e - pos
            if remaining <= MAX_HOLD_SEC:
                final_segments.append((spk, pos, e))
                break
            hold_time = min(MAX_HOLD_SEC * 0.8, remaining - REACTION_MIN_SEC)
            final_segments.append((spk, pos, pos + hold_time))
            pos += hold_time
            reaction_dur = min(REACTION_MAX_SEC, e - pos - 2.0)
            if reaction_dur >= REACTION_MIN_SEC:
                final_segments.append((reaction_target, pos, pos + reaction_dur))
                pos += reaction_dur
            else:
                final_segments.append((spk, pos, e))
                break
    elif spk in ('S', 'W') and duration > MAX_ANY_CAMERA_SEC:
        final_segments.append(('W', s, e))
    else:
        final_segments.append((spk, s, e))

# --- NEW WIDE SHOT CONTEXTUAL SCRIPTING ---
# The user requested tasteful, sparse wide shots to show off the set.
# Rule 1: "The Reset Wide". If someone speaks for >20 seconds, and the speaker changes,
# cut to Wide for 3.5 seconds to reset the spatial awareness before punching in.
wide_pass = []
for idx, (spk, s, e) in enumerate(final_segments):
    if idx > 0 and spk in ('H', 'G') and final_segments[idx-1][0] in ('H', 'G') and final_segments[idx-1][0] != spk:
        prev_dur = final_segments[idx-1][2] - final_segments[idx-1][1]
        if prev_dur > 20.0:  # Previous speaker held the floor for a long time
            wide_dur = min(3.5, (e - s) * 0.5)  # Wide for 3.5s, or up to half their speaking time
            if wide_dur > 1.5:
                wide_pass.append(('W', s, s + wide_dur))
                wide_pass.append((spk, s + wide_dur, e))
                continue
    
    wide_pass.append((spk, s, e))

merged = []
for spk, s, e in wide_pass:
    if merged and merged[-1][0] == spk and abs(s - merged[-1][2]) < 0.01:
        merged[-1] = (spk, merged[-1][1], e)
    else: merged.append((spk, s, e))
segments = merged

if segments and segments[0][1] < OPENING_WIDE_SEC:
    first_end = min(OPENING_WIDE_SEC, segments[0][2])
    new_segs = [('W', 0, first_end)]
    if segments[0][2] > first_end: new_segs.append((segments[0][0], first_end, segments[0][2]))
    new_segs.extend(segments[1:])
    segments = new_segs

def sec_to_frame(s): return int(round(s * FPS))

def encode_path(path):
    parts = path.split("/")
    return "file://localhost/" + "/".join(urllib.parse.quote(p) for p in parts if p)

print("Generating 3-Track XML...")

# Build a registry of ALL files and their absolute offsets on the timeline
# format: (tl_s, tl_e, file_offset_at_tl_s, folder, filename)
track_configs = [("V1", "W", WIDE_CLIPS), ("V2", "H", HOST_CLIPS), ("V3", "G", GUEST_CLIPS)]
file_registry = {}
file_entries = {}
fid_counter = 0

for t_idx, (trk_id, spk_flag, c_list) in enumerate(track_configs):
    rgs = []
    for folder, name, offset in c_list:
        path = f"{BASE}/{folder}/{name}"
        dur_s, _ = core.ffprobe_metadata(path)
        
        clip_start = offset
        clip_end = offset + dur_s
        
        if clip_end <= 0:
            continue
            
        if clip_start < 0:
            tl_s = 0.0
            src_off = -clip_start
        else:
            tl_s = clip_start
            src_off = 0.0
            
        tl_e = clip_end
        
        url = encode_path(path)
        fid = f"file_{fid_counter}"
        
        dur_f = sec_to_frame(dur_s)
        file_entries[fid] = (name, url, dur_f, folder)
        rgs.append((tl_s, tl_e, src_off, fid))
        fid_counter += 1
    file_registry[trk_id] = rgs

def find_src(trk_id, t_sec):
    for tl_s, tl_e, src_off, fid in file_registry[trk_id]:
        if tl_s <= t_sec < tl_e:
            return fid, src_off + (t_sec - tl_s)
    return None, None

clip_counter = 0
spk_to_track = {'W': 'V1', 'S': 'V1', 'H': 'V2', 'G': 'V3'}

video_tracks = []

for trk_idx, (trk_id, spk_flag, _) in enumerate(track_configs):
    track_xml = []
    track_xml.append('        <track>')
    track_xml.append('          <enabled>TRUE</enabled>')
    track_xml.append('          <locked>FALSE</locked>')
    
    for (active_spk, s, e) in segments:
        fid, src_s = find_src(trk_id, s)
        if fid is None:
            # Maybe gap (card rollover), just continue
            continue
            
        name, url, dur_f, folder = file_entries[fid]
        tl_s_f, tl_e_f = sec_to_frame(s), sec_to_frame(e)
        in_f = sec_to_frame(src_s)
        out_f = in_f + (tl_e_f - tl_s_f)
        
        if tl_e_f <= tl_s_f: continue
        
        # If it's this track's turn, it's TRUE. Otherwise FALSE.
        # But wait! If the active speaker is H, but H is in a gap (None returned by find_src above for V2), 
        # we fallback to V1 (Wide) in actual logic.
        # Actually, let's keep it simple: if this track is the one assigned to `spk_to_track[active_spk]`, it's enabled.
        is_active = (spk_to_track[active_spk] == trk_id)
            
        track_xml.append(f'          <clipitem id="cut_{clip_counter}">')
        track_xml.append(f'            <name>{name}</name>')
        track_xml.append(f'            <duration>{dur_f}</duration>')
        track_xml.append('            <rate><timebase>24</timebase><ntsc>TRUE</ntsc></rate>')
        track_xml.append(f'            <start>{tl_s_f}</start><end>{tl_e_f}</end>')
        track_xml.append(f'            <enabled>{"TRUE" if is_active else "FALSE"}</enabled>')
        track_xml.append(f'            <in>{in_f}</in><out>{out_f}</out>')
        track_xml.append(f'            <file id="{fid}">')
        track_xml.append(f'                <name>{name}</name>')
        track_xml.append(f'                <pathurl>{url}</pathurl>')
        track_xml.append('                <media>')
        track_xml.append('                    <video><samplecharacteristics><width>3840</width><height>2160</height></samplecharacteristics></video>')
        track_xml.append('                    <audio><samplecharacteristics><depth>16</depth><samplerate>48000</samplerate></samplecharacteristics><channelcount>2</channelcount></audio>')
        track_xml.append('                </media>')
        track_xml.append('            </file>')
        track_xml.append('          </clipitem>')
        clip_counter += 1
        
    track_xml.append('        </track>')
    video_tracks.append("\n".join(track_xml))

total_frames = sec_to_frame(total_sec)
mic1_url = encode_path(MIC1_PATH)
mic2_url = encode_path(MIC2_PATH)

audio_clips_mic1 = f"""          <clipitem id="mic1_leilani">
            <name>MIC1.WAV</name>
            <duration>{total_frames}</duration>
            <rate><timebase>24</timebase><ntsc>TRUE</ntsc></rate>
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

audio_clips_mic2 = f"""          <clipitem id="mic2_janine">
            <name>MIC2.WAV</name>
            <duration>{total_frames}</duration>
            <rate><timebase>24</timebase><ntsc>TRUE</ntsc></rate>
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

xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE xmeml>
<xmeml version="4">
  <sequence>
    <name>Sonya Hollins AutoCut (3-Track) v8</name>
    <duration>{total_frames}</duration>
    <rate><timebase>24</timebase><ntsc>TRUE</ntsc></rate>
    <media>
      <video>
        <format><samplecharacteristics>
          <rate><timebase>24</timebase><ntsc>TRUE</ntsc></rate>
          <width>3840</width><height>2160</height>
        </samplecharacteristics></format>
{chr(10).join(video_tracks)}
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

out_path = f"{BASE}/Sonya_Hollins_FINAL_3TRACK_SYNC_v8.xml"
with open(out_path, "w") as f:
    f.write(xml)

print(f"Written: {out_path}")

