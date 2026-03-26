# AI Multicam Editor — Emily Project Manual

This repository contains the full "Software 2.0" framework for the Emily interview series. It uses a combination of audio wave-energy and transcript intelligence to generate a high-end, 3-track Premiere Pro multicam edit.

## 📁 The Emily "Formula" (Current Settings)
If you ever need to reset or resume this specific project, these are the hardcoded constants:

### 1. File Mappings
*   **V1 (Wide)**: `C9124.MP4` (Offset: -9.0102s)
*   **V2 (Host - Lillani)**: `C0003.MP4` (-4.5544s) / `C0004.MP4` (1792.33s)
*   **V3 (Guest - Emily)**: `C0001.MP4` (-2.2166s) / `C0002.MP4` (1800.43s)
*   **Audio**: `MIC1.WAV` (Lillani) / `MIC2.WAV` (Emily)

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
