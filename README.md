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
