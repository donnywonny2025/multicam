import numpy as np

def snap_in_fixed(mic_data, fs, w_start, threshold=500):
    # Just look slightly before the whisper mark (say 0.3s) and find the first
    # time it breaks threshold. If it never does, return w_start.
    start_i = max(0, int((w_start - 0.3) * fs))
    end_i = int((w_start + 0.3) * fs)
    chunk = mic_data[start_i:end_i]
    window_size = int(fs * 0.02)
    step = int(fs * 0.01)
    
    rms_vals = []
    for i in range(0, len(chunk) - window_size, step):
        window = chunk[i:i+window_size]
        rms = np.sqrt(np.mean(window.astype(np.float32)**2))
        rms_vals.append(rms)
        
    actual = w_start
    for i, rms in enumerate(rms_vals):
        if rms > threshold:
            # We found the first spike!
            actual = (start_i + i * step) / fs
            break
            
    return actual - 0.02 # Tiny safety buffer

def snap_out_fixed(mic_data, fs, w_end, threshold=500):
    start_i = max(0, int((w_end - 0.3) * fs))
    end_i = int((w_end + 0.8) * fs) # look further ahead for trails
    chunk = mic_data[start_i:end_i]
    window_size = int(fs * 0.02)
    step = int(fs * 0.01)
    
    rms_vals = []
    for i in range(0, len(chunk) - window_size, step):
        window = chunk[i:i+window_size]
        rms = np.sqrt(np.mean(window.astype(np.float32)**2))
        rms_vals.append(rms)
        
    actual = w_end
    
    # Starting from w_end, find when it drops below threshold
    start_search_idx = int(0.3 * fs / step)
    for i in range(start_search_idx, len(rms_vals)):
        if rms_vals[i] < threshold:
            actual = (start_i + i * step) / fs
            break
            
    return actual + 0.05
