import stable_whisper
import torch
import json
import os
import time

os.environ["PATH"] += os.pathsep + "/opt/homebrew/bin"

# Limit core usage so we don't melt the M2
torch.set_num_threads(4)

print("Loading stable-ts model (base.en) onto CPU...")
t0 = time.time()
model = stable_whisper.load_model("base.en", device="cpu")
print(f"Model loaded in {time.time() - t0:.2f}s")

def transcribe_precision(path, name):
    print(f"\n==============================================")
    print(f"Starting PRECISION Transcription for {name}...")
    print(f"==============================================")
    tmp_wav = f"/tmp/{name}_16k_precision.wav"
    import subprocess
    cmd = ["/opt/homebrew/bin/ffmpeg", "-y", "-i", path, "-vn", "-ac", "1", "-ar", "16000", tmp_wav]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    t1 = time.time()
    # word_timestamps=True is natively implied in stable-ts, but we keep the whisper standard API
    # Stable-ts aligns using DTW and silero VAD natively.
    result = model.transcribe(tmp_wav, fp16=False)
    
    out_json = f"/Volumes/WORK 2TB/WORK 2026/SANDBOX/Emily/Master_{name}_Precision_Transcript.json"
    
    result.save_as_json(out_json)
    
    print(f"✅ Saved Precision {name} Transcript to {out_json}")
    print(f"Time taken for {name}: {time.time() - t1:.2f}s")


mic1 = "/Volumes/WORK 2TB/WORK 2026/SANDBOX/Audio Organized/Nurse Interview Session (Feb 17)/MIC1.WAV"
mic2 = "/Volumes/WORK 2TB/WORK 2026/SANDBOX/Audio Organized/Nurse Interview Session (Feb 17)/MIC2.WAV"

transcribe_precision(mic1, "MIC1")
transcribe_precision(mic2, "MIC2")

print("\n--- ALL PRECISION TRANSCRIPTIONS COMPLETE ---")
