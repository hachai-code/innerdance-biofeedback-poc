# Innerdance Biofeedback POC

A feasibility study and hypothesis-generation instrument exploring how the **innerdance** sound technique modulates the autonomic nervous system, measured via HRV from a Polar H10 chest strap.

**Current phase:** Ideation — reviewing the analysis report, agreeing on hypotheses to pursue, and designing the next data collection round.

---

## Primary output

**[`outputs/innerdance_model_report_v2.html`](outputs/innerdance_model_report_v2.html)** — Open this in a browser. It is the authoritative document for everything this POC found.

It contains:
- Per-participant HRV profiles (N=6)
- Per-stage acoustic feature analysis (8 tracks, 6 features)
- Qualitative acoustic × HRV model (the stage map)
- 12 tiered research hypotheses
- A full critical review of what is reliable vs. what needs more data

---

## What was done

**6 participants** recorded during innerdance sessions (Dec 2025, Polar H10).  
**3 participants (P1/P2/P3)** have per-stage timestamps and are used for stage-level HRV analysis.  
**8 audio tracks** (12 innerdance stages) analysed with librosa.  
**4 HRV metrics** computed per stage: RMSSD (pre/post only), SD2, SD1/SD2, DFA α1.  
**6 acoustic features** extracted per track: Overall Energy, Bass Energy, Tonal Brightness, AM Depth, Onset Strength, Rhythm Clarity.

Key finding (P1, with full timestamps): Stage 4 (Purgation-Release) is the SNS activation peak (DFA α1 = 0.777). Stage 10 (Dark Night of the Soul) is the PNS rebound peak (SD2 = 241 ms, DFA α1 = 1.236).

**Important caveat:** N=3 per stage. These findings are hypothesis-generating, not statistically conclusive. No causal claim about acoustic features driving HRV changes can yet be made.

---

## Research hypotheses (from the report)

12 hypotheses in 3 tiers. The full rationale, required design, and critical assessment for each is in the report.

### Tier 1 — Test in next data collection round
*(add per-stage timestamps + 5-min post-session rest window + PANAS/SUDS questionnaire)*

| H | Statement |
|---|---|
| H1 | Acoustic energy arc (low → S4 peak → quiet S10) predicts autonomic arc (DFA α1 drop then recovery) |
| H2 | Within-session RMS energy negatively correlates with DFA α1 (Spearman ρ < −0.4) |
| H3 | Higher pre-session DFA α1 (≥0.9) predicts larger within-session arc amplitude |
| H4 | Larger DFA α1 rebound (S10 vs S4) predicts greater post-session subjective wellbeing |

### Tier 2 — Expanded study (N≥15, additional sensors or controlled stimuli)
*(breathing belt unlocks H6; purpose-designed tracks unlock H5/H7/H8)*

| H | Statement |
|---|---|
| H5 | Sub-bass (20–80 Hz) predicts DFA α1 reduction independently of overall loudness |
| H6 | AM modulation at respiratory frequency (0.15–0.25 Hz) entrains breathing and raises SD2 |
| H7 | Vocal presence produces higher SD1/SD2 than instrumental tracks at equivalent energy |
| H8 | Spectral brightness above ~1100 Hz independently predicts SNS activation |
| H9 | Full-arc sessions predict better next-night sleep quality |

### Tier 3 — Future research programme
| H | Statement |
|---|---|
| H10 | Identify acoustic tipping points (feature combinations) that reliably cross DFA α1 < 0.75 |
| H11 | The arc is the therapy: randomising track order eliminates the PNS rebound at S10 |
| H12 | Full-arc sessions produce salivary cortisol reduction vs. waiting-room control |

**Single most important experiment** (H11): until track order is counterbalanced, every result is equally consistent with "music matters" and "time-on-task + expectation matters."

---

## What is reliable vs. what needs caution

From the report's critical review:

| What is reliable | What needs caution |
|---|---|
| P1's within-session HRV shows a plausible autonomic arc using DFA α1 and SD2 | No causal music→HRV claim is supportable yet |
| Audio feature extraction pipeline is technically sound | Cross-participant absolute HRV comparisons are invalid (P1 RMSSD ~104 ms vs P3 ~17 ms: both valid for their profiles) |
| Respiratory-sinus artifact identification during paper-reading is valid | DFA α1 ambiguous without respiratory rate (slow breathing and SNS activation produce the same signal) |
| Qualitative Low/Medium/High framework is a reasonable starting point | Acoustic feature thresholds are relative to this 9-track set; not stable population estimates |

---

## Next steps

The recommended minimum additions for the next round (from the report's Principal Data Scientist Summary):

1. **Per-stage timestamps** for all participants — unlocks H1–H4 with no new sensors
2. **5-min post-session rest window** — establishes a true rebound reference
3. **PANAS or SUDS questionnaire** (pre + post) — adds subjective wellbeing measure
4. **Breathing belt (~€50)** — single highest-value sensor upgrade; resolves DFA α1 ambiguity and enables H6
5. **New acoustic features**: AM rate spectrum (dominant modulation frequency), sub-bass split (20–80 Hz vs 80–250 Hz), vocal presence score

---

## Setup

```bash
git clone <repo-url>
cd innerdance-biofeedback-poc
pip install -r requirements.txt

# Regenerate the HTML report (requires data files — not in repo)
python analysis/03_qualitative_model_report.py

# Run stage-level HRV analysis (add your session to SESSIONS list first)
python analysis/01_stage_hrv_analysis.py
```

---

## Repository layout

```
outputs/innerdance_model_report_v2.html   ← PRIMARY OUTPUT — open this first
analysis/                                 ← HRV + acoustic analysis scripts
docs/                                     ← Research journal, architecture, step files
data/                                     ← Participant data — gitignored
database/                                 ← Supabase Postgres schema
app/                                      ← Streamlit upload form (not yet built)
notebooks/                                ← Jupyter workspace for AI engineers
processing/                               ← Data pipeline scripts (not yet built)
```

**Read `CLAUDE.md`** for all technical decisions, data formats, and contribution conventions.

---

## Data ethics

Participant health data is not in this repository. All HRV data is pseudonymised. The `.gitignore` excludes all participant CSV files by default.
