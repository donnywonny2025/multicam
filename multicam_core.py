#!/usr/bin/env python3
"""
Multicam Core Logic
Shared utilities for audio extraction, sync calculation, and XML generation.
"""
import subprocess, numpy as np, os
from urllib.parse import quote

# ============================================================
# TIME & FRAME HELPERS
# ============================================================
def sec_to_frames(sec, fps=23.976):
    if abs(fps - 23.976) < 0.1: tb, ntsc = 24, "TRUE"
    elif abs(fps - 29.97) < 0.1: tb, ntsc = 30, "TRUE"
    elif abs(fps - 30.0) < 0.1: tb, ntsc = 30, "FALSE"
    else: tb, ntsc = int(round(fps)), "FALSE"
    return int(round(sec * fps))

def ffprobe_metadata(path):
    """Returns (duration_s, fps)"""
    r = subprocess.run([
        "ffprobe", "-v", "error", "-select_streams", "v:0", 
        "-show_entries", "format=duration:stream=r_frame_rate", 
        "-of", "csv=p=0", path
    ], capture_output=True, text=True)
    lines = r.stdout.strip().split('\n')
    if len(lines) < 2:
        # Might be audio only
        r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path], capture_output=True, text=True)
        return float(r.stdout.strip()), 23.976
    
    fps_raw = lines[0] # Stream 0 r_frame_rate
    dur_s = float(lines[1]) # Format duration
    if '/' in fps_raw:
        n, d = fps_raw.split('/')
        fps = float(n) / float(d)
    else:
        fps = float(fps_raw)
    return dur_s, fps

# ============================================================
# AUDIO EXTRACTION
# ============================================================
def extract_mono(path, sr=16000, tmp_prefix="multicam"):
    tmp = f"/tmp/_{tmp_prefix}_tmp.raw"
    subprocess.run(["ffmpeg", "-y", "-i", path, "-vn", "-ac", "1", "-ar", str(sr), "-f", "s16le", tmp], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    data = np.fromfile(tmp, dtype=np.int16).astype(np.float32) / 32768.0
    if os.path.exists(tmp):
        os.remove(tmp)
    return data

# ============================================================
# XML GENERATION HELPERS
# ============================================================
def get_xml_header(name, duration_f):
    L = []
    L.append('<?xml version="1.0" encoding="UTF-8"?>')
    L.append('<!DOCTYPE xmeml>')
    L.append('<xmeml version="4">')
    L.append('  <sequence>')
    L.append(f'    <name>{name}</name>')
    L.append(f'    <duration>{duration_f}</duration>')
    L.append('    <rate><timebase>24</timebase><ntsc>TRUE</ntsc></rate>')
    L.append('    <media>')
    L.append('      <video>')
    L.append('        <format><samplecharacteristics>')
    L.append('          <rate><timebase>24</timebase><ntsc>TRUE</ntsc></rate>')
    L.append('          <width>3840</width><height>2160</height>')
    L.append('        </samplecharacteristics></format>')
    return L

def get_xml_footer():
    L = []
    L.append('    </media>')
    L.append('  </sequence>')
    L.append('</xmeml>')
    return L

def generate_audio_tracks(mic_configs):
    """
    mic_configs: list of (name, path)
    """
    L = []
    L.append('      <audio>')
    L.append('        <numchannels>2</numchannels>')
    L.append('        <format><samplecharacteristics><depth>16</depth><samplerate>48000</samplerate></samplecharacteristics></format>')
    
    for mic_idx, (m_id, m_path) in enumerate(mic_configs):
        m_dur_s, _ = ffprobe_metadata(m_path)
        m_dur_f = sec_to_frames(m_dur_s, 23.976) # Timeline default
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
    return L
