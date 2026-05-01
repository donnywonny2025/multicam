import numpy as np
from scipy.io import wavfile

# Load a snippet from MIC2.WAV (Guest) around 1300 seconds
fs, data = wavfile.read('/Volumes/WORK 2TB/WORK 2026/SANDBOX/Audio Organized/Nurse Interview Session (Feb 17)/MIC2.WAV')

print("Loaded audio. Sample rate:", fs)
if len(data.shape) > 1:
    data = data[:, 0]  # Take left channel

start_s = 1300.0
end_s = 1305.0
start_i = int(start_s * fs)
end_i = int(end_s * fs)

chunk = data[start_i:end_i]

# Compute moving average RMS to find where the speech starts
window_size = int(fs * 0.05) # 50ms
rms = []
for i in range(0, len(chunk), window_size):
    window = chunk[i:i+window_size]
    # watch out for int16 overflow
    val = np.sqrt(np.mean(window.astype(np.float32)**2))
    rms.append(val)

# Find first point where RMS > threshold
# Let's print out the peaks
print("RMS values (every 50ms):")
for idx, r in enumerate(rms):
    time_offset = idx * 0.05
    if r > 500:  # arbitrary threshold
        print(f"[{start_s + time_offset:.2f}s] RMS: {r:.1f} ***")
    else:
        print(f"[{start_s + time_offset:.2f}s] RMS: {r:.1f}")

