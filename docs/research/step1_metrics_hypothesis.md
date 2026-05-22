# Innerdance Biofeedback POC — Objective, Metrics & Hypothesis

**Project:** Validating how innerdance sound technique regulates the autonomic nervous system to improve stress resilience in business professionals  
**Stage:** Step 1 — Objective, user metric, and system metric definition  
**Date:** 2026-05-10

---

## 1. Recommended Metric Pair

### User Metric: Perceived Stress Level
A short daily self-report — either a single validated item ("How stressed did you feel today?" 0–10) or the 3-item abbreviated Perceived Stress Scale (PSS-3). Collected once in the morning and once after each innerdance session via a simple mobile form or voice memo.

**Why it matters to the user:** Business professionals already understand stress as a performance and health risk. This metric is immediately legible, requires no device literacy, and produces a number they will instinctively want to move downward. It connects directly to their stated goal: resilience under pressure.

### System Metric: Parasympathetic Tone (RMSSD from R-R Intervals)
RMSSD (Root Mean Square of Successive Differences) is derived directly and reliably from the Polar chest wrap R-R interval stream. It is the single most robust short-term HRV metric for tracking parasympathetic nervous system (PNS) activation — the "rest and digest" branch that innerdance explicitly targets.

Measured in two windows:
- **5-minute resting baseline** before each innerdance session (seated, quiet)
- **5-minute resting recovery** immediately after each session
- Optionally: **overnight RMSSD** (if participants are comfortable wearing the chest wrap during sleep — not required for the prototype)

**Why RMSSD over other HRV metrics:** RMSSD is less sensitive to breathing rate artefacts and movement than frequency-domain metrics (LF/HF ratio), which makes it appropriate for small, lightly controlled datasets. It can be computed from a 5-minute window, keeping data collection practical.

---

## 2. Rationale for the Choice

### Grounding in the innerdance mechanism
The innerdance definition describes the process as directly targeting "autonomic nervous system regulation" through modulated soundscapes that influence "arousal states, breathing rhythms, and emotional activation." The brain stem/midbrain — which controls heartbeat, breath, and thermoregulation — is explicitly identified in the source materials as the first locus of physiological change during a session: *"Feeling sudden or gradual changes in the breath and in the heart rate."*

RMSSD is a direct, non-invasive readout of the same physiological system that innerdance claims to modulate. The link between the intervention and the measurement is mechanistically sound.

### Fit with the target group
Business professionals under chronic stress show consistently suppressed HRV (low RMSSD). This creates a measurable baseline suppression that makes within-person change detectable even with small samples. They do not need to understand HRV to engage with the user metric; perceived stress is the bridge.

### Feasibility with 4 participants over 14 days
With ~1 innerdance session per participant per day, the study produces approximately:
- 56 paired (pre/post) RMSSD measurements
- 56 morning perceived stress ratings
- 56 post-session perceived stress ratings

This is sufficient for within-person (n-of-1) time-series analysis and simple cross-participant comparison. It is not sufficient for generalisable population-level conclusions — which is appropriate for a funding prototype.

### Simplicity of data collection
| Data type | Tool | Frequency | Burden |
|---|---|---|---|
| R-R intervals | Polar chest wrap | During session + 5 min before/after | Low |
| Perceived stress | 3-question form (phone) | 2× daily | Very low |
| Session log | Facilitator or auto-timestamp | Per session | None for participant |

No clinical equipment, no lab visit, no continuous 24/7 monitoring required.

### Mapping to sound adjustment
RMSSD provides a direct signal for adaptive sound control:

| RMSSD state (vs. personal baseline) | Interpretation | Sound adjustment |
|---|---|---|
| Below baseline (↓ PNS, ↑ stress) | High sympathetic activation | Shift toward lower tempo, drone bass, slow rhythm, minimal harmonic complexity |
| Near baseline | Moderate arousal | Maintain current soundscape |
| Above baseline (↑ PNS) | Deepening parasympathetic state | Can introduce more complex or emotionally evocative layers; deepen into stillness phase |

This maps directly to the innerdance playlist evolution documented in the source materials: early phases use activating sound; the practice progressively moves toward stillness, deep rest, and what participants describe as "restedness upon waking."

---

## 3. Hypothesis

**Primary hypothesis:**

> A single innerdance session (45–90 minutes of facilitator-modulated soundscape) produces a statistically significant increase in post-session RMSSD relative to pre-session baseline, and a reduction in immediately post-session perceived stress relative to pre-session report, in business professionals under habitual occupational stress.

**Secondary hypothesis:**

> Repeated innerdance sessions over 14 days produce a trend toward higher morning resting RMSSD and lower morning perceived stress compared to the participant's own pre-study baseline week (days 1–3 before regular sessions begin).

**Cause:** Modulated sound activating the brain stem / ANS regulation pathway, as described in the innerdance framework.  
**Effect:** Measurable increase in parasympathetic tone (RMSSD) and decrease in perceived stress.  
**How we know the effect has been reached:** RMSSD post-session is ≥ 10% above pre-session RMSSD for the individual (within-person threshold, validated against published HRV change benchmarks). Perceived stress rating drops by ≥ 1 point on a 0–10 scale.

**Purpose:** This is a wellness and occupational health application, not a medical claim. No therapeutic or diagnostic claim is made. The target use case is self-regulated wellbeing support, comparable to guided meditation or biofeedback-assisted relaxation. Risk level is low: the intervention is non-invasive, substance-free, and facilitated in a safe environment. Contraindications (e.g., epilepsy) should be screened at enrollment given the neurological activation patterns documented in the source materials.

---

## 4. ML Model and Optimisation Method

### Phase 1 (Prototype, weeks 1–3): Rule-Based Adaptive System

Before ML is viable, a **threshold-based adaptive rule** is the appropriate starting point given the dataset size:

```
if current_RMSSD < 0.85 × personal_baseline_RMSSD:
    activate "deep regulation" sound mode (low BPM, drone, bass-forward)
elif current_RMSSD > 1.15 × personal_baseline_RMSSD:
    activate "integration" sound mode (stillness, sparse, high-frequency textures)
else:
    maintain current mode
```

This rule is explainable, testable, and gives the facilitator a live dashboard signal. It produces labeled training data for the next phase.

### Phase 2 (Post-prototype, with growing data): Personalized Regression Model

**Method:** Linear Mixed-Effects Model (LME)

```
RMSSD_post ~ RMSSD_pre + sound_tempo + sound_bass_energy + sound_harmonic_complexity + session_number + (1 | participant_id)
```

The random effect `(1 | participant_id)` handles the small number of participants and captures individual physiological baselines. This model:
- Estimates which sound features predict the largest RMSSD increase per person
- Requires only ~56+ observations to produce meaningful coefficient estimates
- Is interpretable for the research funding narrative

**Libraries:** R (`lme4`) or Python (`statsmodels` mixed LM, `pymer4`).

### Phase 3 (With 50+ sessions per participant): Contextual Bandit / Reinforcement Learning

Once sufficient within-person data exists, a **contextual bandit model** can replace the rule-based system:

- **State:** current RMSSD (relative to personal baseline), time-in-session, session number
- **Action:** discrete sound adjustment (tempo band, bass level, harmonic density — 3–4 parameters)
- **Reward:** RMSSD change in the following 5-minute window + post-session stress rating

A simple Upper Confidence Bound (UCB) or Thompson Sampling bandit is tractable with small data and does not require a neural network. This is the architecture for a production adaptive innerdance system.

### Data infrastructure requirements (minimal viable)

| Component | Tool | Rationale |
|---|---|---|
| Raw R-R storage | SQLite or MySQL (AWS RDS t3.micro) | Structured, cheap, sufficient for prototype |
| Session metadata | Same DB, separate table | Links sound parameters to physiological windows |
| Self-report data | Google Forms → CSV or same DB | Easiest participant onboarding |
| Analysis | Python (pandas, scipy, statsmodels) or R | Researcher-friendly |
| Dashboard (Phase 1) | Streamlit or Grafana | Fast to build, shows live RMSSD + stress trend |

---

## 5. Summary

| Dimension | Choice |
|---|---|
| **User metric** | Perceived stress (0–10 VAS or PSS-3, daily) |
| **System metric** | RMSSD from Polar chest wrap R-R intervals (pre/post session) |
| **Primary hypothesis** | Single innerdance session increases RMSSD and reduces perceived stress vs. baseline |
| **Secondary hypothesis** | 14-day repeated sessions trend toward improved resting RMSSD and morning stress |
| **MVP optimisation method** | Rule-based threshold system using personal RMSSD baseline |
| **Scale-up ML method** | Linear mixed-effects model → contextual bandit RL |
| **Data collection burden** | Polar chest wrap ~2 hrs/day during session + short mobile form 2× daily |

---

*Next step: Define data collection protocol and participant-facing application design.*
