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
def sec_to_frames(sec):
    return int(round(sec * 23.976))

def ffprobe_frames(path):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path], capture_output=True, text=True)
    sec = float(r.stdout.strip())
    return sec, int(round(sec * 23.976))

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
    return L
