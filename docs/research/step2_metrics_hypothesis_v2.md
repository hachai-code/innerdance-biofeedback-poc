# Innerdance Biofeedback POC — Metrics, Hypotheses & ML Approaches (v2)

**Sources:** mi-05-04-00236.pdf (Gitler et al., Medicine International 2025), HRV_RR_Metrics_Wellbeing.docx, PubMed literature review, Brain.fm / Endel / SSP published and disclosed research  
**Iteration over:** step1_metrics_and_hypothesis.md  
**Date:** 2026-05-19

---

## 1. Background: What the Literature Establishes

### 1.1 The core paper (mi-05-04-00236 / Gitler et al., Medicine International 2025)

**Full citation:** Gitler A, Bar Yosef Y, Kotzer U, Levine AD. Harnessing non-invasive vagal neuromodulation: HRV biofeedback and SSP for cardiovascular and autonomic regulation. Medicine International 5: 37, 2025. DOI: 10.3892/mi.2025.236. PMC12082064.  
**Journal:** Medicine International (Spandidos Publications). Peer-reviewed narrative review.

**Key relevant findings for our project:**

- RMSSD and HF-HRV are validated short-term vagal indices; RMSSD from 5-min recordings (even 10-sec segments) reliably reflects parasympathetic tone
- HRV-B at resonance frequency (~6 breaths/min, ~0.1 Hz) produces immediate, large-scale increases in baroreflex gain measurable within a single session
- SSP (Safe and Sound Protocol) engages the ventral vagal complex via **auditory-motor circuits** — the closest published analog to innerdance's sound-regulation mechanism
- Herhaus et al. 2023 (4-week RCT, n=55): Slow-paced breathing + HRV-B significantly reduced TNF-α, increased SDNN and LF-HRV — anti-inflammatory and autonomic gains
- SDNN <70 ms post-MI = ~4× mortality risk; SDNN and RMSSD both improve within 4–8 weeks of vagal training
- SSP preliminary evidence: benefits in PTSD, ASD, anxiety; mechanism = modulation of nucleus ambiguus and dorsal vagal complex
- Future direction explicitly stated in the paper: "integrating wearable HRV monitoring, AI-driven adaptive biofeedback"

**Why this matters for innerdance:** The SSP mechanism (filtered music → auditory-vagal pathway → parasympathetic activation) is the closest studied analog to innerdance's sound regulation. Both use non-rhythmic, layered acoustic stimulation targeting the ventral vagal complex. The innerdance framework adds facilitator-modulated real-time adjustment, which this paper frames as a natural extension ("AI-driven adaptive biofeedback").

---

## 2. Top Metrics: Updated Ranking and Evidence

Based on the docx evidence table and the literature review, here is the ranked set of metrics for our specific context (Polar H10, ≤4 participants, ≤14 days, healthy stressed adults, 45-90 min sessions):

### Tier 1 — Primary metrics (use in all sessions)

| Metric | Derivation from R-R | Session signal | 2-week trend | Wellbeing outcome | Source |
|--------|-------------------|----------------|--------------|-------------------|--------|
| **RMSSD** | Direct from successive R-R differences | HIGH | MODERATE | Anxiety ↓, stress ↓, sleep quality ↑, emotional regulation ↑ | Laborde et al. 2017 (Front. Psychol.); Sensors 2025 (PMID 40732543) |
| **Mean HR** | 60/mean(RR) | HIGH | HIGH | Resting HR as daily recovery proxy; lower = more vagal tone | Task Force ESC 1996; PMC2952123 |
| **SD1 (Poincaré)** | √(RMSSD²/2) | HIGH | MODERATE | Mirrors RMSSD; adds visual session fingerprint | PLoS ONE 2016 (PMID 26745621) |

**New addition vs. v1:** Mean HR elevated to primary tier. The Sensors 2025 study (n=41, 14 days, Polar H10, Bayesian mixed-effects) found RMSSD significantly associated with self-reported sleep (β=0.510), fatigue (β=0.281), and stress (β=0.353) — this is our exact study design validated on the same sensor.

### Tier 2 — Secondary metrics (add from session 3+)

| Metric | Derivation from R-R | Session signal | Wellbeing outcome | Key caveat |
|--------|-------------------|----------------|-------------------|------------|
| **HF Power (0.15–0.40 Hz)** | FFT of R-R series | SESSION | Relaxation ↑, anxiety ↓, PTSD improvement | Highly breathing-rate dependent; confounded if participant breathes <9 bpm |
| **SD1/SD2 ratio** | Poincaré geometry | HIGH | Sympathovagal balance direction indicator | Reliable session trend; resting baseline needs 2–4 weeks |
| **LF/HF ratio** | FFT | SESSION | Vagal dominance trend (use as within-person trend only) | NOT a sympathetic marker; meaningful only as personal relative change |
| **RSA amplitude** | Peak-valley HR swing | SESSION | Most valid vagal index during slow/deep breathing — where RMSSD is invalid | Requires parallel respiration tracking or known breathing rate |

**Critical note on RMSSD validity:** The AJP-Regu 2022 paper (doi:10.1152/ajpregu.00272.2022) explicitly states RMSSD is NOT valid during slow deep breathing. Innerdance sessions often guide participants toward slow breath. **Recommendation: measure RMSSD only in the 5-minute standardized window before/after sessions (controlled normal breathing), not during the session itself. Use RSA amplitude or HF power as the within-session real-time signal.**

### Tier 3 — 4–8 week markers (not early signal)

| Metric | Signal timeline | Wellbeing outcome |
|--------|----------------|-------------------|
| **SDNN** | 4–8 weeks | All-cause mortality risk ↓, cardiovascular resilience, emotional wellbeing (GDS correlation) |
| **DFA α1** | 4+ weeks | Fractal regulatory complexity; cardiovascular risk prediction |
| **SampEn** | 4+ weeks | Psychopathology discriminator; chronic stress reduction |
| **SD2** | 4–8 weeks | Cumulative autonomic flexibility gain |

---

## 3. Recommended Metric Pairs: User ↔ System

### Primary pair (prototype, weeks 1–2)

| | Metric | Measurement | Timing |
|--|--------|------------|--------|
| **User metric** | Perceived stress (PSS-3, 0–10 VAS) + Subjective energy/recovery (0–10) | Short mobile form | Morning + post-session |
| **System metric** | RMSSD (5-min standardized baseline) + Mean HR | Polar H10 R-R | 5 min pre-session (resting, seated) + 5 min post-session |

### Secondary pair (add from week 2)

| | Metric | Measurement | Timing |
|--|--------|------------|--------|
| **User metric** | Sleep quality (0–5 morning rating, single item) | Mobile form | Each morning |
| **System metric** | HF power + RSA amplitude | Polar H10 R-R | During session (5-min windows every 15 min) |

**Rationale for sleep quality as secondary:** The innerdance "History of the Playlist" (2022 phase) explicitly documents "restedness upon waking," "states of continuous dreaming," and "changes in metabolism and immunity." Overnight RMSSD is a validated sleep quality predictor. If participants can wear the Polar H10 during sleep (chest strap tolerable for several hours), this adds a high-value metric aligned with innerdance's documented outcomes.

---

## 4. Updated Hypotheses

### Hypothesis 1 (Primary — acute, single session)
> A single innerdance session of 45–90 minutes produces a statistically significant increase in post-session RMSSD relative to pre-session baseline (expected direction: ≥10% within-person increase), and a reduction of ≥1 point on a 0–10 perceived stress VAS, in business professionals under habitual occupational stress.

**Mechanism (from source literature):** Innerdance's layered soundscape activates the ventral vagal complex via auditory-motor circuits (homologous to SSP mechanism, Gitler et al. 2025). The sound guides the listener toward slow respiratory rhythms, increasing RSA and parasympathetic dominance, measurable as RMSSD and HF-HRV increase.

**Timeframe for signal:** Within single session and within 30 min post-session. High confidence based on SSP and HRV-B literature showing session-level HRV shifts (Herhaus et al. 2023, Lehrer 2020).

---

### Hypothesis 2 (Secondary — cumulative, 14 days)
> Repeated innerdance sessions over 14 days (≥5 sessions) produce a statistically significant trend toward higher morning resting RMSSD and lower morning perceived stress, compared to the participant's own days 1–3 baseline (pre-intervention).

**Mechanism:** Repeated vagal activation builds baroreflex sensitivity and autonomic flexibility over time (Lehrer & Gevirtz 2014; Herhaus et al. 2023 4-week RCT). The innerdance framework's progressive deepening over multiple sessions (documented in playlist evolution: from emotional activation → morphing of consciousness → deep peacefulness) mirrors the autonomic training arc of HRV-B protocols.

**Timeframe:** Trend detectable in 2 weeks; statistically powered signal at 4–8 weeks. Given n=4, use within-person Bayesian mixed-effects model rather than frequentist p-value.

---

### Hypothesis 3 (New vs. v1 — sound-response coupling)
> Within-session HF power and RSA amplitude co-vary with identifiable acoustic features of the sound (specifically: tempo ≤80 BPM, bass energy dominance, slow amplitude modulation rate), such that a personalized acoustic-to-HRV mapping can be learned per individual.

**Mechanism grounding:** Scientific Reports 2017 (PMC5339732): sound stimuli at tempo ≤60 BPM increase parasympathetic activity; Bretherton et al. 2019 (Music Perception): controlled tempo reductions produce measurable HRV increases. PLOS ONE 2015 (PMC4540583): sympathetic activation by high tempo requires co-occurrence of fast breathing — i.e., slow sound + natural breathing = parasympathetic shift.

**Timeframe:** Detectable within 2–4 sessions per individual if acoustic feature logging is implemented.

---

## 5. Literature Review: ML and Computational Approaches

### 5.1 Direct studies linking acoustic features to HRV / ANS

| Study | Source | N | Acoustic features | HRV metric | Method | Key finding | Reliability |
|-------|--------|---|------------------|------------|--------|-------------|-------------|
| Nozaradan et al., acoustic tempo → HR interaction | Sci. Reports 2017, PMC5339732 | 20 | Tempo (BPM) | Mean HR, HF-HRV | ANOVA, linear regression | Tempo at subject basal HR → HR coupling; below basal → parasympathetic activation | Nature Publishing Group ★★★★ |
| Bretherton et al. 2019 | Music Perception (SAGE) | 20 | Tempo gradient (controlled decrease from 140→60 BPM) | RMSSD, HF, LF/HF | Repeated-measures ANOVA | Tempo decrease to 60 BPM → significant RMSSD increase, LF/HF decrease | Peer-reviewed ★★★ |
| Sympathetic tone + high tempo | PLoS ONE 2015, PMC4540583 | 40 | Tempo (60 vs 80 BPM), respiratory coupling | Mean HR, LF/HF | 2×2 factorial | Sympathetic effect requires BOTH fast tempo AND fast breathing — slow tempo + natural breathing = safe for parasympathetic target | PLoS ONE ★★★★ |
| GAN biofeedback: HMI → HRV | Biomedical Signal Processing and Control, ScienceDirect 2021 | Simulation | Harmonic musical intervals (frequency ratios) | HRV time series | 1D GAN (two generators: HRV + sound) | GAN learned association between HMI acoustic stimuli and HRV response; real-time bidirectional coupling demonstrated in simulation | ScienceDirect/Elsevier ★★★ |
| Generating EEG from acoustic features | arXiv 2020 (Shen et al.) | Varies | MFCC, chroma, spectral centroid, tempo | EEG alpha/beta power | CNN encoder-decoder | Acoustic features can be used to predict EEG spectral features — provides indirect route to HRV via EEG | Preprint ★★ |

### 5.2 HRV prediction from physiological + contextual features (ML)

| Study | Source | N | Features | Output | Method | Key finding | Reliability |
|-------|--------|---|----------|--------|--------|-------------|-------------|
| HRV stress detection wearables | PMC8072791 (Sensors 2021) | 15 | RMSSD, SDNN, LF/HF, pNN50 | Stress binary/level | Random Forest, SVM, XGBoost | RF achieves ~80% accuracy stress classification; RMSSD most discriminative | MDPI Sensors ★★★ |
| PPG-based HRV + ML real-time stress | PMC11970940 (APL Bioengineering 2025) | 31 | RMSSD, LF/HF, SD1 from PPG | Continuous stress score | LSTM + attention | Real-time stress quantification with <2s latency | AIP Publishing ★★★★ |
| Daily HRV ↔ self-reported wellness (Polar H10, 14 days) | Sensors 2025, PMC12300306, PMID 40732543 | **41** | RMSSD (5-min morning, Polar H10) | Sleep, fatigue, stress (self-report) | **Bayesian ordinal mixed-effects** | RMSSD predicts same-day stress (β=0.353), sleep (β=0.510), fatigue (β=0.281); substantial individual variability | MDPI Sensors ★★★★ **Most directly relevant to our design** |
| LLM + HRV real-time interpretation | PMC12512671 (2025) | Pilot | RMSSD, HR, HF from Polar-like sensors | Physiological state narrative | HRV → LLM pipeline | Modular pipeline for biomarker-to-language state interpretation; directly applicable to facilitator dashboard | PubMed Central ★★★ |

### 5.3 Brain.fm, Endel, SSP — disclosed research

| Company/Protocol | Published evidence | Method disclosed | Reliability |
|--|--|--|--|
| **Brain.fm** | Woods et al. 2024, *Communications Biology* (Nature Publishing Group), PMID 39443657 | Amplitude modulation of music tracks → neural phase-locking; EEG beta increase (12–20 Hz); amplitude-modulated music vs. control music vs. pink noise; fMRI + EEG multi-experiment | ★★★★★ Peer-reviewed in Nature portfolio |
| **Brain.fm** | Internal EEG sleep study (Hewett, disclosed on brain.fm/pdfs) | EEG delta/theta during sleep session vs. playlist; proprietary | ★★ Disclosed but not peer-reviewed |
| **Endel** | Arctop EEG study 2022 (disclosed, not peer-reviewed) | EEG engagement score during Endel vs. silence vs. playlists; 7× better focus claimed | ★★ Proprietary claim; not independently peer-reviewed |
| **Endel** | Stress reduction claim: 3.6× reduction | Method not publicly disclosed in peer-reviewed form | ★ Marketing claim |
| **SSP (Safe and Sound Protocol)** | Gitler et al. 2025 (mi-05-04-00236) review; Kishimoto et al. 2023; Kawai et al. 2023 | Filtered music (high-pass filtered human voice prosody) targets middle-ear stapedius muscle → auditory-vagal arc → ventral vagal complex; preliminary RCTs in ASD, PTSD | ★★★ Preliminary but peer-reviewed |
| **HRV-B (Lehrer et al.)** | Lehrer & Gevirtz 2014 meta-analysis; Herhaus et al. 2023 RCT | Resonance frequency breathing (5–6 bpm) + real-time HRV feedback; SDNN, LF, RMSSD measured; gold standard protocol | ★★★★★ Extensive peer-reviewed evidence |

---

## 6. ML Approaches: Evaluation for Our Context

Given: ≤4 participants × ≤14 days × ~1 session/day = ~56 session observations. Possible additional fine-grained window data: ~50–100 5-minute HRV windows per session = up to ~2800–5600 individual measurements if windowed.

### Approach A: Bayesian Hierarchical Mixed-Effects Model

**What it is:** Bayesian ordinal or linear mixed-effects model. State = RMSSD / HF power. Predictor = acoustic features logged per time window (tempo, bass energy, amplitude modulation rate). Random effect = participant.

**Why it fits:**
- Directly validated on our exact design (Sensors 2025, n=41, Polar H10, 14 days, Bayesian mixed-effects)
- Handles small N naturally through prior distributions and partial pooling
- Produces credible intervals (not just p-values) — more honest for n=4
- Interpretable: "bass-dominant, slow-tempo windows predict +X ms RMSSD increase"
- Framework: R (brms + lme4) or Python (PyMC, bambi)

**Why not:**
- Requires clean acoustic feature logging (tempo, bass RMS, AM rate per time window) — needs audio pipeline
- Assumes linear relationship (may miss non-linear coupling)
- No real-time prediction capability

**What is required:**
- Session audio logged with timestamps
- Librosa or Essentia for acoustic feature extraction per 30-sec window
- Kubios or pyHRV for RR → RMSSD per matching window
- ~2 weeks to implement; ~1 week to analyze per participant

**Source reliability:** ★★★★★ Sensors 2025 uses this exact approach on our sensor

---

### Approach B: Personalized Threshold / Rule-Based System (MVP)

**What it is:** Per-participant baseline RMSSD computed from days 1–3. Live comparison: current RMSSD vs. personal baseline. Acoustic adjustment triggered by threshold crossing.

**Why it fits:**
- Requires zero ML training data
- Immediately deployable in session 1
- Directly grounded in HRV-B protocol logic (Lehrer et al.)
- Produces labeled training data for Approach A
- Clinically interpretable and safe

**Why not:**
- Not adaptive to individual response patterns (same threshold for everyone)
- Does not learn from session to session
- No acoustic feature modeling — facilitator still makes sound choices intuitively

**What is required:**
- Polar H10 + real-time R-R streaming (Polar SDK or BLE)
- Simple dashboard (Streamlit): live RMSSD vs. baseline bar + alert
- 1 person, ~2 days to implement

**Source reliability:** ★★★★★ Standard HRV-B clinical practice

---

### Approach C: Within-Person Time Series Regression (per participant)

**What it is:** For each participant separately, fit a linear regression: RMSSD(t+1) ~ acoustic_features(t) + RMSSD(t). One model per person, learned across their 14-day session series.

**Why it fits:**
- Fully personalized: captures individual acoustic response profiles
- Works with ~56–100 observations per person (adequate for ~5–10 features)
- Directly tests Hypothesis 3: does sound predict HRV for this individual?
- Produces interpretable coefficients per person

**Why not:**
- Cannot generalize across participants (4 separate models)
- Assumes RMSSD is stationary within participant across 14 days (may not hold)
- Requires more acoustic feature engineering effort

**What is required:**
- Audio logging + feature extraction (librosa: tempo, spectral centroid, bass energy, AM depth)
- pandas + statsmodels for OLS
- Participant-by-participant analysis workflow

**Source reliability:** ★★★★ Standard econometric/psychophysiology approach; N-of-1 design validated in clinical HRV research

---

### Approach D: GAN / Generative Model (HRV ↔ Sound bidirectional)

**What it is:** Based on Fuentes & Pérez-Meana (ScienceDirect 2021): train a 1D GAN where one generator maps HRV → ideal acoustic interval, and another maps acoustic features → predicted HRV response.

**Why it fits:**
- Most ambitious approach; directly closes the feedback loop
- The ScienceDirect 2021 paper demonstrates feasibility in simulation
- Long-term goal: system that generates sound from real-time RMSSD state

**Why not:**
- Requires substantially more data than 56 sessions (minimum ~200–500 samples for a GAN to train non-trivially)
- The 2021 paper used simulated HRV — real-world coupling is noisier
- High implementation complexity: audio synthesis + real-time HRV + GAN inference

**What is required:**
- PyTorch or TensorFlow
- Pre-trained audio synthesis model (could start with parameter mapping rather than waveform generation)
- At minimum 6 months of data collection before meaningful training
- Research collaboration or grant-funded development

**Source reliability:** ★★★ Simulation proof-of-concept, not validated in live participants

---

### Approach E: Contextual Bandit / Reinforcement Learning

**What it is:** State = (RMSSD relative to baseline, time-in-session, session number). Action = discrete sound adjustment (tempo band, bass level, AM rate — 3–4 parameters). Reward = RMSSD change in next 5-min window + next-morning stress rating.

**Why it fits:**
- Learns optimal real-time sound adjustments across sessions
- Thompson Sampling or UCB handles exploration with sparse data
- Scales naturally as more sessions accumulate
- Directly aligns with the project goal: adaptive sound optimization

**Why not:**
- Requires a minimum of ~20–30 action-reward cycles to start converging (feasible at 1 session/day over 14 days if intra-session sampling is used)
- Action space must be discretized carefully (too many actions = too slow to converge)
- Needs human facilitator buy-in: system recommends; facilitator executes

**What is required:**
- Real-time RMSSD pipeline (Polar SDK → pyHRV → Streamlit)
- Bandit library: `vowpalwabbit` or custom Thompson Sampling in ~100 lines
- Facilitator interface: show current RMSSD + recommended next sound action
- 3–4 weeks to implement; starts learning from session 1

**Source reliability:** ★★★★ Contextual bandits validated for adaptive health interventions (general); not yet published specifically for music-HRV coupling

---

## 7. Recommended Implementation Sequence

| Phase | Timeline | Approach | Deliverable |
|-------|----------|----------|-------------|
| **Phase 0** | Week 1 | Approach B (threshold rule) | Live RMSSD dashboard, session logging, participant onboarding |
| **Phase 1** | Weeks 1–4 | Approach C (within-person regression) | Per-participant acoustic-feature → RMSSD model; identifies top predictive acoustic features |
| **Phase 2** | Weeks 2–14 | Approach A (Bayesian hierarchical) | Cross-participant model; publishable; funding-ready evidence |
| **Phase 3** | Month 3+ | Approach E (contextual bandit) | Adaptive real-time sound adjustment; prototype for app |
| **Phase 4** | Month 6+ | Approach D (GAN/generative) | Full closed-loop synthesis; requires research funding |

---

## 8. Top Acoustic Features to Extract

Based on what has been empirically linked to HRV/ANS response in the literature:

| Feature | Extraction tool | Why relevant |
|---------|---------------|--------------|
| **Tempo (BPM)** | librosa.beat.tempo | Most studied; ≤60 BPM → parasympathetic; >120 BPM → sympathetic (PMC5339732, PMC4540583) |
| **Bass energy (RMS 20–250 Hz)** | librosa.feature.rms (filtered) | Low-frequency rumble in innerdance playlists; postulated ventral vagal effect |
| **Amplitude modulation (AM) rate** | Hilbert transform envelope | Brain.fm's key patented feature; neural phase-locking to AM rate (Woods et al. 2024) |
| **Spectral centroid** | librosa.feature.spectral_centroid | Timbre brightness; high centroid = alerting, low = calming |
| **Zero-crossing rate** | librosa.feature.zero_crossing_rate | Roughness / harmonic complexity proxy |
| **Onset density** | librosa.onset.onset_detect | Event rate; higher = more activating |
| **Silence ratio** | Threshold on RMS envelope | Innerdance uses silence as an active regulatory tool (documented in source) |
| **Harmonic-to-noise ratio** | librosa.effects.harmonic | Consonance vs dissonance; harmonicity linked to social engagement system |

Extraction pipeline: 30-second sliding windows, 50% overlap. Merge with HRV windows by timestamp. Store in structured DB (session_id, window_start_ts, acoustic_features[], hrv_metrics[]).

---

## 9. Summary: Top 5 Metric-Hypothesis-Model Combinations

| Rank | User metric | System metric | Hypothesis | Model | Earliest signal | Evidence source |
|------|-------------|--------------|------------|-------|----------------|-----------------|
| 1 | Perceived stress (PSS-3) | RMSSD (5-min resting, pre/post) | Single session ↑ RMSSD, ↓ stress | Bayesian mixed-effects | Session 1 | Sensors 2025 (Polar H10, n=41, 14d) ★★★★★ |
| 2 | Sleep quality (morning 0–5) | Morning RMSSD (overnight or 5-min morning) | 14-day trend ↑ RMSSD, ↑ sleep quality | Same model + lagged correlation | Week 2 | Sensors 2025 (β=0.510 sleep-RMSSD) ★★★★★ |
| 3 | Subjective energy (0–10) | Mean HR + SD1 during session | Sessions reduce resting HR trend over 14 days | Within-person OLS regression | Week 1–2 | Task Force 1996; multiple HRV-B RCTs ★★★★ |
| 4 | (No self-report needed) | HF power / RSA amplitude during session | Sound tempo ≤60 BPM window predicts HF-HRV increase within 5 min | Within-person time series regression | Session 2–3 | PMC5339732, Bretherton 2019, PMC4540583 ★★★★ |
| 5 | Cognitive performance (optional: Stroop task, 3 min) | RMSSD pre-session | Pre-session RMSSD predicts within-session cognitive performance | Linear regression | Baseline session | Neurovisceral integration model (Thayer & Lane); multiple RCTs ★★★★ |

---

## 10. Key Limitations and Risks

1. **n=4 is pre-statistical**: No frequentist test will be adequately powered. Frame all results as case series / proof-of-concept with Bayesian credible intervals or effect sizes. This is appropriate and honest for funding purposes.
2. **RMSSD validity during slow breathing**: Do NOT use RMSSD as real-time in-session signal. Use HF power or RSA amplitude during sessions; reserve RMSSD for pre/post standardized windows.
3. **Individual variability is large**: The Sensors 2025 study (same design) found substantial individual variability even with β>0 group effects. Within-person models are more informative than group averages at n=4.
4. **Acoustic feature logging is the bottleneck**: Without timestamped audio logs, Hypotheses 3 cannot be tested. This infrastructure must be built before sessions begin.
5. **SSP analogy is plausible but not proven for innerdance**: The SSP and innerdance mechanisms are analogous (auditory → ventral vagal) but innerdance is not filtered voice prosody — it is a broader frequency and layering approach. The mapping is conceptually valid but requires original data.
6. **Innerdance is not a clinical intervention**: All wellness claims should be framed as observational wellbeing effects, not therapeutic efficacy, to manage regulatory risk.

---

*Next step (Step 2 full): Define data collection protocol, session structure, Polar H10 streaming setup, acoustic feature logging pipeline, and participant onboarding.*

---

## References (key, cited above)

- Gitler et al. (2025). Medicine International 5:37. DOI: 10.3892/mi.2025.236. PMC12082064
- Sensors 2025, PMC12300306, PMID 40732543 — Daily HRV ↔ wellbeing, Polar H10, 14 days, Bayesian
- Laborde, Mosley & Thayer (2017). Front. Psychol. 8:213. PMID 28265249
- Task Force ESC/NASPE (1996). Circulation 93:1043
- Schaffarczyk et al. (2022). Sensors 22:6536. PMID 36081005 — Polar H10 validity
- Woods et al. (2024). Communications Biology 7:1376 — Brain.fm amplitude modulation, Nature portfolio
- Nozaradan et al. / PMC5339732 — Acoustic tempo → HR interaction, Scientific Reports 2017
- PLOS ONE 2015, PMC4540583 — Sympathetic tone + high tempo requires fast respiration
- Bretherton et al. (2019). Music Perception (SAGE) — Controlled tempo → cardiovascular autonomic function
- Fuentes & Pérez-Meana (2021). Biomedical Signal Processing and Control (ScienceDirect) — GAN HMI ↔ HRV
- Herhaus et al. (2023) — SPB + HRV-B RCT, TNF-α + HRV outcomes
- Lehrer & Gevirtz (2014) — HRV-B meta-analysis
- AJP-Regu 2022, doi:10.1152/ajpregu.00272.2022 — RMSSD invalid during slow breathing
- PMC7438833 — SampEn under stress, Front. Physiol. 2020
- PMC5974559 — DFA-α1 + SampEn internalising psychopathology discriminators, 2018
