# Architecture Decision Records

---

## ADR 1 — Platform: Supabase

### Decision

Use **Supabase** as the core platform (Postgres + file storage + auto REST API).

### Reasoning

| Need | Why Supabase wins |
|---|---|
| Non-experts upload & browse data | Supabase Studio has a spreadsheet-style table editor and SQL console — no CLI needed |
| File storage (RR CSVs) | Built-in S3-compatible Storage bucket, linked directly to Postgres rows |
| Auto REST API | PostgREST generates a REST endpoint for every table the moment you create it — zero code |
| Dashboards | Connects directly to Metabase (free, drag-and-drop) or Grafana via the Postgres wire protocol |
| LLM / ML extension | `supabase-py` client works in any Jupyter notebook; pgvector extension for embeddings already bundled |
| Maintenance burden | Fully managed cloud, free tier covers the POC, upgrades are one click |
| Self-hostable later | Open source, Docker-composable — no vendor lock-in for a future grant/institution setup |

### V1 stack

**Supabase + React + Metabase**

- **Supabase** is the core: Postgres + file storage + auto REST API + Studio (spreadsheet-style UI that works for non-experts without SQL). Free tier covers the POC. Open source and self-hostable later.
- **React app** for the participant-facing UI — upload form, playlist playback with `playlist_start_utc` logging, self-report. Owned and built by the frontend developer. Deploy to Vercel or Netlify (free tier, push to GitHub → auto-deploy).
- **Metabase** connects to Supabase Postgres in one step and gives non-experts drag-and-drop dashboards.

### Processing trigger (V1)

The simplest approach: a Python script (`process_sessions.py`) that polls `sessions WHERE processed_at IS NULL`. An AI engineer runs it manually or sets up a GitHub Actions cron later. No serverless, no webhooks on day one.

### Key design principle

The `feature_dataset` view is the single handoff point between data engineering and ML work. AI engineers query it with one line of pandas, and every ML phase (0 → 4) reads from the same place without any schema changes.

Extension points (MLflow, LLM connector, pgvector, contextual bandit) require no architecture change — they read from the existing REST API or view and write back into it.

---

## ADR 2 — Acoustic Feature Extraction: Python Package Selection

### Decision

Use **librosa + surfboard + torchaudio** as the acoustic feature extraction stack. All three have commercial-compatible licenses.

### Package evaluation

#### Tier 1 — Core feature extraction

| Package | License | GitHub Stars | Best for |
|---|---|---|---|
| librosa | MIT | ~7k | Gold standard: MFCCs, spectral centroid, chroma, onset, tempo, beat |
| torchaudio | BSD-2 | ~2.5k | PyTorch-native transforms, spectrograms, mel filterbanks, deep feature extraction |
| pyAudioAnalysis | Apache 2.0 | ~5.5k | Higher-level: feature extraction + classification pipelines, HMM/SVM built-in |

#### Tier 2 — Specialised / psychoacoustic

| Package | License | GitHub Stars | Best for |
|---|---|---|---|
| surfboard | MIT | ~300 | Acoustic features designed explicitly for biosignal and health ML — rhythm, energy, shimmer, jitter |
| openl3 | MIT | ~500 | Deep audio embeddings via pretrained networks; good when handcrafted features underfit |
| essentia | AGPL-3 ⚠️ | ~2.8k | 200+ descriptors including psychoacoustic: loudness, dissonance, roughness, tonality — requires paid commercial licence for closed use |

### Features most relevant to biofeedback modelling

For HRV/physiological response to sound, prioritise:

- **Psychoacoustic:** loudness (LUFS), spectral roughness, dissonance, brightness — librosa + custom computation, or essentia
- **Temporal/rhythmic:** tempo, beat strength, onset density, pulse clarity — `librosa.beat_track`, `librosa.onset.onset_strength`
- **Spectral:** MFCC (timbre), spectral flux (change rate), spectral centroid (perceived brightness)
- **Energy dynamics:** RMS envelope, attack/release shapes

### Recommended stack (commercially safe)

```python
librosa          # spectral + rhythmic features
torchaudio       # efficient transforms + pretrained encoders
surfboard        # psychoacoustic + health-domain features
scikit-learn     # regression/classification on extracted features
```

If the full psychoacoustic suite (roughness, dissonance, tonality) is required, **essentia** is the most complete option — but requires either a commercial licence or keeping the codebase open-source under AGPL.

---

## ADR 3 — Frontend: React (replacing Streamlit)

### Decision

Use **React** for the participant-facing web app instead of Streamlit.

### Context

The initial design specified Streamlit Community Cloud as the upload form, chosen for its fast Python-only setup. The team has a frontend developer with React experience, making a proper React app the better fit.

### Reasoning

| Need | Why React wins over Streamlit |
|---|---|
| Participant experience | React supports custom UI, playlist playback controls, and responsive mobile layout — Streamlit is form-only and visually constrained |
| Playlist playback with timestamp | React `Audio` API can log `playlist_start_utc` precisely at playback start — this is not easily done in Streamlit |
| Frontend developer owns it | The team has React expertise; Streamlit would require the React developer to work outside their stack |
| Supabase integration | `@supabase/supabase-js` is a first-class client library — file upload, auth, and REST calls are idiomatic in React |
| Future mobile app path | A React web app can be wrapped with Capacitor for a native mobile app without rewriting — Streamlit cannot |
| Deployment | Vercel / Netlify free tier: push to GitHub → auto-deploy; same operational simplicity as Streamlit Community Cloud |

### What changes

- `app/` folder becomes a React project (`package.json`, `src/`, etc.) instead of a Python script
- `streamlit` removed from `requirements.txt` (Python requirements are now analysis/processing only)
- The Supabase JS client (`@supabase/supabase-js`) handles all database writes from the frontend

### What stays the same

- Supabase remains the backend (same schema, same REST API)
- Metabase remains for non-expert dashboards
- The Python processing pipeline (`hrv_processor.py`, `acoustic_processor.py`) is backend-only and unaffected
