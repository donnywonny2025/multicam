#!/usr/bin/env python3
"""
Final 3-track multicam XML with WAVEFORM-CORRECTED offsets.
Uses the same structure that already imports successfully.
"""
import subprocess
from urllib.parse import quote

def ffprobe_frames(path):
    r = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path],
        capture_output=True, text=True
    )
    sec = float(r.stdout.strip())
    return sec, int(round(sec * 23.976))

def sec_to_frames(s):
    return int(round(s * 23.976))

BASE = "/Volumes/WORK 2TB/WORK 2026/SANDBOX/Emily"
AUDIO_BASE = "/Volumes/WORK 2TB/WORK 2026/SANDBOX/Audio Organized/Nurse Interview Session (Feb 17)"

# WAVEFORM-CORRECTED OFFSETS (from FFT cross-correlation)
tracks = [
    ("Wide - Cam 1", [
        ("Cam 1", "C9124.MP4", -9.0102),
    ]),
    ("CU1 - Cam 2", [
        ("Cam 2", "C0003.MP4", -4.5544),
        ("Cam 2", "C0004.MP4", 1792.3358),
    ]),
    ("CU2 - Cam 3", [
        ("Cam 3", "C0001.MP4", -2.2166),
        ("Cam 3", "C0002.MP4", 1800.4341),
    ]),
]

audio_files = [
    ("MIC1.WAV", f"{AUDIO_BASE}/MIC1.WAV"),
    ("MIC2.WAV", f"{AUDIO_BASE}/MIC2.WAV"),
]

# Get real durations
print("Reading durations...")
clip_info = {}
for label, clip_list in tracks:
    for folder, name, offset in clip_list:
        path = f"{BASE}/{folder}/{name}"
        dur_sec, dur_frames = ffprobe_frames(path)
        clip_info[f"{folder}/{name}"] = (dur_sec, dur_frames)
        print(f"  {folder}/{name}: {dur_sec:.2f}s = {dur_frames}f, offset={offset:.4f}s")

mic_info = {}
for mic_name, mic_path in audio_files:
    dur_sec, dur_frames = ffprobe_frames(mic_path)
    mic_info[mic_name] = (dur_sec, dur_frames)

# Sequence duration
seq_frames = 0
for label, clip_list in tracks:
    for folder, name, offset in clip_list:
        _, dur_f = clip_info[f"{folder}/{name}"]
        end = sec_to_frames(max(0, offset)) + dur_f
        seq_frames = max(seq_frames, end)
for mn in mic_info:
    seq_frames = max(seq_frames, mic_info[mn][1])

# Build XML
fc = 0
L = []
L.append('<?xml version="1.0" encoding="UTF-8"?>')
L.append('<!DOCTYPE xmeml>')
L.append('<xmeml version="4">')
L.append('  <sequence>')
L.append('    <name>Emily Interview - Multicam</name>')
L.append(f'    <duration>{seq_frames}</duration>')
L.append('    <rate><timebase>24</timebase><ntsc>TRUE</ntsc></rate>')
L.append('    <media>')
L.append('      <video>')
L.append('        <format><samplecharacteristics>')
L.append('          <rate><timebase>24</timebase><ntsc>TRUE</ntsc></rate>')
L.append('          <width>3840</width><height>2160</height>')
L.append('        </samplecharacteristics></format>')

for label, clip_list in tracks:
    L.append('        <track>')
    for folder, name, offset in clip_list:
        _, dur_f = clip_info[f"{folder}/{name}"]
        
        if offset < 0:
            start_f = 0
            in_f = sec_to_frames(-offset)
            out_f = dur_f
            end_f = dur_f - in_f
        else:
            start_f = sec_to_frames(offset)
            in_f = 0
            out_f = dur_f
            end_f = start_f + dur_f
        
        url = "file://localhost" + quote(f"{BASE}/{folder}/{name}")
        
        L.append(f'          <clipitem id="clip_{fc}">')
        L.append(f'            <name>{name}</name>')
        L.append(f'            <duration>{dur_f}</duration>')
        L.append('            <rate><timebase>24</timebase><ntsc>TRUE</ntsc></rate>')
        L.append(f'            <start>{start_f}</start><end>{end_f}</end>')
        L.append(f'            <in>{in_f}</in><out>{out_f}</out>')
        L.append(f'            <file id="file_{fc}">')
        L.append(f'                <name>{name}</name>')
        L.append(f'                <pathurl>{url}</pathurl>')
        L.append('                <media>')
        L.append('                    <video><samplecharacteristics><width>3840</width><height>2160</height></samplecharacteristics></video>')
        L.append('                    <audio><samplecharacteristics><depth>16</depth><samplerate>48000</samplerate></samplecharacteristics><channelcount>2</channelcount></audio>')
        L.append('                </media>')
        L.append('            </file>')
        L.append('          </clipitem>')
        fc += 1
    L.append('        </track>')

L.append('      </video>')
L.append('      <audio>')
L.append('        <numchannels>2</numchannels>')
L.append('        <format><samplecharacteristics><depth>16</depth><samplerate>48000</samplerate></samplecharacteristics></format>')

for mic_name, mic_path in audio_files:
    _, mic_frames = mic_info[mic_name]
    url = "file://localhost" + quote(mic_path)
    L.append('        <track>')
    L.append(f'          <clipitem id="clip_{fc}">')
    L.append(f'            <name>{mic_name}</name>')
    L.append(f'            <duration>{mic_frames}</duration>')
    L.append('            <rate><timebase>24</timebase><ntsc>TRUE</ntsc></rate>')
    L.append(f'            <start>0</start><end>{mic_frames}</end>')
    L.append(f'            <in>0</in><out>{mic_frames}</out>')
    L.append(f'            <file id="file_{fc}">')
    L.append(f'                <name>{mic_name}</name>')
    L.append(f'                <pathurl>{url}</pathurl>')
    L.append('                <media>')
    L.append('                    <audio><samplecharacteristics><depth>16</depth><samplerate>48000</samplerate></samplecharacteristics><channelcount>2</channelcount></audio>')
    L.append('                </media>')
    L.append('            </file>')
    L.append('          </clipitem>')
    fc += 1
    L.append('        </track>')

L.append('      </audio>')
L.append('    </media>')
L.append('  </sequence>')
L.append('</xmeml>')

xml = "\n".join(L)
out_path = f"{BASE}/Emily_MULTICAM.xml"
with open(out_path, "w") as f:
    f.write(xml)
print(f"\nWrote: {out_path}")

# Pre-flight
print("\n=== PRE-FLIGHT ===")
import xml.etree.ElementTree as ET
tree = ET.parse(out_path)
for ci in tree.getroot().iter('clipitem'):
    n = ci.find('name').text
    d = int(ci.find('duration').text)
    i = int(ci.find('in').text)
    o = int(ci.find('out').text)
    s = int(ci.find('start').text)
    e = int(ci.find('end').text)
    ok = o <= d and i >= 0 and (e-s) == (o-i)
    print(f"  {n:12s} {'✅' if ok else '❌'} dur={d} in={i} out={o} start={s} end={e}")
