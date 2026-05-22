# Innerdance AI — Architecture

---

## V1 Implementation Architecture

```mermaid
flowchart TD

    subgraph PART["Participants  —  no technical setup required"]
        UP(["Open URL in browser\nupload RR CSV · fill form · paste Spotify link"])
    end

    subgraph STREAMLIT["Streamlit Upload App  —  Streamlit Community Cloud  free"]
        FORM["Session form\nparticipant ID · date · PSS-3 · energy · sleep · playlist URL"]
        UPLOADER["RR file uploader\nvalidate CSV columns on submit"]
    end

    subgraph SB["Supabase  —  managed Postgres + Storage  free tier"]
        direction TB
        BUCKET[("Storage Bucket\nraw RR CSV files\npath: rr/{session_id}.csv")]

        subgraph TABLES["Postgres Tables  —  browseable in Supabase Studio"]
            T_PART[("participants\nid · name · email\ndemographics jsonb")]
            T_SESS[("sessions\nid · participant_id · date\nplaylist_url · form_data jsonb\nrr_file_path · processed_at")]
            T_HRV[("hrv_windows\nsession_id · window_ts · window_type\nrmssd · mean_hr · sd1\nhf_power · rsa_amplitude")]
            T_ACO[("acoustic_windows\nsession_id · window_ts\ntempo · bass_rms · am_rate\ncentroid · zcr · onset_density\nsilence_ratio · hnr")]
            T_VIEW[("feature_dataset  ★  SQL VIEW\nhrv_windows ⋈ acoustic_windows\nby session_id + window_ts\n— query this for all ML work —")]
        end

        SB_API["Auto REST API  PostgREST\nsupabase-py · no code needed"]
        T_HRV & T_ACO --> T_VIEW
        TABLES --> SB_API
    end

    subgraph PROC["Processing Pipeline  —  Python scripts  run locally or GitHub Actions cron"]
        POLL["poll_new_sessions.py\nSELECT * FROM sessions\nWHERE processed_at IS NULL"]
        HRV_S["hrv_processor.py\nneurokit2 · pyHRV\n─────────────────\nPre/Post 5-min windows\n→ RMSSD · Mean HR · SD1\n─────────────────\nIn-session 30-sec windows 50% overlap\n→ HF power · RSA amplitude · Mean HR\n⚠ RMSSD not valid here"]
        ACO_S["acoustic_processor.py\nlibrosa · surfboard\n─────────────────\nfetch playlist audio\nSpotify API · yt-dlp fallback\n30-sec windows · 50% overlap\n→ tempo · bass_rms · am_rate\n→ centroid · zcr · onset_density\n→ silence_ratio · hnr"]
        WRITE["write results\nINSERT INTO hrv_windows\nINSERT INTO acoustic_windows\nUPDATE sessions SET processed_at = now()"]
        POLL --> HRV_S & ACO_S --> WRITE
    end

    subgraph ACCESS["Data Access  —  by persona"]
        META["Metabase  ★  non-experts\nfree · connects to Supabase Postgres\ndrag-and-drop charts · no SQL\nshare dashboards via link"]
        STUDIO["Supabase Studio\ntable editor · SQL console\nbrowse · filter · export CSV\nworks for admins + non-experts"]
        NB["Jupyter Notebooks\npandas · SQLAlchemy · supabase-py\nAI engineer workspace\nread feature_dataset directly"]
        SLIT_DASH["Streamlit Session Viewer\nPhase 0 facilitator tool\nlive RMSSD vs baseline\nHF power · Mean HR"]
    end

    subgraph EXTEND["Extension Points  —  add when ready  no architecture change needed"]
        MLFLOW["MLflow\nexperiment tracking\nmodel registry\nrun: mlflow ui"]
        LLM_EXT["LLM Connector\nsupabase REST → Claude API\nbiomarker rows → narrative\nPMC12512671 pattern"]
        BANDIT["Contextual Bandit\nvowpalwabbit\nPhase 3: state → sound action\nneeds ~30 action-reward cycles"]
        PGVEC["pgvector  Supabase extension\nsemantic search\nover session notes + outcomes\nenable in Supabase dashboard: 1 click"]
        GHA["GitHub Actions cron\nreplace manual poll script\nruns process_sessions.py\non schedule or webhook"]
    end

    %% Upload flow
    UP --> FORM & UPLOADER
    FORM & UPLOADER --> BUCKET & T_SESS & T_PART

    %% Processing trigger
    T_SESS --> POLL
    BUCKET --> HRV_S
    SB_API --> ACO_S
    WRITE --> T_HRV & T_ACO

    %% Access paths
    SB_API --> META & NB & SLIT_DASH
    BUCKET & T_SESS --> STUDIO

    %% Extension hooks
    NB --> MLFLOW
    SB_API --> LLM_EXT
    T_VIEW --> BANDIT
    T_SESS --> PGVEC
    POLL -.->|"upgrade path"| GHA

    %% Styling
    classDef zone fill:#1e1e2e,stroke:#7c7cff,color:#cdd6f4
    classDef store fill:#1e2e1e,stroke:#a6e3a1,color:#cdd6f4
    classDef script fill:#2e1e2e,stroke:#cba6f7,color:#cdd6f4
    classDef access fill:#1e2a2e,stroke:#89dceb,color:#cdd6f4
    classDef ext fill:#2a2a1e,stroke:#f9e2af,color:#cdd6f4
    classDef warn fill:#2e2010,stroke:#f38ba8,color:#cdd6f4

    class PART,STREAMLIT zone
    class BUCKET,T_PART,T_SESS,T_HRV,T_ACO,T_VIEW store
    class PROC,POLL,WRITE script
    class ACCESS,META,STUDIO,NB,SLIT_DASH access
    class EXTEND,MLFLOW,LLM_EXT,BANDIT,PGVEC,GHA ext
    class HRV_S warn
```

---

## Platform Decision: Supabase + Streamlit + Metabase

| Layer | Tool | Cost | Maintained by |
|---|---|---|---|
| Database + Storage + API | Supabase (managed Postgres) | Free tier covers POC | Supabase cloud — zero ops |
| Upload form | Streamlit Community Cloud | Free | Push to GitHub → auto-deploy |
| Non-expert dashboards | Metabase (self-hosted or cloud) | Free OSS / $500/yr cloud | Connect once to Supabase Postgres |
| AI engineer workspace | Jupyter + supabase-py | Free | Local or Google Colab |
| Experiment tracking | MLflow | Free | Run locally: `mlflow ui` |
| Processing scripts | Python (neurokit2 + librosa) | Free | Run manually or GitHub Actions |

**Why not alternatives:**
- *Airtable* — too limited for timeseries data and ML queries
- *Firebase* — NoSQL makes analytical joins painful
- *AWS/GCP* — overkill ops burden for a 4-person POC
- *Neon/PlanetScale* — no built-in file storage or Studio UI; harder for non-experts

---

## Database Schema

```sql
-- one row per study participant
CREATE TABLE participants (
    id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    name        text,
    email       text UNIQUE,
    demographics jsonb,           -- age, occupation, stress_context etc.
    created_at  timestamptz DEFAULT now()
);

-- one row per innerdance session
CREATE TABLE sessions (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    participant_id  uuid REFERENCES participants(id),
    session_date    date,
    playlist_url    text,
    form_data       jsonb,        -- PSS-3, energy 0-10, sleep 0-5, notes
    rr_file_path    text,         -- path in Supabase Storage bucket
    processed_at    timestamptz,  -- NULL = pending processing
    created_at      timestamptz DEFAULT now()
);

-- one row per 5-min pre/post window OR 30-sec in-session window
CREATE TABLE hrv_windows (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id      uuid REFERENCES sessions(id),
    window_ts       timestamptz,  -- start of window
    window_type     text,         -- 'pre' | 'post' | 'in_session'
    rmssd           float,        -- ms  — valid only for pre/post windows
    mean_hr         float,        -- bpm
    sd1             float,        -- ms  Poincaré short-term
    hf_power        float,        -- ms² — in_session primary signal
    rsa_amplitude   float         -- ms  — in_session vagal index
);

-- one row per 30-sec acoustic window
CREATE TABLE acoustic_windows (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id      uuid REFERENCES sessions(id),
    window_ts       timestamptz,  -- start of window — joins to hrv_windows
    tempo           float,        -- BPM
    bass_rms        float,        -- RMS energy 20-250 Hz
    am_rate         float,        -- amplitude modulation rate Hz
    spectral_centroid float,      -- Hz  brightness proxy
    zcr             float,        -- zero-crossing rate
    onset_density   float,        -- onsets/sec
    silence_ratio   float,        -- fraction of window below RMS threshold
    hnr             float         -- harmonic-to-noise ratio dB
);

-- AI engineers query this — no joins needed
CREATE VIEW feature_dataset AS
SELECT
    s.participant_id,
    h.session_id,
    h.window_ts,
    h.window_type,
    h.rmssd, h.mean_hr, h.sd1, h.hf_power, h.rsa_amplitude,
    a.tempo, a.bass_rms, a.am_rate, a.spectral_centroid,
    a.zcr, a.onset_density, a.silence_ratio, a.hnr,
    s.form_data->>'pss3_score'       AS pss3,
    s.form_data->>'energy_score'     AS energy,
    s.form_data->>'sleep_score'      AS sleep
FROM hrv_windows h
JOIN acoustic_windows a  USING (session_id, window_ts)
JOIN sessions s          ON s.id = h.session_id;
```

---

## AI Engineer Extension Path

How an AI engineer picks up from V1 without any architecture change:

```
1. EXPLORE          read feature_dataset via supabase-py or SQLAlchemy
                    pd.read_sql("SELECT * FROM feature_dataset", conn)

2. PHASE 0 (now)    threshold rule — compare RMSSD pre vs post per participant
                    ~2 hours to implement in a notebook

3. PHASE 1 (wk 1-4) within-person OLS per participant
                    statsmodels.formula.api.ols("rmssd ~ tempo + bass_rms + ...", data)

4. PHASE 2 (wk 2-14) Bayesian hierarchical model
                    import bambi as bmb
                    model = bmb.Model("rmssd ~ tempo + (1|participant_id)", data)

5. PHASE 3 (mo 3+)  contextual bandit — plug into existing feature_dataset
                    import vowpalwabbit as vw

6. REGISTER MODEL   mlflow.sklearn.log_model(model, "hrv_state_predictor")

7. SERVE            FastAPI endpoint reads model from MLflow registry
                    POST /predict  { acoustic_features } → { hrv_state, confidence }

8. CONNECT FACILITATOR UI  Streamlit reads from /predict + feature_dataset
```

---

## Conceptual Architecture (research reference)

```mermaid
flowchart TD

    subgraph PART["Participants"]
        PH10([Polar H10\nR-R stream via BLE])
        PFORM([Mobile Form\nPSS-3 · energy 0–10 · sleep 0–5])
        PAUDIO([Session Audio Log\ntimestamped recording])
        PLIST([Playlist Link\nSpotify URL · file upload])
    end

    subgraph PORTAL["Data Ingestion Portal  —  Web App"]
        BLE[Polar SDK / BLE Receiver]
        UI[Web Form + File Upload]
        ALOG[Audio Logger\ntimestamped capture]
    end

    subgraph STORAGE["Data Lake  —  Shared Storage"]
        RR[(R-R Interval Files\nraw Polar H10 CSV)]
        FORM_DB[(Session Metadata\nPSS-3 · energy · sleep · demographics)]
        AUDIO_DB[(Audio Store\ntimestamped session recordings)]
        PLIST_DB[(Playlist Registry\nURLs + audio cache)]
        FEAT_DS[("Feature Dataset  ★\nsession_id · window_ts\nacoustic_features[ ] · hrv_metrics[ ]")]
    end

    subgraph HRV_PROC["HRV Processing Pipeline"]
        PRE_POST["Pre / Post Windows  ✓\n5-min resting · seated\nRMSSD · Mean HR · SD1\n— RMSSD valid here only —"]
        IN_SES["In-Session Windows\n30-sec · 50% overlap\nHF power · RSA amplitude · Mean HR\n— RMSSD NOT valid during slow breathing —"]
        STATES["HRV State Labeller\nRMSSD bands:\nrelaxed · activated · transitional"]
    end

    subgraph ACOUSTIC_PROC["Acoustic Feature Extraction  —  librosa · surfboard"]
        FETCH[Playlist Fetcher\nSpotify API · yt-dlp fallback]
        WIN[30-sec Sliding Windows\n50% overlap · matched to HRV epochs]
        FEAT["Feature Extractor\ntempo BPM · bass RMS 20–250 Hz\nAM rate · spectral centroid\nZCR · onset density\nsilence ratio · HNR"]
    end

    subgraph ALIGN_BUILD["Alignment & Dataset Building"]
        ALIGN[Temporal Aligner\nHRV epochs ↔ acoustic windows\njoined by window_start_ts]
        BUILD[Dataset Builder\n+ metadata join · versioned]
    end

    subgraph ML_PIPELINE["ML Pipeline  —  AI Engineer Workspace"]
        direction LR
        PH0["Phase 0  MVP\nThreshold Rule-Based\nRMSSD vs personal baseline\nno training · immediate deploy\n★★★★★ HRV-B clinical standard"]
        PH1["Phase 1  Weeks 1–4\nWithin-Person OLS\nacoustic → RMSSD per participant\n~56–100 sessions/person\n★★★★ N-of-1 validated"]
        PH2["Phase 2  Weeks 2–14\nBayesian Hierarchical\nPyMC · bambi · cross-participant\ncredible intervals · publishable\n★★★★★ Sensors 2025 exact design"]
        PH3["Phase 3  Month 3+\nContextual Bandit\nvowpalwabbit · Thompson Sampling\nstate → sound action → HRV reward\n★★★★ adaptive health interventions"]
        PH4["Phase 4  Month 6+\nGAN Bidirectional\nHRV ↔ sound synthesis\nrequires ≥200 sessions\n★★★ simulation proof only"]
        EXP[Experiment Tracking\nMLflow / W&B]
        REG[(Model Registry\nversioned artefacts)]
        PH0 --> PH1 --> PH2 --> PH3 --> PH4
        PH2 & PH3 --> EXP --> REG
    end

    subgraph PROD["Production Services"]
        SERVE[Inference API\nHRV state prediction · FastAPI]
        LLM[LLM State Interpreter\nbiomarker → plain-language narrative\nPMC12512671 pipeline]
        PLIB[(Fixed Playlist Library\ncurated set → personalised later)]
        REC[Recommendation Engine\nranks playlists by predicted HRV state]
    end

    subgraph FAC["Facilitator Interface  —  Web App"]
        FINPUT[Patient Profile Input\ngoal · history · session type]
        LIVE[Live Session Dashboard\nreal-time HF power · RSA · Mean HR\nvs personal baseline]
        FREC[Playlist Recommendation\n+ predicted HRV trajectory]
        SADJ[Sound Adjustment Prompt\nbandit-recommended action\ntempo ↓ · bass ↑ · AM rate]
        FLOG[Session Outcome Log\nactual vs predicted HRV · notes]
    end

    PH10 --> BLE --> RR
    PFORM --> UI --> FORM_DB
    PAUDIO --> ALOG --> AUDIO_DB
    PLIST --> UI --> PLIST_DB
    RR --> PRE_POST & IN_SES
    PRE_POST --> STATES
    PLIST_DB --> FETCH --> WIN --> FEAT
    STATES & FEAT & FORM_DB --> ALIGN --> BUILD --> FEAT_DS
    FEAT_DS --> PH0 & PH1 & PH2
    REG --> SERVE --> LLM
    PLIB --> REC
    LLM --> REC
    FINPUT --> REC --> FREC
    IN_SES --> LIVE
    LLM --> LIVE
    PH3 --> SADJ --> LIVE
    FREC & LIVE --> FLOG
    FLOG -. session outcome + reward signal .-> FEAT_DS

    classDef zone fill:#1e1e2e,stroke:#7c7cff,color:#cdd6f4
    classDef store fill:#1e2e1e,stroke:#a6e3a1,color:#cdd6f4
    classDef actor fill:#2e1e1e,stroke:#f38ba8,color:#cdd6f4
    classDef svc fill:#1e2a2e,stroke:#89dceb,color:#cdd6f4
    classDef warn fill:#2e2010,stroke:#f9e2af,color:#cdd6f4

    class PART,PORTAL,ALIGN_BUILD,FAC zone
    class RR,FORM_DB,AUDIO_DB,PLIST_DB,FEAT_DS,PLIB,REG store
    class PH10,PFORM,PAUDIO,PLIST,FINPUT actor
    class SERVE,REC,LLM svc
    class IN_SES,PRE_POST warn
```

### Critical Design Constraints (from literature)

**RMSSD validity boundary** — RMSSD is only valid during the standardised 5-min pre/post resting windows (controlled breathing). Do NOT use RMSSD as the real-time in-session signal. Use HF power or RSA amplitude during sessions (AJP-Regu 2022).

**Acoustic feature logging is the bottleneck** — Without timestamped audio logs aligned to R-R data, Hypothesis 3 (acoustic → HRV coupling) cannot be tested. This infrastructure must be in place before sessions begin.

### Top Acoustic Features (empirically linked to HRV/ANS)

| Feature | Tool | Literature grounding |
|---|---|---|
| Tempo (BPM) | `librosa.beat.tempo` | ≤60 BPM → parasympathetic ↑ (PMC5339732, PMC4540583) |
| Bass energy RMS 20–250 Hz | `librosa.feature.rms` (filtered) | Ventral vagal postulated; innerdance low-freq signature |
| Amplitude modulation rate | Hilbert envelope | Brain.fm neural phase-locking (Woods et al. 2024, Nature portfolio) |
| Spectral centroid | `librosa.feature.spectral_centroid` | Brightness proxy; high = alerting, low = calming |
| Zero-crossing rate | `librosa.feature.zero_crossing_rate` | Roughness / harmonic complexity |
| Onset density | `librosa.onset.onset_detect` | Event rate; higher = more activating |
| Silence ratio | RMS threshold | Active regulatory tool in innerdance (documented in source) |
| Harmonic-to-noise ratio | `librosa.effects.harmonic` | Consonance; linked to social engagement system (SSP analogy) |
