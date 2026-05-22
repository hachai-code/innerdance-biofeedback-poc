-- Innerdance Biofeedback POC — Supabase Postgres Schema
-- Run this in the Supabase SQL Editor (one-time setup)
-- See database/README.md for setup instructions

-- ─────────────────────────────────────────────────────────
-- Extensions
-- ─────────────────────────────────────────────────────────

CREATE EXTENSION IF NOT EXISTS "pgcrypto";     -- gen_random_uuid()
CREATE EXTENSION IF NOT EXISTS "vector";       -- pgvector for future semantic search


-- ─────────────────────────────────────────────────────────
-- participants
-- One row per study participant
-- ─────────────────────────────────────────────────────────

CREATE TABLE participants (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    name            text,
    email           text UNIQUE,
    demographics    jsonb,
    -- demographics structure (example):
    -- { "age": 34, "occupation": "consultant", "stress_context": "work", "city": "Berlin" }
    created_at      timestamptz DEFAULT now()
);

COMMENT ON TABLE participants IS 'One row per study participant. Demographics stored as JSONB for flexibility.';


-- ─────────────────────────────────────────────────────────
-- sessions
-- One row per innerdance session
-- ─────────────────────────────────────────────────────────

CREATE TABLE sessions (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    participant_id  uuid REFERENCES participants(id) ON DELETE CASCADE,

    session_date    date NOT NULL,
    session_number  integer,                  -- 1-indexed per participant
    session_type    text DEFAULT 'innerdance', -- 'innerdance' | 'passive_rest' | 'activating_music'

    playlist_url    text,                     -- Spotify URL or null
    rr_file_path    text,                     -- path in Supabase Storage bucket 'rr-files'
    audio_file_path text,                     -- path in Storage, if uploaded

    form_data       jsonb,
    -- form_data schema (always use this structure — never change mid-study):
    -- {
    --   "pre_stress": 0-10,
    --   "post_stress": 0-10,
    --   "pre_energy": 0-10,
    --   "post_energy": 0-10,
    --   "sleep_quality_last_night": 1-5,
    --   "notable_events": "text"
    -- }

    sync_offset_sec float,                    -- seconds: R-R recording start → audio start (3-clap sync)
    polar_format    text DEFAULT 'polar_ecg', -- 'polar_ecg' | 'polar_beat'

    processed_at    timestamptz,              -- NULL = pending processing pipeline
    created_at      timestamptz DEFAULT now()
);

COMMENT ON TABLE sessions IS 'One row per session. processed_at is NULL until the processing pipeline completes.';
COMMENT ON COLUMN sessions.form_data IS 'Self-report form. Schema is fixed: pre_stress, post_stress, pre_energy, post_energy, sleep_quality_last_night, notable_events.';
COMMENT ON COLUMN sessions.sync_offset_sec IS '3-clap sync: seconds between Polar recording start and audio start.';

CREATE INDEX idx_sessions_participant ON sessions(participant_id);
CREATE INDEX idx_sessions_unprocessed ON sessions(processed_at) WHERE processed_at IS NULL;


-- ─────────────────────────────────────────────────────────
-- hrv_windows
-- One row per HRV analysis window
-- Pre/post: 5-min resting windows (RMSSD valid here)
-- In-session: 30-sec sliding windows, 50% overlap (use HF power, not RMSSD)
-- ─────────────────────────────────────────────────────────

CREATE TABLE hrv_windows (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id      uuid REFERENCES sessions(id) ON DELETE CASCADE,

    window_ts       timestamptz NOT NULL,     -- start of window (UTC) — join key with acoustic_windows
    window_type     text NOT NULL,            -- 'pre' | 'post' | 'in_session'

    -- Tier 1 metrics (pre/post only — RMSSD NOT valid during slow breathing)
    rmssd           float,                    -- ms. Valid for 'pre' and 'post' only.
    mean_hr         float,                    -- bpm
    sd1             float,                    -- ms (Poincaré short-term variability)

    -- In-session metrics (30-sec windows)
    hf_power        float,                    -- ms² (0.15–0.40 Hz band power)
    rsa_amplitude   float,                    -- ms (respiratory sinus arrhythmia amplitude)

    created_at      timestamptz DEFAULT now()
);

COMMENT ON TABLE hrv_windows IS 'HRV metrics per window. RMSSD is valid only for pre/post windows. Use hf_power and rsa_amplitude for in-session analysis.';
COMMENT ON COLUMN hrv_windows.rmssd IS 'Valid ONLY for window_type=pre or post. During slow breathing (innerdance sessions), RMSSD is physiologically invalid. See AJP-Regu 2022.';

CREATE INDEX idx_hrv_session ON hrv_windows(session_id);
CREATE INDEX idx_hrv_window_ts ON hrv_windows(session_id, window_ts);


-- ─────────────────────────────────────────────────────────
-- acoustic_windows
-- One row per 30-sec acoustic analysis window
-- ─────────────────────────────────────────────────────────

CREATE TABLE acoustic_windows (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id      uuid REFERENCES sessions(id) ON DELETE CASCADE,

    window_ts       timestamptz NOT NULL,     -- start of window (UTC) — join key with hrv_windows

    -- Features empirically linked to HRV/ANS response (see docs/research/step2_metrics_hypothesis_v2.md)
    tempo           float,                    -- BPM. ≤60 BPM → parasympathetic ↑ (PMC5339732)
    bass_rms        float,                    -- RMS energy 20–250 Hz (ventral vagal postulated)
    am_rate         float,                    -- Hz. Amplitude modulation rate (Brain.fm: Woods 2024)
    spectral_centroid float,                  -- Hz. Brightness proxy: high = alerting, low = calming
    zcr             float,                    -- Zero-crossing rate (roughness / harmonic complexity)
    onset_density   float,                    -- Onsets/sec. Higher = more activating
    silence_ratio   float,                    -- Fraction of window below RMS threshold
    hnr             float,                    -- Harmonic-to-noise ratio dB (consonance proxy)

    created_at      timestamptz DEFAULT now()
);

COMMENT ON TABLE acoustic_windows IS '30-sec acoustic windows. Extracted with librosa/surfboard. Join to hrv_windows on (session_id, window_ts).';

CREATE INDEX idx_acoustic_session ON acoustic_windows(session_id);
CREATE INDEX idx_acoustic_window_ts ON acoustic_windows(session_id, window_ts);


-- ─────────────────────────────────────────────────────────
-- feature_dataset (VIEW)
-- The primary interface for AI engineers and ML models.
-- Joins hrv_windows + acoustic_windows + session metadata.
-- Query this — do not join tables manually in notebooks.
-- ─────────────────────────────────────────────────────────

CREATE VIEW feature_dataset AS
SELECT
    s.participant_id,
    h.session_id,
    s.session_date,
    s.session_number,
    s.session_type,
    h.window_ts,
    h.window_type,

    -- HRV metrics
    h.rmssd,
    h.mean_hr,
    h.sd1,
    h.hf_power,
    h.rsa_amplitude,

    -- Acoustic features
    a.tempo,
    a.bass_rms,
    a.am_rate,
    a.spectral_centroid,
    a.zcr,
    a.onset_density,
    a.silence_ratio,
    a.hnr,

    -- Self-report (from session form)
    (s.form_data->>'pre_stress')::float               AS pre_stress,
    (s.form_data->>'post_stress')::float              AS post_stress,
    (s.form_data->>'pre_energy')::float               AS pre_energy,
    (s.form_data->>'post_energy')::float              AS post_energy,
    (s.form_data->>'sleep_quality_last_night')::float AS sleep_quality

FROM hrv_windows h
JOIN acoustic_windows a  ON  a.session_id = h.session_id
                         AND a.window_ts  = h.window_ts
JOIN sessions s          ON  s.id         = h.session_id;

COMMENT ON VIEW feature_dataset IS 'Primary ML interface. One row per 30-sec aligned window. Filter on window_type: use pre/post for RMSSD, in_session for hf_power/rsa_amplitude.';


-- ─────────────────────────────────────────────────────────
-- Row-level security (enable after initial data load)
-- ─────────────────────────────────────────────────────────

-- ALTER TABLE participants ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE sessions ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE hrv_windows ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE acoustic_windows ENABLE ROW LEVEL SECURITY;
-- Uncomment and configure policies once auth is set up.
