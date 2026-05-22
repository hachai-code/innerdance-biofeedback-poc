# Innerdance POC — Refined Approach (Step 5)

**Addresses:** resilience framing, modeling-ready data, experimental design, self-administered protocol  
**Date:** 2026-05-19

---

## 1. Resilience, Not Relaxation — Updating the Framing

Innerdance co-stimulates SNS and PNS in sequence. The source materials describe it clearly: sessions begin with activation (body shaking, emotional arousal, SNS engagement), move through a peak, then transition into deep rest and integration (PNS dominance, peacefulness, restedness). The value is not the rest state alone — it is the **range traversed** and the **speed of recovery** from activation back to baseline or below.

This is **autonomic flexibility**: the trained capacity to move between arousal states and return efficiently. It is the physiological definition of stress resilience.

**What changes in the hypotheses:**

| Previous framing | Resilience framing |
|------------------|--------------------|
| Post-session RMSSD > pre-session | RMSSD trajectory follows activation → recovery arc within session |
| RMSSD goes up | RMSSD range (max − min) within session widens over weeks |
| Stress goes down | Recovery speed after activation improves over sessions |
| Relaxation | Autonomic flexibility |

### Updated and added hypotheses

**H1 (revised) — The arc exists**
> Within a single session, RMSSD follows a characteristic trajectory: an initial suppression phase (SNS activation, first 15–30 min) followed by a recovery-and-overshoot phase (PNS rebound, final 30 min) relative to the pre-session baseline.

Test: Plot per-session RMSSD curve (5-min rolling window). Visually confirm arc exists before any statistics. Statistical test: compare first-third-of-session mean RMSSD vs last-third-of-session mean RMSSD — paired comparison per session.

**H2 (unchanged)** — Morning RMSSD higher on days after sessions than rest days.

**H3 (revised) — Flexibility grows over time**
> The intra-session RMSSD range (max − min rolling-window RMSSD) increases across sessions 1 → 14, reflecting growing autonomic flexibility rather than just a fixed relaxation effect.

Test: Linear regression: session_number → intra-session RMSSD range, per participant.  
*This distinguishes innerdance from a standard relaxation protocol — relaxation flattens variability, resilience training amplifies it.*

**H4 (unchanged)** — Daily RMSSD correlates with same-day perceived stress.

**H5 (revised) — Activation precedes recovery**
> Segments of the session with high acoustic energy / fast tempo (activation phase) are followed — with a lag of 10–30 min — by higher RMSSD than at the session start, not lower.

Test: Tag session into activation (first half) and integration (second half) by audio energy. Compare pre-session RMSSD vs integration-phase RMSSD. If integration RMSSD > pre-session: the activation drove a rebound, not just a return to baseline.  
*This directly tests the resilience mechanism: stress exposure → stronger recovery.*

**H6 (new) — Resilience generalises to daily life**
> After 14 days of regular sessions, the day-to-day variability of morning RMSSD (SD of morning RMSSD across the 14 days) is higher than in the first 3 baseline days — reflecting a more flexible, reactive ANS.

Test: SD of morning RMSSD in baseline period vs SD in final week. Larger SD = more flexible = better ANS responsiveness, not pathological instability.  
*Counterintuitive but important: the goal is NOT a uniformly high RMSSD. The goal is a system that moves appropriately.*

---

## 2. Making Data Collection Modeling-Ready from Day 1

The principle: **collect raw, label richly, process later.** Every modeling approach from step3 requires only two things: a raw R-R series and a timestamped audio file. Collect those and you can run any analysis in the future. Do not pre-aggregate.

### Minimum data schema (per session)

```
session/
  {participant_id}_{date}_{session_number}/
    rr_intervals.csv          # raw R-R in ms, one per row, with timestamp
    audio.m4a (or .mp3)       # the actual audio played, full session
    self_report.json          # structured: pre_stress, post_stress, pre_energy, post_energy, notes
    metadata.json             # start_time_utc, duration_min, sync_offset_sec, session_type
```

**Why raw R-R and not RMSSD:** RMSSD, HF power, SD1, and every future metric you might want is computed from raw R-R. If you store only RMSSD you cannot recompute anything else. Polar H10 exports raw R-R — use that file directly.

**Why the actual audio and not just acoustic features:** Feature extraction methods will improve. If you store features only (librosa 2026 settings) you cannot re-extract with a better tool in 2027. Store the source file.

**Sync protocol (critical):** The R-R timestamp and audio timestamp must align. Simple method:
1. Participant starts Polar recording first.
2. Participant plays 3 loud handclaps into the room before starting the audio session.
3. The clap appears as a sharp R-R artifact AND as a transient in the audio waveform.
4. Alignment offset is computed from this shared event. This is a 1-minute step that makes every dataset usable.

**Self-report schema (always the same, never change it mid-study):**

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

Four numbers and one optional text field. A participant fills this in 2 minutes. Consistent schema means it is immediately joinable to any model's feature set.

**Within-participant normalization:** On days 1–3, collect 3 resting baseline RMSSD readings (no session, just 5 min seated). This becomes each participant's personal baseline. All subsequent RMSSD values are expressed as % of personal baseline. This handles the large between-person variability and makes participant data poolable.

---

## 3. Experimental Design: Comparison Conditions

Measuring only the treatment tells you the signal exists. Measuring against a comparator tells you it is the treatment that caused it.

### Minimum viable comparator set (per participant over 14 days)

| Condition | Sessions | Purpose |
|-----------|----------|---------|
| **A: Innerdance session** | ~8–10 sessions | The treatment |
| **B: Passive rest** (same duration, silence or white noise) | 2–3 sessions | Controls for "sitting quietly" effect |
| **C: Activating music** (fast tempo >120 BPM, energetic playlist) | 1–2 sessions | Controls for "music in general" effect; should NOT produce the arc |

**Session assignment:** Do not randomize within the same week. Run 3 baseline days (condition B, morning RMSSD only), then alternate A and B across weeks 1–2, with 1–2 condition C sessions placed in week 2 after H1 is confirmed.

**Why condition C matters:** If activating music also produces a post-session RMSSD increase, the effect is "music in general" not innerdance specifically. If only condition A produces the activation → rebound arc, that is a mechanistically specific result. This distinction is what the medical community will ask about.

### Within-session parameter experiments (Stream A compatible, no extra burden)

Once you have 5+ sessions per participant, you can start varying one parameter per session:

| Parameter | Low variant | High variant | Sessions needed |
|-----------|------------|--------------|-----------------|
| Session duration | 30 min | 60 min | 2 sessions each |
| Tempo arc | Always slow (≤70 BPM) | Activation first (>120 BPM) → slow | 2 sessions each |
| Silence proportion | High (>30% silence) | Low (<5% silence) | 2 sessions each |

This is not a formal RCT. It is structured observation. Each variant is logged and its RMSSD arc compared descriptively. If a pattern emerges, it informs the next formal study. If no pattern: you have eliminated that parameter as a primary driver.

---

## 4. Self-Administered Protocol

No facilitator. Each participant is responsible for their own data.

### What the participant does

```
Before session:
  1. Put on Polar H10. Start recording in Polar Beat app.
  2. Sit quietly 5 min (pre-session RMSSD window). Do not start audio yet.
  3. Clap 3 times loudly (sync event). Then start audio.
  4. Fill in pre-session form (2 min, on phone).

During session:
  Nothing required. Lie down, listen.

After session:
  1. Sit quietly 5 min (post-session RMSSD window). Do not stop recording yet.
  2. Stop Polar recording. Export R-R data from Polar Beat (CSV export).
  3. Fill in post-session form (2 min).
  4. Upload: R-R CSV + audio file + form to shared folder (Google Drive or similar).
```

**Participant burden:** ~12 min overhead per session. Sessions run at participant's own time and location.

**Audio source options (participant chooses, logged in metadata):**
- Pre-recorded innerdance playlist (Spotify, provided by study)
- Own playlist matching innerdance criteria
- Live session recording (if attending a facilitator session, record the room audio on phone)

**Data quality checks (automatic, run once per upload):**
- R-R file has >90% of intervals in 400–1500 ms range (basic artefact flag)
- Audio duration and R-R duration differ by <2 min (sync sanity check)
- Self-report fields are complete

A simple Python script (20 lines) can run these checks and email a pass/fail confirmation to the participant within minutes of upload.

### App roadmap (do not build until data pipeline is proven)

```
Phase 0 (now):    Polar Beat export + Google Drive upload + Google Form
Phase 1 (month 2): Simple web form that accepts file upload + validates on submission
Phase 2 (month 4): Mobile app: records audio + triggers Polar export + self-report in one flow
Phase 3 (month 6): Integrated Polar SDK + live RMSSD dashboard for participant
```

Build Phase 0 first. Do not invest in Phase 1 until you have confirmed that participants actually comply with Phase 0 for at least 2 weeks.

---

## 5. What This Gives You for Modeling Later

By following this protocol, at the end of 14 days with 4 participants you have:

| Data asset | What it enables |
|------------|-----------------|
| Raw R-R series, timestamped | Any HRV metric derivable; ARMAX, ESN, LSTM input |
| Aligned audio files | Acoustic feature extraction at any resolution; TRF analysis |
| 3-condition comparison (A/B/C) | Causal claim: effect is specific to innerdance, not just rest or music |
| Within-person baseline normalized | Cross-participant pooling; Bayesian mixed-effects |
| Structured self-report (same schema) | H4 test; joint physiological + subjective model |
| Intra-session RMSSD arcs (H1 revised) | Training labels for session-level sequence models |
| Parameter-varied sessions | Feature importance analysis: which acoustic parameter drives the arc? |

The data collection is **model-agnostic by design.** Whatever modeling approach turns out to be most appropriate (discovered by Stream A), the raw data supports it without recollection.

---

## Summary of Changes from Step 4

| Topic | Step 4 | Step 5 |
|-------|--------|--------|
| Framing | Relaxation / RMSSD goes up | Resilience / RMSSD arc + flexibility grows |
| H1 | Simple post > pre | Activation → recovery arc |
| H3 | Dose-response | Intra-session range widens over weeks |
| H5 | Slow tempo → higher RMSSD | Activation phase → rebound overshoot |
| New H6 | — | Daily RMSSD variability increases = flexible ANS |
| Data collection | Metrics only | Raw R-R + raw audio + sync protocol |
| Experimental design | Treatment only | Treatment + passive rest + activating music |
| Protocol | Assumed facilitator | Fully self-administered with defined upload flow |
