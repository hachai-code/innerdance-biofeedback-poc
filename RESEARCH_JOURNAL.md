# Innerdance Biofeedback POC — Research Journal

**Project:** Physiological evidence for the innerdance sound technique as a training for autonomic flexibility and stress resilience  
**Researcher:** Monica Rafaila, Futurice  
**Last updated:** 2026-05-22  
**Current phase:** Ideation — reviewing findings, agreeing on hypotheses, designing next data collection round

---

## The primary output

**Open [`outputs/innerdance_model_report_v2.html`](outputs/innerdance_model_report_v2.html) in a browser.** It is the authoritative document. Everything below is a structured summary of how the project got there and what the key decisions were.

---

## What innerdance is — the physiological frame

Innerdance is a facilitated or self-administered sound practice. The participant lies down and listens to a structured 60–90 min playlist progressing through 12 named stages. Each stage has a characteristic brainwave state and a corresponding audio track.

**The key physiological insight:** Innerdance co-stimulates the sympathetic (SNS) and parasympathetic (PNS) nervous systems in sequence. It is not relaxation — it is **autonomic flexibility training**. The arc goes: grounding → activation peak (Stage 4, Alpha/Beta) → deep recalibration (Stage 10, Delta) → integration. The value is the range traversed and the speed of recovery, not just the rest state at the end.

**Closest published analog:** The Safe and Sound Protocol (SSP, Porges). Both use acoustic stimulation targeting the ventral vagal complex via auditory-motor circuits. Gitler et al. (2025, *Medicine International*) explicitly call for "AI-driven adaptive biofeedback" as SSP's natural extension — which is what this project builds toward.

---

## Research design evolution: a compressed summary

The design went through five documented iterations. The full documents are in `docs/research/`. Here is only what matters for understanding the current state.

### Critical constraint discovered (Step 2)
RMSSD is invalid during slow breathing (< 9 bpm, AJP-Regu 2022). Innerdance guides participants toward slow, deep breathing. **RMSSD is only valid in the 5-min pre/post resting windows. Within-session: use SD2, DFA α1, and SD1/SD2 ratio.** This is baked into every downstream design decision.

### Resilience reframe (Step 5)
The original framing was "RMSSD goes up after a session." The corrected framing: the session traverses an activation → recovery arc. The metric of interest is the **range** (SD2 at Stage 10 vs. Stage 4) and the **DFA α1 trajectory** across stages, not just a pre/post delta.

### Two-stream design (Step 4)
Stream A: observe and describe (always running). Stream B: validate one hypothesis at a time in order. Do not run H5 (acoustic features) before H1 (arc exists) is confirmed. Do not pool participants before confirming the pattern holds per individual.

---

## Data collected: Dec 2025 cohort

All sessions used the same protocol: 7-min resting baseline + stress induction (paper reading + questions) + 12-stage innerdance session. Audio: standard 12-stage playlist (see `sound/12 stages tracks/`).

| ID | Age | Profile | RMSSD | Mean HR | DFA α1 | Stages | Stage timestamps |
|---|---|---|---|---|---|---|---|
| P1 | 38 | Athlete, very fit | 103.6 ms | 52.9 bpm | 0.989 | 12 full | Full + pre-session baseline |
| P2 | 42 | Mindfulness practitioner | 34.4 ms | 67.6 bpm | 1.431 | 12 full | From session log |
| P3 | 43 | Interiorised | 17.3 ms | 81.2 bpm | 1.436 | 12 full | From session log |
| P4 | 42 | Unfit, coleric, smoker | 14.5 ms | 76.1 bpm | 1.304 | 12 full | None available |
| P5 | 43 | Smoker | 17.5 ms | 75.7 bpm | 1.455 | First 5 only | None available |
| P6 | 46 | — | 18.2 ms | 80.4 bpm | 1.638 | Last stages only | None available |

**P1/P2/P3** have per-stage timestamps → used for stage-level HRV analysis.  
**P4/P5/P6** have whole-session metrics only.

**Critical note on cross-participant comparison:** Absolute RMSSD must not be compared across participants. P1 (athlete, 38) is expected to have 3–5× higher RMSSD than P3 from fitness and age alone. Only within-person delta values (Δ from personal baseline) are valid for cross-participant statements.

---

## Audio analysis

9 tracks analysed (librosa, first 600 s each). 6 acoustic features extracted per track.

| Feature | Method | What it captures |
|---|---|---|
| Overall Energy (RMS) | RMS amplitude of full signal | Loudness / arousal driver |
| Bass Energy | RMS of 20–250 Hz band (Butterworth bandpass) | Somatic / vestibular activation |
| Tonal Brightness | Spectral centroid (Hz) | High = alerting / sharp; Low = calming / warm |
| AM Depth | CV of Hilbert envelope (2 Hz LP) | Modulation / pulsing texture; respiratory entrainment candidate |
| Onset Strength | Mean onset strength envelope | Percussive drive / motor activation |
| Rhythm Clarity | CV of onset envelope (std/mean) | Clear beat vs. ambient drone |

**Note — Tempo BPM was not used:** librosa returned 117–129 BPM across all tracks (the DJ's consistent tempo), making it uninformative for discriminating between stage types.

Qualitative categories (Low / Medium / High) assigned by 33rd/67th percentile thresholds across the 9-track set. These thresholds are **relative to this track set only**.

### Stage-to-acoustic-feature map (summary)

| Stage | Energy | Bass | Brightness | AM Depth | Onset | Rhythm | Primary ANS role |
|---|---|---|---|---|---|---|---|
| S1 Safety | Low | Low | Low | High | Low | Low | PNS grounding |
| S2 Dissatisfaction | High | High | Medium | Medium | Medium | Medium | Transition / activation start |
| S3 Threshold | Medium | Medium | High | Low | High | High | Liminal — neither state |
| **S4 Release** | **High** | **High** | **Medium** | **Medium** | **Low** | **Low** | **SNS activation peak** |
| S5 Disintegration | Medium | Medium | Low | Medium | High | Low | Holding / suspension |
| S6+7 Awakening | Medium | Medium | Medium | High | Medium | Medium | Recovery begins |
| S8+9 Choice | High | High | High | Low | High | High | Secondary activation |
| **S10 Dark Night** | **Low** | **Low** | **High** | **Low** | **Medium** | **Medium** | **PNS rebound peak** |
| S11+12 Unity | Low | Low | Low | High | Low | High | Integration / coherence |

---

## HRV findings

### HRV metrics used and why

| Metric | Valid when | Used for |
|---|---|---|
| RMSSD | Pre/post 5-min resting windows only | Personal baseline anchor; pre/post delta |
| SD2 (Poincaré long-axis) | All stages (including slow breathing) | Primary within-session flexibility marker |
| SD1/SD2 ratio | All stages | Sympathovagal balance direction |
| DFA α1 | All stages (with caveat — see below) | Nonlinear regulatory integrity; < 0.75 = activation/dysregulation zone |

**DFA α1 caveat:** Slow breathing AND SNS activation both produce similar DFA α1 signals. Without a concurrent respiratory rate measurement, DFA α1 values below 0.75 are ambiguous — they could mean genuine SNS peak or simply slow, deep breathing. This is the most important unresolved confound in the dataset.

### Key findings (P1, per-stage analysis)

| Stage | RMSSD (ms) | Δ from S1 | SD2 (ms) | DFA α1 | Interpretation |
|---|---|---|---|---|---|
| Pre-session baseline | 103 | — | 244.3 | — | Personal anchor |
| Paper reading | ~120 | — | — | 0.638 | DFA α1 drop = slow paced breathing artifact (McCreary 2022) |
| Questions (stress) | 80 | — | — | 1.269 | Mild cognitive stress confirmed |
| S1 | 114.7 | +10.5 | 155.3 | 0.873 | Immediate session recovery |
| S2 | 99.1 | −5.1 | 154.9 | 0.833 | Slight dip |
| S3 | 107 | — | — | 0.98 | Threshold / neutral |
| **S4** | **94.9** | **−9.3** | ~94 | **0.777** | **SNS activation — below 0.85 regulatory range** |
| S5 | ~98 | — | ~101 | 1.29 | |
| S6+7 | ~101 | — | ~101 | 1.22 | Recovery begins |
| S8+9 | ~97 | — | 123.5 | 1.25 | Secondary build |
| **S10** | **117.6** | **+13.4** | **241.4** | **1.236** | **PNS rebound — strongest SD2 in session** |
| S11+12 | ~106 | — | 104.5 | 1.40 | Integration |

**P2 and P3** show consistent directional trends (SD2 rise in S8+9 and S10) but at lower absolute values — consistent with their lower baseline HRV.

### Confidence assessment (from the report's critical review)

| Finding | Confidence | Key concern |
|---|---|---|
| Stage 4 is the SNS activation peak | Medium | N=3 per-stage. Timestamp boundaries introduce ±15–60 s uncertainty at 3–5 min stages |
| Stage 10 is the PNS rebound peak | Medium | S10 SD2 (241 ms) ≈ pre-session baseline (244 ms) — may be return to rest, not overshoot. DFA α1 = 1.236 is stronger evidence |
| H5 "activation → rebound overshoot" | Low | Δ of +1.1 ms RMSSD is within measurement noise. Rephrase as "trend consistent with H5" |
| DFA α1 < 0.75 during paper-reading | High | Well-supported by McCreary 2022. Critical implication: same ambiguity applies within session |
| Acoustic thresholds (Low/Med/High) | Low | Calibrated from 9 tracks. 33rd percentile of 9 = 3rd-lowest value. Not stable estimates |
| Acoustic features drive HRV changes | Low | No causal link established. Stage order is fixed — confounded with elapsed time and expectation |

---

## The 12 research hypotheses

Derived from the current data and HRV-biofeedback literature. Full rationale in the HTML report.

### Tier 1 — Test in next round
*Cost: add timestamps to all participants + 5-min post-session rest window + PANAS/SUDS*

| H | Statement | Key features | Key metric |
|---|---|---|---|
| H1 | Acoustic energy arc predicts autonomic arc (DFA α1 drop at S4, recovery by S12) | RMS energy, bass energy | DFA α1 per stage; SD2 final vs. baseline |
| H2 | Within-session RMS energy negatively correlates with DFA α1 (Spearman ρ < −0.4) | RMS energy | DFA α1 per stage |
| H3 | Higher pre-session DFA α1 (≥0.9) → larger arc amplitude (dose-response) | Pre-session baseline | Δ DFA α1 and Δ SD2 |
| H4 | Larger DFA α1 rebound (S10 vs S4) → greater post-session subjective wellbeing | S4/S10 energy contrast | DFA α1 delta; PANAS or SUDS |

### Tier 2 — Expanded study (N≥15, additional sensors or controlled stimuli)

| H | Statement | New requirement |
|---|---|---|
| H5 | Sub-bass (20–80 Hz) predicts DFA α1 reduction independently of loudness | Purpose-designed tracks with matched RMS, varied sub-bass |
| H6 | AM modulation at respiratory frequency (0.15–0.25 Hz) entrains breathing and raises SD2 | Breathing belt; AM rate spectrum (dominant modulation frequency of Hilbert envelope) |
| H7 | Vocal presence produces higher SD1/SD2 than instrumental at matched energy | Vocal presence classifier (pyannote.audio) |
| H8 | Spectral brightness > ~1100 Hz independently predicts SNS activation | Purpose-designed tracks: high brightness / low energy and vice versa |
| H9 | Full-arc sessions improve next-night sleep quality | Next-morning PSQI or single-item sleep questionnaire |

### Tier 3 — Future research programme

| H | Statement | Why later |
|---|---|---|
| H10 | Map acoustic tipping points (feature combinations → DFA α1 < 0.75) | Requires N≥50 sessions for 3D threshold surface |
| H11 | Track order is irreplaceable: randomising order eliminates S10 rebound | Crossover design, 1-week washout; most important causal test |
| H12 | Full-arc sessions produce salivary cortisol reduction | Lab-grade cortisol assay, N≥30 per group |

**H11 is the single most important experiment.** Without it, every finding is equally consistent with "the music causes this" and "time-on-task + expectation causes this." It cannot be run until the basic pattern is replicated across N≥10 participants.

---

## What the ideation workshop should decide

The next meeting should produce answers to these questions:

**Which hypotheses to focus on first?**
Tier 1 hypotheses (H1–H4) require almost no new infrastructure — just timestamps, a rest window, and a questionnaire. They are the highest-value next step. Which 1–2 from Tier 2 are worth adding a breathing belt for (H6 is the strongest candidate)?

**Who does what?**
| Role | Work |
|---|---|
| Data collection (participants) | Follow protocol, record with Polar H10, fill form, upload |
| Facilitator / researcher | Log per-stage timestamps in real time; administer PANAS pre/post |
| Data engineer | Build Streamlit upload form + Supabase pipeline |
| Audio engineer / practitioner | Decide: test existing tracks or design new tracks for H5/H8? |
| ML engineer | Phase 0 dashboard (personal RMSSD baseline); later H1–H4 analysis |

**How to design sound and participant sessions for the hypotheses?**
- H1/H2: existing playlist is fine; need per-stage timestamps and post-session rest
- H5: need new tracks with matched RMS but different sub-bass — who designs them?
- H6: need to measure AM rate spectrum from existing tracks (extractable now) + add breathing belt
- H11: session where track order is shuffled — who is willing to test this?

**Participant selection for next round:**
- Include participants with DFA α1 baseline ≥ 0.9 to test H3 (P1-type baseline needed)
- Include at least 2 mindfulness practitioners and 2 complete novices to test individual moderators
- All participants must be able to provide per-stage timestamps (facilitator is present or timestamps are logged automatically)

---

## Analysis scripts

| Script | What it does | Input | Output |
|---|---|---|---|
| `analysis/01_stage_hrv_analysis.py` | Stage-level RMSSD per session. Tests H1 arc and H5 activation → rebound | R-R CSV + stages CSV | 3 figures per session in `outputs/figures/` |
| `analysis/02_audio_rr_feature_map.py` | Plots acoustic features alongside RR signal on shared time axis | Audio file + R-R CSV | Feature map figure |
| `analysis/03_qualitative_model_report.py` | Generates `outputs/innerdance_model_report_v2.html` | Participant CSVs + audio files (not in repo) | HTML report |

To regenerate the HTML report: `python analysis/03_qualitative_model_report.py` (requires local data files).

---

## What to add in the next acoustic feature pass

These three features are extractable from existing audio with no new recordings:

1. **AM rate spectrum** — power spectrum of the Hilbert envelope; identifies dominant modulation frequency. Tests whether S11+12's high AM depth falls in the respiratory band (0.15–0.25 Hz), which is the key test for H6.
2. **Sub-bass energy split** — separate 20–80 Hz (chest vibration / vestibular) from 80–250 Hz (kick drum / midrange). Required for H5. Currently the two are r ≈ 0.99 correlated in this track set.
3. **Vocal presence score** — ratio of energy in 85–255 Hz fundamental + 2–5 kHz formants, or a pretrained vocal activity detector (pyannote.audio). Required for H7.

---

## File map

```
innerdance-biofeedback-poc/
├── CLAUDE.md                                   ← Read first. All conventions and technical decisions.
├── README.md                                   ← Project overview, hypotheses, next steps
├── RESEARCH_JOURNAL.md                         ← This document
├── .gitignore
├── requirements.txt
│
├── outputs/
│   └── innerdance_model_report_v2.html         ← PRIMARY OUTPUT — open in browser
│
├── analysis/
│   ├── 01_stage_hrv_analysis.py                ← Stage RMSSD, H1 + H5 tests
│   ├── 02_audio_rr_feature_map.py              ← Audio + RR alignment plot
│   └── 03_qualitative_model_report.py          ← Generates the HTML report
│
├── docs/
│   ├── architecture.md                         ← V1 platform design (Supabase + Streamlit)
│   └── research/
│       ├── step2_metrics_hypothesis_v2.md      ← Literature + ML approach reference
│       ├── step3_sequence_models.md            ← Sequence model technical reference
│       ├── step4_pragmatic_approach.md         ← Two-stream pivot
│       └── step5_refined_approach.md           ← Resilience framing + protocol design
│
├── data/
│   └── README.md                               ← Data schema, formats, participant list
│
├── database/
│   └── schema.sql                              ← Supabase Postgres tables + feature_dataset view
│
├── app/
│   └── README.md                               ← Streamlit upload form (not yet built)
│
└── notebooks/
    └── README.md                               ← Jupyter workspace instructions
```
