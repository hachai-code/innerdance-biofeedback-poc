# processing/

Data pipeline scripts that transform raw Polar H10 CSV files and audio into the `hrv_windows` and `acoustic_windows` tables in Supabase.

---

## Scripts

| Script | Input | Output | Status |
|---|---|---|---|
| `hrv_processor.py` | R-R CSV from Supabase Storage | `hrv_windows` rows in Supabase | Not yet built |
| `acoustic_processor.py` | Playlist URL or audio file path | `acoustic_windows` rows in Supabase | Not yet built |

---

## How the pipeline runs (Phase 0 / V1)

The pipeline is triggered manually or by a cron job:

```bash
python processing/hrv_processor.py
python processing/acoustic_processor.py
```

Both scripts poll `sessions WHERE processed_at IS NULL`, process each session, and write results back.

---

## HRV processing logic

### Pre/post windows (RMSSD valid)
- Window type: `'pre'` or `'post'`
- Duration: 5 minutes of resting data before/after the session
- Metrics computed: RMSSD, Mean HR, SD1

### In-session windows (RMSSD NOT valid during slow breathing)
- Window type: `'in_session'`
- Duration: 30 seconds, 50% overlap
- Metrics computed: HF power (0.15–0.40 Hz), RSA amplitude, Mean HR
- Reference: AJP-Regu 2022 (doi:10.1152/ajpregu.00272.2022) — RMSSD is invalid during slow deep breathing typical of innerdance sessions

### Dependencies
- `neurokit2` — HRV metrics
- `pyhrv` — alternative HRV library
- `scipy` — signal processing

---

## Acoustic processing logic

### Feature extraction
- Window: 30-second sliding windows, 50% overlap
- Sample rate alignment: 4 Hz (matching HRV windows)
- Features extracted per window:

| Feature | Method | Literature grounding |
|---|---|---|
| Tempo (BPM) | `librosa.beat.tempo` | ≤60 BPM → parasympathetic ↑ |
| Bass RMS (20–250 Hz) | `librosa.feature.rms` (filtered) | Ventral vagal effect |
| AM rate | Hilbert envelope | Brain.fm phase-locking (Woods 2024) |
| Spectral centroid | `librosa.feature.spectral_centroid` | Brightness / arousal |
| ZCR | `librosa.feature.zero_crossing_rate` | Roughness proxy |
| Onset density | `librosa.onset.onset_detect` | Event rate |
| Silence ratio | RMS threshold | Active regulatory tool |
| HNR | `librosa.effects.harmonic` | Consonance / social engagement |

### Audio source
- Spotify API for metadata and 30-sec previews
- `yt-dlp` as fallback for full audio (check licensing before use)
- If participant uploaded audio file: read directly from Supabase Storage

---

## Temporal alignment

Both HRV and acoustic windows use `window_start_ts` (UTC timestamp) as the join key. The 3-clap sync protocol establishes the offset between R-R recording start and audio start.

The `feature_dataset` view in Supabase joins `hrv_windows ⋈ acoustic_windows` on `(session_id, window_ts)`.
