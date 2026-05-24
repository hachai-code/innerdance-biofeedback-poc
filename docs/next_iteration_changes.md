# Next Iteration — Proposed Changes

Changes agreed in design session (2026-05-24). Not yet implemented.

---

## 1. Sync protocol — replace 3-clap with UI-logged timestamp

**Current:** Participant claps 3 times before starting audio. Clap appears as spike in Polar data and audio waveform. `sync_offset_sec` is computed manually from this shared event.

**Problem:** Pre-recorded playlists played from the UI make the clap protocol unnecessary — the UI knows exactly when the playlist started.

**Change:**
- Remove `sync_offset_sec` from the session metadata schema
- Add `playlist_start_utc` (ISO 8601) logged automatically by the UI at the moment playback begins
- Polar data already carries UTC timestamps — alignment is `polar_ts - playlist_start_utc`
- Screenshot at playlist start kept as a manual backup (cheap redundancy)
- Clock drift between UI device and Polar is typically <1 s over 60 min — acceptable

**Files to update:**
- `docs/data_collection_protocol.md` — remove clap sync section, add UI timestamp section
- `database/schema.sql` — replace `sync_offset_sec float` with `playlist_start_utc timestamptz` in `sessions` table
- `CLAUDE.md` — update sync protocol description
- `data/sample/P1_2025-12-14_timestamps.json` — rename to `P1_2025-12-14_metadata.json`, replace `sync_offset_sec` field

---

## 2. Playlist catalog — pre-compute acoustic features once per playlist

**Context:** Sessions use a managed set of playlists (not one fixed playlist, not arbitrary user-chosen audio). The UI plays from this set and records which playlist was used.

**Change:** Add a `playlists/` folder to the repo containing:

```
playlists/
├── catalog.json                        ← playlist registry
├── PL001_acoustic_features.csv         ← pre-computed once per playlist
├── PL002_acoustic_features.csv
└── ...
```

**`catalog.json` schema:**
```json
[
  {
    "id": "PL001",
    "name": "12 Stages — Dec 2025 cohort",
    "duration_sec": 3480,
    "file": "sound/12 stages tracks/...",
    "description": "Standard 12-stage innerdance sequence used in Dec 2025 sessions"
  }
]
```

**`PLxxx_acoustic_features.csv` schema:**
```
time_sec, rms_energy, bass_energy, spec_centroid_hz, am_depth, onset_strength, onset_cv
0.0, 0.14, 0.12, 985.3, 0.38, 0.95, 0.58
15.0, ...
```
Window: 30 s, step: 15 s (50% overlap).

**New script:** `analysis/00_precompute_playlist_features.py`
- Takes a playlist `id` from `catalog.json`
- Concatenates the constituent audio files in order
- Extracts sliding-window acoustic features (same 6 features as current pipeline)
- Writes `playlists/PLxxx_acoustic_features.csv`
- Run once when a new playlist is added; never re-run unless the playlist changes

**Updated session metadata schema:**
```json
{
  "playlist_id": "PL001",
  "playlist_start_utc": "2025-12-14T13:07:00Z",
  "session_type": "innerdance",
  "polar_format": "polar_ecg"
}
```

**Files to update:**
- `database/schema.sql` — add `playlists` table; update `sessions` to use `playlist_id` FK + `playlist_start_utc`
- `analysis/README.md` — document `00_precompute_playlist_features.py`
- `CLAUDE.md` — update acoustic feature extraction section

---

## 3. Stage timestamps — demote from required to optional annotation

**Current:** Stage timestamps are described as required for per-stage HRV analysis, and their absence limits analysis to whole-session metrics.

**Change:** Stage timestamps remain useful for labelling and visualisation but the primary analysis pipeline no longer depends on them.

**Rationale:**
- Sliding-window analysis across the full session gives ~120 data points per session vs ~9 stage summaries
- Because the playlist is from a fixed catalog with known structure, stage boundaries can be inferred from the acoustic feature time series (e.g., Stage 4 = window with highest bass energy)
- Cross-participant averaging at the playlist time axis is more informative than stage-level summaries

**What stage timestamps still enable:**
- Labels on the HRV timeline for interpretability and stakeholder presentations
- Validation that the acoustic-inferred stage boundaries match the intended ones
- The existing qualitative model report (`03_qualitative_model_report.py`) which uses stage summaries

**Files to update:**
- `docs/data_collection_protocol.md` — move stage timestamps from "required" to "optional annotation"
- `analysis/README.md` — clarify that `01_stage_hrv_analysis.py` is for exploration; primary pipeline uses `03_qualitative_model_report.py`

---

## 4. Primary analysis — sliding window across full session

**Current:** Analysis summarises HRV per stage (~9 windows per session).

**Change:** Primary analysis uses 30-second sliding windows (15-second step) across the full session, joined to the pre-computed playlist acoustic features at each time point.

**What this enables:**

| | Per-stage (current) | Sliding window (proposed) |
|---|---|---|
| Data points per session | ~9 | ~120 |
| Requires stage timestamps | Yes | No |
| Cross-participant averaging | Coarse | Time-aligned (same axis) |
| Detects HRV response lag | No | Yes (~30–60 s measurable) |
| ML feature rows per participant | ~9 | ~120 |

**Cross-playlist analysis:** Because all sessions record `playlist_id`, you can:
- Average HRV at each time point across all sessions using `PL001` → characteristic response curve
- Compare `PL001` vs `PL002` arcs → which playlist produces a stronger resilience arc?
- Per-participant × per-playlist analysis → does P1 respond differently to different playlists?

**New `feature_dataset` view logic:**
```sql
-- HRV window joined to playlist acoustic features at matching time point
SELECT
  s.id AS session_id,
  s.participant_id,
  s.playlist_id,
  h.window_ts,
  EXTRACT(EPOCH FROM (h.window_ts - s.playlist_start_utc)) AS t_sec,
  h.rmssd, h.sd2, h.dfa_a1, h.mean_hr,
  p.rms_energy, p.bass_energy, p.spec_centroid_hz,
  p.am_depth, p.onset_strength, p.onset_cv
FROM hrv_windows h
JOIN sessions s ON s.id = h.session_id
JOIN playlist_acoustic_features p
  ON p.playlist_id = s.playlist_id
  AND ABS(p.time_sec - EXTRACT(EPOCH FROM (h.window_ts - s.playlist_start_utc))) < 7.5
```

---

## Summary of schema changes

### `sessions` table (delta only)

| Column | Change |
|---|---|
| `sync_offset_sec float` | Remove |
| `audio_source text` | Remove |
| `playlist_id text` | Add — FK to `playlists.id` |
| `playlist_start_utc timestamptz` | Add |

### New `playlists` table

```sql
CREATE TABLE playlists (
  id            text PRIMARY KEY,           -- e.g. 'PL001'
  name          text NOT NULL,
  duration_sec  integer,
  description   text,
  created_at    timestamptz DEFAULT now()
);
```

### New `playlist_acoustic_features` table

```sql
CREATE TABLE playlist_acoustic_features (
  playlist_id       text REFERENCES playlists(id),
  time_sec          float,                  -- window centre, seconds from playlist start
  rms_energy        float,
  bass_energy       float,
  spec_centroid_hz  float,
  am_depth          float,
  onset_strength    float,
  onset_cv          float,
  PRIMARY KEY (playlist_id, time_sec)
);
```
