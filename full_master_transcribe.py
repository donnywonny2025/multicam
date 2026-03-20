import whisper, torch, json, os

# Throttled to 4 cores for M2 system comfort
torch.set_num_threads(4)
model = whisper.load_model("base.en", device="cpu")

def transcribe_full(path, name):
    print(f"Starting FULL Master Transcription for {name}...")
    tmp_wav = f"/tmp/{name}_16k.wav"
    import subprocess
    cmd = ["ffmpeg", "-y", "-i", path, "-vn", "-ac", "1", "-ar", "16000", tmp_wav]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    # word_timestamps=True allows for exact camera alignment later
    result = model.transcribe(tmp_wav, word_timestamps=True, fp16=False)
    
    out_json = f"/Volumes/WORK 2TB/WORK 2026/SANDBOX/Emily/Master_{name}_Transcript.json"
    with open(out_json, "w") as f:
        json.dump(result, f, indent=4)
    print(f"✅ Saved Master {name} Transcript to {out_json}")

mic1 = "/Volumes/WORK 2TB/WORK 2026/SANDBOX/Audio Organized/Nurse Interview Session (Feb 17)/MIC1.WAV"
mic2 = "/Volumes/WORK 2TB/WORK 2026/SANDBOX/Audio Organized/Nurse Interview Session (Feb 17)/MIC2.WAV"

transcribe_full(mic1, "MIC1")
transcribe_full(mic2, "MIC2")

print("\n--- ALL MASTER TRANSCRIPTIONS COMPLETE ---")
