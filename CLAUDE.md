# Innerdance Biofeedback POC — Claude Code Context

This file is read by Claude Code to understand the project. It is the single source of truth for contributors.

---

## What this project is

A research proof-of-concept that uses HRV (heart rate variability) data from a Polar H10 chest strap to study how the **innerdance** sound technique regulates the autonomic nervous system. The goal is to generate physiological evidence for research funding.

**Innerdance** is a facilitated or self-administered sound practice that co-stimulates the sympathetic (SNS) and parasympathetic (PNS) nervous systems in sequence — it is a training for **autonomic flexibility / stress resilience**, not just relaxation.

**Current state:** 6 participants have completed sessions (Dec 2025). One participant (P1, 14.12.2025) has been analysed. The data pipeline and analysis scripts are working. The system architecture has been designed; implementation of the V1 web platform has not started.

---

## Repository structure

```
innerdance-biofeedback-poc/
├── CLAUDE.md                        ← YOU ARE HERE — read first
├── README.md                        ← Human-readable overview and setup
├── .gitignore                       ← Excludes data, audio, PDFs, generated outputs
├── requirements.txt                 ← Python dependencies
│
├── docs/                            ← All documentation and research artefacts
│   ├── README.md                    ← Index of docs
│   ├── architecture.md             ← V1 + conceptual system architecture (Mermaid)
│   ├── RESEARCH_JOURNAL.md         ← Consolidated research journal (start here for context)
│   └── research/                   ← Iteration documents (step1–step5)
│       ├── README.md
│       ├── step1_metrics_hypothesis.md
│       ├── step2_metrics_hypothesis_v2.md   ← Most complete: literature + ML approaches
│       ├── step3_sequence_models.md          ← Sequence model technical reference
│       ├── step4_pragmatic_approach.md       ← Two-stream pivot
│       └── step5_refined_approach.md         ← FINAL: resilience framing + protocol
│
├── data/                            ← Participant data — GITIGNORED (health data)
│   └── README.md                    ← Data schema, format, upload instructions (committed)
│
├── analysis/                        ← Exploratory and hypothesis-testing scripts
│   ├── README.md
│   ├── 01_stage_hrv_analysis.py     ← Stage-level HRV analysis, H1 + H5 tests
│   └── 02_audio_rr_feature_map.py  ← Audio + RR alignment and feature visualisation
│
├── processing/                      ← Data pipeline scripts (HRV + acoustic features)
│   ├── README.md
│   ├── hrv_processor.py             ← Pre/post + in-session HRV windows → Supabase
│   └── acoustic_processor.py        ← Acoustic feature extraction → Supabase
│
├── app/                             ← React participant app (Phase 1 — not yet built)
│   ├── README.md
│   └── upload_app.py                ← Participant upload form
│
├── notebooks/                       ← Jupyter workspace for AI engineers
│   └── README.md
│
└── database/                        ← Database schema
    ├── README.md
    └── schema.sql                   ← Supabase Postgres table definitions
```

---

## Key technical decisions (do not change without discussion)

### Platform: Supabase + React + Metabase
- **Supabase** (managed Postgres): storage for RR CSV files, session metadata, processed features. Auto REST API via PostgREST. Non-experts use Supabase Studio to browse/query data.
- **React app** (`app/`): participant-facing UI — playlist playback, `playlist_start_utc` logging, self-report form, R-R CSV upload. Owned by the frontend developer. Deploys to Vercel/Netlify. See ADR 3 in `docs/architecture_decision_records.md`.
- **Metabase**: non-expert dashboards connecting directly to Supabase Postgres.
- See `docs/architecture.md` for the full V1 diagram.

### HRV metrics — CRITICAL timing constraint
- **RMSSD is only valid in pre/post 5-min resting windows** (controlled breathing). Do NOT compute RMSSD during sessions where participants breathe slowly (AJP-Regu 2022, doi:10.1152/ajpregu.00272.2022).
- **During-session signals**: use HF power (0.15–0.40 Hz) and RSA amplitude.
- Pre/post windows: `window_type = 'pre'` or `'post'` in `hrv_windows` table.
- In-session windows: `window_type = 'in_session'`, 30-sec duration, 50% overlap.

### Acoustic feature extraction
- Tool: `librosa` + `surfboard`
- Window: 30-second sliding windows, 50% overlap
- Features: tempo (BPM), bass RMS (20–250 Hz), AM rate (Hilbert envelope), spectral centroid, ZCR, onset density, silence ratio, HNR
- Target sample rate: 4 Hz (both HRV and acoustic windows aligned to `window_start_ts`)

### Temporal alignment
- Participant claps 3 times before starting audio. Clap appears as artefact in both R-R data and audio waveform. Compute offset from this shared event.
- All windows joined by `(session_id, window_ts)` — this is the primary key for the feature dataset.

### ML phase sequence (do not skip ahead)
| Phase | Approach | Trigger |
|---|---|---|
| 0 (now) | Threshold rule: RMSSD vs personal baseline | No data needed |
| 1 (weeks 1–4) | Within-person OLS: acoustic → RMSSD per participant | 5+ sessions/person |
| 2 (weeks 2–14) | Bayesian hierarchical (PyMC/bambi) | All participants data in |
| 3 (month 3+) | Contextual bandit (vowpalwabbit) | ~30 action-reward cycles |
| 4 (month 6+) | GAN bidirectional | ≥200 sessions |

---

## Data formats

### Polar H10 raw ECG export (`polar_ecg`)
Columns: `time [ns], ecg, hr, rr [ms], marker`
The `rr` column has the R-R interval in ms on rows where an R-peak was detected (NaN otherwise). Nanosecond timestamps from session start.

### Polar Beat app export (`polar_beat`)
Columns: `Phone timestamp, RR-interval [ms]`

### Stage timestamps file
CSV with columns: `stage, start_sec, label`
`start_sec` = seconds from session start (when stage transitions in the audio).

### Self-report JSON (always this schema — never change mid-study)
```json
{
  "pre_stress": 0-10,
  "post_stress": 0-10,
  "pre_energy": 0-10,
  "post_energy": 0-10,
  "sleep_quality_last_night": 1-5,
  "notable_events": "free text, optional"
}
```

### Session metadata JSON
```json
{
  "start_time_utc": "ISO 8601",
  "duration_min": 60,
  "sync_offset_sec": 4.2,
  "session_type": "innerdance | passive_rest | activating_music",
  "audio_source": "spotify_link | filename"
}
```

---

## The 12 innerdance stages (physiological map)

| Stage | Name | Brainwave | Expected HRV |
|---|---|---|---|
| Pre | Baseline | — | Personal RMSSD anchor |
| 1 | Befriedigung / Satisfaction | Delta | First PNS response ↑ |
| 2 | Unzufriedenheit / Dissatisfaction | Theta | Slight dip |
| 3 | Die Schwelle / Threshold | θ→α/β | Neutral |
| **4** | **Freisetzung / Release** | **Alpha/Beta** | **SNS peak — RMSSD dip ↓** |
| 5 | Desintegration | Delta | Holding |
| 6–7 | Erwachen / Erleuchtung | θ/α → α/β | Recovery begins |
| 8–9 | Wahl / Verstärkung | α/θ, Mu | Secondary energy |
| **10** | **Dunkle Nacht / Dark Night** | **Delta** | **PNS rebound — RMSSD peak ↑** |
| 11 | Einheit / Unity | θ/α | Heart coherence |
| 12 | Re-Integration | δ/α | Return to consciousness |

Stage 4 dip → Stage 10 peak is the **resilience arc** — the primary pattern to detect.

---

## Participants (current data)

| Participant | Date | Sample file | Sessions analysed |
|---|---|---|---|
| P1 | 14.12.2025 | `data/sample/P1_2025-12-14_session01.csv` | YES — see `RESEARCH_JOURNAL.md` |
| P2 | 26.12.2025 | *(not committed — health data)* | Timestamps available |
| P3 | 26.12.2025 | *(not committed — health data)* | Timestamps available |
| P4 | 13.12.2025 | *(not committed — health data)* | No stage timestamps |
| P5 | 10.12.2025 | *(not committed — health data)* | First 5 stages only |
| P6 | 19.12.2025 | *(not committed — health data)* | Last stages only |

Timestamps for P1 are in `data/sample/P1_2025-12-14_timestamps.json`. Timestamp reference documents for P2 and P3 are in the original data folder as `.docx` files (not committed).

---

## How to add and analyse a new session

1. Add the session CSV file to `data/` (gitignored — do not commit participant data).
2. Create a stage timestamps CSV (see format above).
3. Open `analysis/01_stage_hrv_analysis.py` and add an entry to the `SESSIONS` list at the top.
4. Run: `python analysis/01_stage_hrv_analysis.py`
5. Figures are saved to `outputs/figures/` (gitignored).
6. To add audio analysis: open `analysis/02_audio_rr_feature_map.py` and update the paths.

---

## Contribution conventions

- Branch naming: `feature/<short-description>` or `fix/<short-description>`
- One PR per feature; include what hypothesis or architecture component it addresses
- Do not commit participant data files, audio files, or PDFs — they are gitignored
- Do not change the self-report JSON schema mid-study — all analyses depend on it
- Add a `README.md` to every new folder you create
- If you add a new Python script, add it to `requirements.txt` if it introduces a new dependency
