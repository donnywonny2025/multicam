import sys, os
import numpy as np
import librosa

def find_offset(reference, target, sr=16000):
    n = len(reference) + len(target) - 1
    fft_size = 1
    while fft_size < n: fft_size *= 2
    ref_fft = np.fft.rfft(reference, fft_size)
    tgt_fft = np.fft.rfft(target, fft_size)
    xcorr = np.fft.irfft(ref_fft * np.conj(tgt_fft))
    peak = np.argmax(xcorr)
    if peak > fft_size // 2: peak -= fft_size
    return peak

def main():
    BASE = "/Volumes/WORK 2TB/WORK 2026/SANDBOX/Leilani's Friends"
    MIC1_PATH = "/Volumes/WORK 2TB/WORK 2026/SANDBOX/Audio Organized/_Session_Library/2026_0216_0628/MIC1.WAV"
    MIC2_PATH = "/Volumes/WORK 2TB/WORK 2026/SANDBOX/Audio Organized/_Session_Library/2026_0216_0628/MIC2.WAV"
    
    print("Loading MIC1 and MIC2...")
    mic1, _ = librosa.load(MIC1_PATH, sr=16000, mono=True)
    mic2, _ = librosa.load(MIC2_PATH, sr=16000, mono=True)
    
    # Mix them to ensure we catch both speakers
    min_len = min(len(mic1), len(mic2))
    mic = (mic1[:min_len] + mic2[:min_len]) / 2.0
    
    files = [
        ("Cam 1", "C9119.MP4"),
        ("Cam 2", "C0001.MP4"),
        ("Cam 3", "C0002.MP4")
    ]
    
    results = []
    for folder, name in files:
        print(f"Processing {folder}/{name}...")
        path = f"{BASE}/{folder}/{name}"
        try:
            cam, _ = librosa.load(path, sr=16000, mono=True)
            peak = find_offset(mic, cam, 16000)
            offset_sec = peak / 16000.0
            print(f"  {name}: {offset_sec:.4f}s")
            results.append((folder, name, offset_sec))
        except Exception as e:
            print(f"  {name}: ERROR {e}")
            
    with open("ALL_OFFSETS.txt", "w") as f:
        for folder, name, off in results:
            f.write(f"{folder},{name},{off:.4f}\n")

if __name__ == "__main__":
    main()
