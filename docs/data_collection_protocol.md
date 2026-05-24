# Data Collection Protocol

This is the single reference for what to record, when, in what format, and why.
Do not change any schema mid-study — all analyses depend on consistent field names.

---

## Overview

Each session produces four things:

| What | Format | Who collects |
|---|---|---|
| R-R interval recording | Polar H10 CSV export | Participant |
| Self-report form | JSON (fixed schema) | Participant (phone) |
| Session metadata | JSON | Participant or researcher |
| Stage timestamps | CSV | Researcher present, or logged live |

---

## Before the session

### 1. Baseline days (days 1–3, first week only, no innerdance)
Collect 3 resting RMSSD readings before any sessions begin. These become the participant's **personal baseline** — all subsequent RMSSD values are expressed as % of this baseline, making cross-participant comparisons valid.

Protocol: 5 min seated, relaxed, normal breathing. Polar H10 recording. Export R-R CSV.

### 2. Pre-session rest window (every session)
- Put on Polar H10. Start recording in Polar Beat.
- Sit quietly for **5 minutes** — seated, no talking, normal breathing.
- This is the only window where RMSSD is valid (AJP-Regu 2022: RMSSD is invalid during slow breathing typical of innerdance).

### 3. Sync event (every session with audio)
- After the 5-min rest window, **clap 3 times loudly** before starting the audio.
- The clap appears as a sharp spike in both the R-R data and the audio waveform.
- This shared event is used to align the two recordings. Record the computed offset in `metadata.json` as `sync_offset_sec`.

### 4. Pre-session self-report (every session)
Fill in `pre_stress` and `pre_energy` fields immediately before starting audio (2 min on phone).

---

## During the session

- Lie down, listen. No action required from participant.
- If a researcher is present: **log stage timestamps in real time** as the audio transitions between stages. Format: `stage, start_sec, label` (seconds from session start).
- Stage timestamps are required for per-stage HRV analysis. Without them only whole-session metrics are available (as with P4/P5/P6 in the current dataset).

---

## After the session

### 1. Post-session rest window (every session)
- **Do not stop the Polar recording yet.**
- Sit quietly for **5 minutes** — same conditions as the pre-session window.
- This establishes the post-session RMSSD reference and enables the rebound comparison.
- Then stop recording and export R-R CSV from Polar Beat.

### 2. Post-session self-report (every session)
Fill in `post_stress`, `post_energy`, and `sleep_quality_last_night` immediately after (2 min on phone).

### 3. Subjective wellbeing (recommended addition)
Administer **PANAS** (Positive and Negative Affect Schedule) or **SUDS** (Subjective Units of Distress Scale, 0–10) immediately pre and post session. This is the minimum addition needed to test H4 (physiological rebound predicts subjective wellbeing). Costs 2 min.

### 4. Upload
Upload via the React app (or Google Drive until the app is ready):
- R-R CSV file
- `self_report.json`
- `metadata.json`
- Stage timestamps CSV (if available)
- Audio file or playlist link

---

## Self-report schema (fixed — never change mid-study)

```json
{
  "pre_stress": 0,
  "post_stress": 0,
  "pre_energy": 0,
  "post_energy": 0,
  "sleep_quality_last_night": 3,
  "notable_events": ""
}
```

| Field | Scale | When |
|---|---|---|
| `pre_stress` | 0–10 (0 = no stress) | Before session |
| `post_stress` | 0–10 | After session |
| `pre_energy` | 0–10 (0 = exhausted) | Before session |
| `post_energy` | 0–10 | After session |
| `sleep_quality_last_night` | 1–5 (1 = very poor) | After session |
| `notable_events` | Free text, optional | After session |

---

## Session metadata schema

```json
{
  "start_time_utc": "2025-12-14T12:50:00Z",
  "duration_min": 60,
  "sync_offset_sec": 4.2,
  "session_type": "innerdance",
  "audio_source": "spotify:playlist:xxx",
  "polar_format": "polar_ecg"
}
```

| Field | Values |
|---|---|
| `session_type` | `innerdance` / `passive_rest` / `activating_music` |
| `polar_format` | `polar_ecg` (raw H10 ECG export) / `polar_beat` (Polar Beat app CSV) |
| `sync_offset_sec` | Seconds between Polar recording start and audio start (from 3-clap alignment) |

---

## Stage timestamps schema

```csv
stage,start_sec,label
baseline,0,Resting baseline
stress,300,Stress induction
1,600,Stage 1 - Befriedigung
2,900,Stage 2 - Unzufriedenheit
3,1140,Stage 3 - Die Schwelle
4,1380,Stage 4 - Freisetzung
5,1680,Stage 5 - Desintegration
6,1920,Stage 6+7 - Erwachen
8,2520,Stage 8+9 - Wahl
10,2940,Stage 10 - Dunkle Nacht
11,3180,Stage 11+12 - Einheit
```

`start_sec` = elapsed seconds from the moment the Polar recording started (not from audio start — apply `sync_offset_sec` to convert).

---

## Metric pairs: what is measured and when

### Primary (every session from day 1)

| Metric | Type | Window | Why |
|---|---|---|---|
| RMSSD | HRV | 5-min pre-session rest | Personal baseline anchor; vagal tone at rest. Valid here only. |
| RMSSD | HRV | 5-min post-session rest | Post-session recovery reference |
| Mean HR | HRV | Pre + post + in-session | Resting HR trend; arousal reference |
| PSS-3 / `pre_stress` | Self-report | Pre-session | Perceived stress at entry |
| `post_stress` | Self-report | Post-session | Perceived stress at exit |

### Within-session (requires stage timestamps)

| Metric | Type | Window | Why |
|---|---|---|---|
| SD2 | HRV | 30-sec sliding, 50% overlap | Total autonomic flexibility; valid during slow breathing |
| SD1/SD2 ratio | HRV | 30-sec sliding | Sympathovagal balance direction |
| DFA α1 | HRV | Per stage (~150–300 beats) | Nonlinear regulatory integrity; <0.75 = activation zone |
| Mean HR | HRV | Per stage | Arousal reference |

**Note:** RMSSD is NOT valid during in-session windows when participants breathe slowly (<9 bpm). Use SD2 and DFA α1 instead (AJP-Regu 2022).

### Secondary (add from session 3 onward)

| Metric | Type | Timing | Why |
|---|---|---|---|
| `sleep_quality_last_night` | Self-report | Morning of session day | Sleep-HRV link (Sensors 2025: β=0.510) |
| `pre_energy` / `post_energy` | Self-report | Pre + post | Energy/recovery proxy |
| PANAS or SUDS (0–10) | Self-report | Pre + post | Tests H4: rebound predicts subjective wellbeing |

### Long-term (after 4+ weeks)

| Metric | Type | Why |
|---|---|---|
| Morning RMSSD (daily) | HRV | Cumulative autonomic flexibility trend (H3, H6) |
| SDNN | HRV | Cardiovascular resilience at 4–8 week scale |

---

## Comparison conditions

Running the same participant under different conditions is what separates "innerdance works" from "any sound works" or "sitting quietly works."

| Condition | Sessions | Purpose |
|---|---|---|
| A: Innerdance session | 8–10 | Treatment |
| B: Passive rest (silence, same duration) | 2–3 | Controls for "just sitting quietly" |
| C: Activating music (>120 BPM) | 1–2 | Controls for "music in general" |

If condition C produces the same arc as A: the effect is music in general, not innerdance specifically. If only A produces the arc: mechanistically specific result.

---

## Participant baseline profile (collect once)

| Field | Type | Why |
|---|---|---|
| Age | Integer | HRV decreases with age; must control for |
| Fitness level | Low / Medium / High / Athlete | Strongly predicts baseline RMSSD |
| Smoker | Yes / No | Smoking suppresses HRV |
| Mindfulness / meditation practice | Yes / No | Predicts higher baseline HRV and arc amplitude |
| Chronic stress context | Free text | Frames the intervention target |

---

## Minimum additions for the next data collection round

From the HTML report's Principal Data Scientist Summary — these unlock H1–H4 with no new sensors:

1. **Per-stage timestamps for all participants** — log in real time during session
2. **5-min post-session rest window** — sit quietly after session before stopping recording
3. **PANAS or SUDS** (pre + post, 2 min) — adds subjective wellbeing measurement

Optional but high-value:
4. **Breathing belt (~€50)** — resolves the DFA α1 ambiguity (slow breathing vs. SNS activation produce the same signal); enables H6 (respiratory entrainment)

---

## Data quality checks (run on every upload)

- R-R file has >90% of intervals in 300–2000 ms range (basic artefact flag)
- Pre-session rest window is present and ≥4 min long
- Post-session rest window is present and ≥4 min long
- Audio duration and R-R duration differ by <3 min (sync sanity check)
- Self-report fields `pre_stress`, `post_stress`, `pre_energy`, `post_energy` are all filled
