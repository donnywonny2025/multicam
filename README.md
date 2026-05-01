# AI Multicam Editor — Emily Project Manual

This repository contains the full "Software 2.0" framework for the Emily interview series. It uses a combination of audio wave-energy and transcript intelligence to generate a high-end, 3-track Premiere Pro multicam edit.

## 📁 Project Architecture & Multi-Episode Support
While the original framework was built for the Emily interview, it has been successfully generalized and adapted into a scalable 3-track architecture. The framework now natively supports:

1. **Emily Episode** (2-track hybrid)
2. **Sonya Hollins Episode** (3-track discrete: Wide, Host, Guest)
3. **Leilani's Friends Episode** (3-track discrete with Multi-Guest indexing)

### 1. The 3-Track Mapping Standard
*   **V1 (Wide)**: Usually `Cam 1` (e.g. C9124, C9119)
*   **V2 (Host)**: Usually `Cam 2`
*   **V3 (Guest(s))**: Usually `Cam 3`
*   **Audio**: Energy-based dominance tracking mapped to `MIC1.WAV` (Host) and `MIC2.WAV` (Guest/Friends).

### 2. Architecture
*   **multicam_core.py**: The "Engine." Contains the logic for audio extraction, frame calculations, and the Premiere XML structure. **Do not modify this unless you want to change the foundational sync engine.**
*   **autocut_intelligent.py (v3)**: The "Gold Master." 172 clever cuts. Great for professional, steady pacing.
*   **autocut_dynamic.py (v5)**: The "High Energy" cut. 349 cuts. Includes reaction padding (laughs) and name-mention triggers.

## 🧠 The Tech Stack (How it Works)
This system follows a "Signal-to-Story" pipeline across four layers:

1.  **The "Ears" (Waveform Sync)**: Using **FFT Cross-Correlation** (`xcorr_fast.py`). It listens to the actual sound waves to compute frame-accurate offsets between all cameras and the master mic. This is the "Anchor."
2.  **The "Brain" (Transcription)**: Using **Whisper AI** (`full_master_transcribe.py`). It transcribes the master audio to get word-level timestamps. This provides the "Meaning" (questions, names, laughs).
3.  **The "Editor" (Intelligence Fusion)**: Using the **Python v3/v5 Logic**. It fuses the sync offsets with the transcript data. It chooses the camera based on energy, but uses the transcript to override for professional touches (anticipatory cuts, reaction padding).
4.  **The "Output" (XMEML Assembly)**: Using **XMEML v4**. It writes a map for Premiere Pro telling it exactly where to cut and which clips to enable, while keeping the timeline 100% non-destructive.

## 🚀 How to Run
1.  **Sync**: Ensure all offsets are calculated via `xcorr_fast.py`.
2.  **Transcribe**: Use `full_master_transcribe.py` to generate the `.json` context.
3.  **Generate XML**: Run `python3 autocut_dynamic.py`.
4.  **Import**: Drag the resulting `.xml` into Premiere Pro.

## 🛠 Moving to a New Project (e.g., Cancer Survivors)
To bring this intelligence to a new project:
1.  **Copy this folder** to the new project.
2.  **Calculate New Offsets**: Run the FFT sync on the new files.
3.  **Update Config**: Edit the `BASE`, `AUDIO_BASE`, and `CLIPS` mappings in the `autocut_*.py` scripts.
4.  **Codified Safety**: Because the audio logic is moved to `multicam_core.py`, you can change the project filenames without breaking the track structures.

**Project Lead**: Gemini 2.0 (DeepMind)
**User/Director**: DonnyWonny
**State**: Production Ready
