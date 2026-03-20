#!/usr/bin/env python3
"""
FFT-based audio cross-correlation for precise sync offsets.
Uses numpy for instant results instead of slow sample-by-sample.
"""
import subprocess, numpy as np, os

def extract_audio_np(path, start_sec, dur_sec):
    """Extract audio as numpy array via ffmpeg."""
    tmp = "/tmp/_xcorr_tmp.raw"
    subprocess.run([
        "ffmpeg", "-y", "-ss", str(start_sec), "-i", path,
        "-t", str(dur_sec), "-vn", "-ac", "1", "-ar", "16000",
        "-f", "s16le", tmp
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    data = np.fromfile(tmp, dtype=np.int16).astype(np.float32) / 32768.0
    os.remove(tmp)
    return data

def find_offset(reference, target):
    """FFT cross-correlation. Returns lag in samples."""
    # Zero-pad to same length
    n = len(reference) + len(target) - 1
    fft_size = 1
    while fft_size < n:
        fft_size *= 2
    
    ref_fft = np.fft.rfft(reference, fft_size)
    tgt_fft = np.fft.rfft(target, fft_size)
    
    # Cross-correlation via conjugate multiply
    xcorr = np.fft.irfft(ref_fft * np.conj(tgt_fft))
    
    # Find peak
    peak = np.argmax(xcorr)
    
    # Wrap around: if peak > half the FFT size, it's a negative lag
    if peak > fft_size // 2:
        peak -= fft_size
    
    return peak

SR = 16000
BASE = "/Volumes/WORK 2TB/WORK 2026/SANDBOX/Emily"
MIC1 = "/Volumes/WORK 2TB/WORK 2026/SANDBOX/Audio Organized/Nurse Interview Session (Feb 17)/MIC1.WAV"

# === START CLIPS: Compare first 20s against MIC1 at 0s ===
print("Extracting MIC1 reference (0-20s)...")
ref = extract_audio_np(MIC1, 0, 20)

start_clips = [
    ("Cam 1", "C9124.MP4"),
    ("Cam 2", "C0003.MP4"),
    ("Cam 3", "C0001.MP4"),
]

print("\n=== START CLIPS (vs MIC1 at 0s) ===")
offsets = {}
for folder, name in start_clips:
    path = f"{BASE}/{folder}/{name}"
    target = extract_audio_np(path, 0, 30)
    
    lag = find_offset(ref, target)
    lag_sec = lag / SR
    
    offsets[f"{folder}/{name}"] = lag_sec
    print(f"  {folder}/{name}: lag={lag} samples = {lag_sec:.4f}s")
    print(f"    → Offset: {lag_sec:.4f}s (camera started {abs(lag_sec):.3f}s {'before' if lag_sec > 0 else 'after'} master)")

# === SECOND-HALF CLIPS: Compare against MIC1 at approximate position ===
# For these, we search around the approximate position
second_clips = [
    ("Cam 2", "C0004.MP4", 1790),
    ("Cam 3", "C0002.MP4", 1800),
]

print("\n=== SECOND-HALF CLIPS ===")
for folder, name, approx in second_clips:
    path = f"{BASE}/{folder}/{name}"
    
    # Extract 20s of MIC1 around the approximate offset
    ref2 = extract_audio_np(MIC1, approx, 20)
    target = extract_audio_np(path, 0, 30)
    
    lag = find_offset(ref2, target)
    lag_sec = lag / SR
    
    true_offset = approx + lag_sec
    offsets[f"{folder}/{name}"] = true_offset
    print(f"  {folder}/{name}: lag from {approx}s = {lag_sec:.4f}s")
    print(f"    → True offset: {true_offset:.4f}s")

print("\n=== FINAL OFFSET TABLE ===")
for k, v in offsets.items():
    print(f"  {k}: {v:.4f}s")
