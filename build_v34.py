with open('/Volumes/WORK 2TB/WORK 2026/SANDBOX/Emily/sync_scripts/autocut_v33_hook.py', 'r') as f:
    code = f.read()

new_snaps = """def snap_in(mic_data, fs, w_start, threshold=700):
    start_i = max(0, int((w_start - 0.4) * fs))
    end_i = int((w_start + 0.4) * fs)
    chunk = mic_data[start_i:end_i]
    window_size = int(fs * 0.02)
    step = int(fs * 0.01)
    
    rms_vals = []
    for i in range(0, len(chunk) - window_size, step):
        window = chunk[i:i+window_size]
        rms = np.sqrt(np.mean(window.astype(np.float32)**2))
        rms_vals.append(rms)
        
    actual = w_start
    # Just find the FIRST time the RMS breaks the threshold in the zone
    for i, rms in enumerate(rms_vals):
        if rms > threshold:
            actual = (start_i + i * step) / fs
            break
            
    return actual - 0.03 # Tiny safety pad

def snap_out(mic_data, fs, w_end, threshold=500):
    start_i = max(0, int((w_end - 0.2) * fs))
    end_i = int((w_end + 0.8) * fs)
    chunk = mic_data[start_i:end_i]
    window_size = int(fs * 0.02)
    step = int(fs * 0.01)
    
    rms_vals = []
    for i in range(0, len(chunk) - window_size, step):
        window = chunk[i:i+window_size]
        rms = np.sqrt(np.mean(window.astype(np.float32)**2))
        rms_vals.append(rms)
        
    actual = w_end
    start_search_idx = int(0.2 * fs / step)
    for i in range(start_search_idx, len(rms_vals)):
        if rms_vals[i] < threshold:
            actual = (start_i + i * step) / fs
            break
            
    return actual + 0.08
"""

import re
code = re.sub(r'def snap_in\(.*?(?=def get_active_mic)', new_snaps, code, flags=re.DOTALL)
code = code.replace('v33', 'v34')
code = code.replace('Transient Snap', 'Transient Corrected')

with open('/Volumes/WORK 2TB/WORK 2026/SANDBOX/Emily/sync_scripts/autocut_v34_hook.py', 'w') as f:
    f.write(code)
