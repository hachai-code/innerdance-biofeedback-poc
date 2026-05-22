# Innerdance POC — Pragmatic Two-Stream Approach

**Framing:** Architect-first. Build for the data you have in week 1, not the model you want in month 6.  
**Date:** 2026-05-19

---

## The honest starting point

You have 4 people, some sessions, a Polar H10, and a question.  
Before any model, you need to answer: **is there anything in this data worth modeling?**

If the signal is too noisy, too person-specific, or too confounded, no amount of ML fixes that. The first job is to look at the data with minimal assumptions and see if a pattern is visible at all. Only then do you invest in modeling it.

---

## Two streams

```
Stream A — Observe                     Stream B — Validate
(runs from day 1, never stops)         (starts after first 5 sessions)

Collect → Visualise → Describe         Pick one simple hypothesis
No model required                      Test it with the minimum viable method
Generates the questions                Act on the answer
```

These run in parallel. Stream A feeds Stream B. Stream B failure redirects Stream A's attention.

---

## Stream A: Observe and Describe

**Goal:** Understand what the HRV signal actually does during and after an innerdance session, for each person, without imposing a hypothesis.

**What you build:**
- A simple dashboard showing RMSSD (5-min rolling window) plotted against session time
- Facilitator marks events on the timeline: "sound changed here", "participant was still", "sound got louder"
- Morning RMSSD logged daily
- Self-reported stress logged daily (single number, 0–10)

**What you look for — by eye, no statistics:**
- Does RMSSD visibly rise during the session? When?
- Is the rise consistent across participants, or completely different per person?
- Does the next-morning RMSSD look different on session days vs rest days?
- Is there a participant for whom nothing changes? That is equally informative.

**What this produces even if you never run a model:**
- A data pipeline that works reliably
- Labelled session data that others can analyze
- Observable patterns that justify or redirect Stream B
- Documentation for the medical community of what the raw signal looks like

**Time to implement:** 1–2 weeks for a basic Streamlit dashboard reading from Polar H10 BLE.

---

## Stream B: Simple Hypotheses

Design principle: each hypothesis must be testable with a paired comparison or a correlation. A beginner with a spreadsheet should be able to run it. If rejected, the data collected still answers other questions.

---

### H1 — The session works (immediate effect)

> **Post-session RMSSD is higher than pre-session RMSSD.**

| Property | Detail |
|----------|--------|
| Measurement | 5-min resting RMSSD before session; 5-min resting RMSSD immediately after |
| Test | Paired t-test (or Wilcoxon if non-normal). One line of Python/R. |
| Smallest useful sample | 8 paired sessions (single participant, 8 days) |
| Medical relevance | This is the minimum claim: the session has an acute parasympathetic effect. Without this, nothing else matters. |
| If rejected | Look at H1b: does RMSSD rise *during* the session but return to baseline before the post-measurement? Check where in the session the peak occurs (Stream A). |
| If confirmed | Foundation for every other hypothesis. Proceed to H2. |

**Why this is first:** It requires no acoustic analysis, no ML, no complex stats. It is the single most important thing to establish.

---

### H2 — The effect accumulates (carry-over effect)

> **Morning RMSSD on the day after a session is higher than morning RMSSD on days without a session.**

| Property | Detail |
|----------|--------|
| Measurement | Daily 5-min morning RMSSD (Polar H10 + Kubios app, already validated for this) |
| Test | Simple group comparison: session-day-mornings vs non-session-day-mornings per participant |
| Smallest useful sample | 7 session days + 7 rest days (2 weeks) |
| Medical relevance | Establishes that the effect is not purely momentary — it persists into the next day. This is the claim that matters for health practice. |
| If rejected | The effect may be real but too brief (returns to baseline within hours). This is not failure — it tells you sessions need to be more frequent, or the protocol needs adjusting. Data from H1 + Stream A still stands. |
| If confirmed | Justifies recommending innerdance as a regular practice rather than a one-off intervention. |

---

### H3 — The effect is dose-dependent (who benefits most)

> **Participants with lower pre-session RMSSD show larger RMSSD increases post-session than participants with higher pre-session RMSSD.**

| Property | Detail |
|----------|--------|
| Measurement | Pre-session RMSSD vs post–pre delta, per session |
| Test | Scatter plot + Pearson r. Two lines of code. |
| Smallest useful sample | 15–20 paired sessions (can pool across participants if H1 is confirmed) |
| Medical relevance | "Those who need it most benefit most." This is a clinically actionable finding — it tells practitioners who to prioritise. Common pattern in vagal interventions (HRV-B literature). |
| If rejected (flat or reverse) | Either the effect is ceiling-limited (high baseline leaves less room to increase), or the intervention doesn't discriminate — both are informative for clinical targeting. |
| If confirmed | Strong argument for innerdance as a targeted intervention for high-stress / low-HRV populations, which is exactly the business professional target group. |

---

### H4 — Perceived stress and RMSSD move together (user ↔ system coherence)

> **Days with higher morning RMSSD correspond to lower self-reported stress on the same morning.**

| Property | Detail |
|----------|--------|
| Measurement | Daily RMSSD + daily stress score (0–10). Already collected if H1 and H2 are running. |
| Test | Pearson correlation per participant, then descriptive summary across 4. |
| Smallest useful sample | 14 days (already validated in Sensors 2025 study on identical design) |
| Medical relevance | Validates that the physiological signal (RMSSD) is meaningful to the person experiencing it. Without this link, you have a physiological curiosity but not a patient-relevant outcome. |
| If rejected | RMSSD is moving but the person doesn't feel it. Could mean the self-report scale is wrong, the measurement window is wrong, or the RMSSD change is too small to be subjectively perceptible. All are addressable. |
| If confirmed | Justifies using RMSSD as a proxy for subjective wellbeing in future automated systems — this is the bridge between the sensor and the user experience. |

---

### H5 — The sound structure matters (acoustic signal has an effect)

> **Sessions with more slow-tempo segments (≤ 70 BPM) show larger RMSSD increases than sessions with fewer slow-tempo segments.**

| Property | Detail |
|----------|--------|
| Measurement | Tempo tag the session audio (librosa, 1 line per session) → compute % of session below 70 BPM → correlate with RMSSD delta |
| Test | Spearman correlation: slow-tempo ratio vs post–pre RMSSD delta |
| Smallest useful sample | 10 sessions with different tempo profiles |
| Medical relevance | Identifies the first acoustic lever the facilitator can consciously control. Directly actionable: if confirmed, slow the playlist down for high-stress participants. |
| If rejected | Tempo is not the driver — look at bass energy, silence ratio, or AM depth instead (Stream A shows which acoustic features visually co-vary with RMSSD peaks). |
| Why this is last | H1–H4 do not require any acoustic analysis. H5 is the first step toward understanding mechanism, not just effect. Do not run H5 before H1 is confirmed. |

---

## What happens if all hypotheses are rejected

The data collected is still valuable:

1. **The data pipeline is built and working.** This is reusable for the next protocol iteration and for other researchers.
2. **Stream A observations stand.** Even null results for RMSSD tell you something: maybe the mechanism is not vagal tone, maybe it is EEG alpha, maybe it is cortisol. The data redirects.
3. **The self-report and acoustic logs exist.** Other researchers can apply different analyses.
4. **The null result is publishable** in the context of innerdance research — there is essentially no prior physiological study of this specific modality. A well-designed null result with n=4 is a legitimate contribution.

---

## Execution order

```
Week 1:   Set up data pipeline (Polar H10 → CSV → morning RMSSD).
          Start Stream A dashboard.
          Run first session. Plot the RMSSD curve. Look at it.

Week 2:   Enough data to test H1 (5–8 sessions).
          Run paired comparison. Record result.

Week 3-4: H2 (session vs non-session mornings).
          H4 (RMSSD vs stress correlation, daily).

Week 5-6: H3 (dose-response: who benefits most).

Week 7+:  H5 (tempo structure), only if H1 confirmed.
          Begin thinking about what a second cohort would need.
```

---

## What NOT to do yet

- Do not build a sequence model before H1 is confirmed.
- Do not compute LF/HF ratio, DFA-α1, SampEn, or non-linear metrics in the first iteration. They add noise before the basic signal is established.
- Do not pool participants before checking that H1 holds for each individual. Group averages at n=4 are meaningless; individual patterns are the finding.
- Do not pre-register a specific effect size. At n=4 the goal is direction and consistency, not magnitude.
