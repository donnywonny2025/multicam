# AI Video Editor Agent — Technical Reference

## What This Is
An LLM agent with domain-specific tools for video editing, where the LLM handles high-level editorial reasoning and the tools handle low-level media manipulation.

---

## System Architecture

### Layer 1: Tools (Mechanical)
The scripts that extract data and generate output. No intelligence — just reliable execution.

| Tool | Purpose |
|---|---|
| `ffprobe` | Get exact clip durations, frame counts, metadata |
| `ffmpeg` | Extract audio, convert formats |
| `numpy` FFT cross-correlation | Find precise sync offsets between camera and master audio |
| `numpy` RMS energy analysis | Compute waveform loudness per 250ms window |
| XML generator | Write Premiere Pro XMEML v4 files |

### Layer 2: Data (What the AI Knows)
All the information the AI has access to for making editorial decisions.

| Data Source | What It Provides |
|---|---|
| **Master transcript** | Every word spoken, timestamped to the millisecond |
| **MIC1 waveform** | When Lillani (host) is talking, how loud, silence gaps |
| **MIC2 waveform** | When Emily (guest) is talking, how loud, silence gaps |
| **Camera assignments** | V1=Wide (both), V2=Lillani CU, V3=Emily CU |
| **Sync offsets** | Exact frame-accurate alignment between all files |
| **Speaker identity** | MIC1=Lillani (host), MIC2=Emily Ellis/Nurse Silly (guest) |
| **Content understanding** | Story topics, questions, answers, humor, transitions |

> [!IMPORTANT]
> This is **more data than a human editor** typically has on a first pass. A human would need to watch all 45 minutes to absorb what the AI already knows from the transcript in seconds.

### Layer 3: Intelligence (Editorial Reasoning)
The LLM reads all the data and makes contextual editorial decisions. This is the gap between "mechanical cutting" and "editing."

**What the mechanical layer does:** If MIC1 is louder → show Lillani. Pure math.

**What the intelligence layer does:** Reads the transcript and understands:
- "Lillani just asked a question → cut to Emily *before* she answers (anticipatory cut)"
- "Emily is telling a personal story about correctional nursing → stay on her, don't cut away"
- "They're both laughing → go wide to show the chemistry"
- "Topic is changing from Nurse Silly to nursing career → use wide as a visual reset"
- "Emily said something short ('oh you got multiple today') → cut to her for that line, then back"

---

## Data Correlation: "Seeing Without Seeing"

The AI can't watch the footage, but it can make visual editing decisions because:
1. **Transcript** → knows what's being said (the screenplay)
2. **Waveform energy** → knows who's talking and how intensely
3. **Speaker identity** → knows whose close-up to show
4. **Content context** → knows the story beats, humor, emotion
5. **Pacing data** → knows where natural pauses and transitions occur

For a talking-head podcast, this covers ~95% of editing decisions. The only thing missing is facial expressions and eye contact — and that's the 5% the human editor handles in the polish pass.

---

## Output Versions

| Version | Type | Tracks | Description |
|---|---|---|---|
| **v1** | Multicam Sync | 3V + 2A | Full uncut tracks, synced. For manual editing. |
| **v2** | Rough Cut | 1V + 2A | Auto-cut on single track. Good for preview, limited control. |
| **v3** | Intelligent Cut | 3V + 2A | All three tracks cut at same edit points. AI picks the active angle. Editor can override any cut. **This is the target.** |

### v3 Concept (3-Track Intelligent Cut)
- All three camera tracks are sliced at every edit point
- The AI's recommended angle is the "active" one at each cut
- The other two angles are right there on their tracks at the same position
- Editor can swap angles at any cut point by grabbing from another track
- **AI does the first pass, human does the polish**

This matches how a professional editor actually works in Premiere: three tracks, all synced, cutting between them. The AI just automates finding the 164+ cut points.

---

## Editorial Rules

### Always
- **If someone is talking, show them** — even 1-second interjections
- **Cut on sentence/phrase boundaries** — never mid-word
- **Open on wide** — establish the scene for 3-5 seconds

### Smart Cuts
- **Question → cut to answerer** before they start speaking (anticipatory cut)
- **Reaction moments** — hold on the listener for 2-3 seconds when something funny/surprising
- **Long stories** — stay on the storyteller, don't cut away
- **Topic transitions** → go to wide for a visual "reset"

### Avoid
- **Rapid-fire switching** — if back-and-forth is too fast (3+ cuts under 3s each), use the wide
- **Cutting for mic bleed** — sub-1-second energy spikes are noise, not speech
- **Staying on one angle too long** (40+ seconds) — vary the visual rhythm

---

## Sync Pipeline (Foundation)

### FFT Cross-Correlation (How Sync Works)
Compares raw audio waveforms between each camera's scratch audio and the master mic:
```python
xcorr = np.fft.irfft(np.fft.rfft(reference, n) * np.conj(np.fft.rfft(target, n)))
peak = np.argmax(xcorr)  # lag in samples
offset_seconds = peak / sample_rate
```

> [!CAUTION]
> **Do NOT use Whisper word timestamps for sync.** They drift up to 0.8s on noisy audio. Always use waveform cross-correlation.

### Verified Sync Offsets
| Clip | Duration | Offset | Track |
|---|---|---|---|
| Cam 1/C9124.MP4 | 2717.72s | -9.0102s | V1 (Wide) |
| Cam 2/C0003.MP4 | 1790.29s | -4.5544s | V2 (Lillani CU) |
| Cam 2/C0004.MP4 | 929.43s | 1792.3358s | V2 (Lillani CU) |
| Cam 3/C0001.MP4 | 1790.79s | -2.2166s | V3 (Emily CU) |
| Cam 3/C0002.MP4 | 915.41s | 1800.4341s | V3 (Emily CU) |

---

## Premiere XML Requirements

| Requirement | Value |
|---|---|
| Version | `<xmeml version="4">` |
| DOCTYPE | `<!DOCTYPE xmeml>` — **must be present** |
| File URIs | `file://localhost/Volumes/...` |
| Spaces/specials | URL-encoded (`%20`, `%28`, `%29`) |
| Clip durations | **Must match ffprobe** |
| `<out>` value | **Must NOT exceed `<duration>`** |
| Frame rate | `<timebase>24</timebase><ntsc>TRUE</ntsc>` |
| Sample rate | `48000` for all audio |
| Frame math | `frames = int(round(seconds * 23.976))` |

> [!CAUTION]
> The #1 cause of "File Import Failure" is `<out>` exceeding the clip's real frame count.

---

## Scripts & Files

### Working Scripts (saved in project)
| Script | Location |
|---|---|
| FFT sync finder | `Emily/sync_scripts/xcorr_fast.py` |
| XML generator | `Emily/sync_scripts/gen_multicam_v2.py` |
| Auto-cut engine | `Emily/sync_scripts/autocut.py` |
| Master transcription | `Emily/sync_scripts/full_master_transcribe.py` |
| Editing rules | `Emily/sync_scripts/editing_rules.md` |

### Media Locations
- Camera clips: `/Volumes/WORK 2TB/WORK 2026/SANDBOX/Emily/Cam {1,2,3}/`
- Master audio: `.../Audio Organized/Nurse Interview Session (Feb 17)/`
- Master transcript: `Emily/Master_MIC1_Transcript.json`
- Generated XMLs: `Emily/Emily_v{N}_*.xml`

### People
| Name | Role | Camera | Mic |
|---|---|---|---|
| Lillani | Host | V2 (CU left) | A1 / MIC1 |
| Emily Ellis (Nurse Silly) | Guest | V3 (CU right) | A2 / MIC2 |
| Daryl | Camera operator | — | — |

### Dependencies
- `ffmpeg` / `ffprobe`, `numpy`, `python3`
- `whisper` (for content identification only, not sync)
