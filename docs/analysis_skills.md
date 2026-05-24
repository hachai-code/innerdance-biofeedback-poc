# Analysis Skills — Compressed Technical Reference

This document captures the analysis methods, code patterns, and domain constraints used to produce the innerdance HTML report. Use it as a starting point when extending or replicating the analysis in a new environment.

---

## 1. HRV Pipeline

### Loading Polar H10 ECG data

```python
import pandas as pd, numpy as np

def load_rr(file_path, col_time="time", col_rr="rr"):
    df = pd.read_csv(file_path)
    df["t_sec"] = (df[col_time] - df[col_time].iloc[0]) / 1e9  # ns → sec
    rr = df.dropna(subset=[col_rr]).copy()
    # Physiological range filter
    rr = rr[(rr[col_rr] > 300) & (rr[col_rr] < 2000)]
    # Artefact filter: reject beats >20% from rolling median
    rolling_med = rr[col_rr].rolling(5, center=True, min_periods=1).median()
    deviation = (rr[col_rr] - rolling_med).abs() / rolling_med
    rr = rr[deviation <= 0.20].reset_index(drop=True)
    return rr["t_sec"].values, rr[col_rr].values
```

**Polar Beat format** (different column names):
```python
col_time="UNIX Timestamp", col_rr="RR"
```

### Computing RMSSD in a time window

```python
def rmssd_in_window(t, rr, t0, t1):
    mask = (t >= t0) & (t < t1)
    rw = rr[mask]
    if len(rw) < 6:
        return np.nan
    return float(np.sqrt(np.mean(np.diff(rw)**2)))
```

**CRITICAL CONSTRAINT:** RMSSD is only valid during controlled (resting) breathing. Do NOT compute RMSSD during innerdance sessions where participants breathe slowly (<9 bpm). Use SD2 and DFA α1 instead.
*(Source: AJP-Regu 2022, doi:10.1152/ajpregu.00272.2022)*

### Poincaré metrics (SD1, SD2, ratio)

```python
def poincare_metrics(rr):
    sd1   = np.sqrt(0.5 * np.mean(np.diff(rr)**2))
    sdnn  = np.std(rr, ddof=1)
    sd2   = np.sqrt(max(2*sdnn**2 - 0.5*np.mean(np.diff(rr)**2), 0))
    ratio = sd1/sd2 if sd2 > 0 else np.nan
    return sd1, sd2, ratio
```

- **SD1** = short-term variability (beat-to-beat, parasympathetic)
- **SD2** = long-term variability (total autonomic flexibility) — valid during slow breathing
- **SD1/SD2 ratio** = sympathovagal balance (high = PNS dominant, low = SNS dominant)

### DFA α1 (nonlinear regulatory integrity)

```python
def dfa_alpha1(rr, n_min=4, n_max=16):
    N = len(rr)
    if N < n_max * 4:
        return np.nan
    y = np.cumsum(rr - np.mean(rr))
    ns, F = [], []
    for n in range(n_min, n_max + 1):
        nb = N // n
        if nb < 2: continue
        segs = y[:nb*n].reshape(nb, n)
        x = np.arange(n)
        fl = [np.mean((s - np.polyval(np.polyfit(x, s, 1), x))**2) for s in segs]
        ns.append(n); F.append(np.sqrt(np.mean(fl)))
    if len(F) < 4:
        return np.nan
    return float(np.polyfit(np.log(ns), np.log(F), 1)[0])
```

- **α1 > 1.0**: long-range correlations, deep rest/sleep
- **α1 ~ 0.75–1.0**: healthy autonomic regulation
- **α1 < 0.75**: activation zone (SNS engagement or pathology)
- **Ambiguity:** slow breathing and SNS activation both drive α1 lower — a breathing belt resolves this

---

## 2. Acoustic Feature Extraction

### The 6 features used (and why tempo was dropped)

Tempo (BPM) was computed but returned a uniform 117–129 BPM across all tracks regardless of actual rhythmic structure. This is a known librosa artefact with ambient/drone music that has no clear beat grid. Tempo was **excluded** from the qualitative model; the 6 retained features are:

```python
import librosa, scipy.signal, numpy as np

def extract_audio_features(audio_path, duration=None, sr=22050):
    max_dur = min(duration or 600, 600)
    y, sr = librosa.load(audio_path, sr=sr, duration=max_dur, mono=True)

    # 1. Overall Energy (RMS) — loudness/intensity
    rms = float(np.sqrt(np.mean(y**2)))

    # 2. Bass Energy (20–250 Hz RMS) — somatic vibration
    sos_bass = scipy.signal.butter(4, [20, 250], btype="bandpass", fs=sr, output="sos")
    y_bass = scipy.signal.sosfilt(sos_bass, y)
    bass_rms = float(np.sqrt(np.mean(y_bass**2)))

    # 3. Tonal Brightness (spectral centroid Hz) — high = bright/sharp, low = dark/warm
    centroid = librosa.feature.spectral_centroid(y=y, sr=sr)
    spec_cent = float(np.mean(centroid))

    # 4. AM Depth (Hilbert envelope CV) — amplitude modulation / pulse quality
    #    High = waves/pulses; Low = flat drone
    envelope = np.abs(scipy.signal.hilbert(y))
    sos_env = scipy.signal.butter(2, 2.0, btype="low", fs=sr, output="sos")
    env_s = scipy.signal.sosfilt(sos_env, envelope)
    am_depth = float(np.std(env_s) / (np.mean(env_s) + 1e-10))

    # 5. Onset Strength (mean onset detection envelope) — activity/transient density
    oenv = librosa.onset.onset_strength(y=y, sr=sr)
    onset_mean = float(np.mean(oenv))

    # 6. Rhythm Clarity (onset CV = std/mean) — clear beats vs continuous drone
    #    High CV = distinct beats with silence between them
    #    Low CV = continuous/ambient, no rhythmic structure
    onset_cv = float(np.std(oenv) / (np.mean(oenv) + 1e-10))

    return {
        "rms_energy": rms,
        "bass_energy": bass_rms,
        "spec_centroid_hz": spec_cent,
        "am_depth": am_depth,
        "onset_strength": onset_mean,
        "onset_cv": onset_cv,
    }
```

### Qualitative categorisation (Low / Medium / High)

Features are normalised across the set of tracks using 33rd/67th percentile thresholds:

```python
def categorize(value, p33, p67):
    if np.isnan(value): return "—"
    if value <= p33:    return "Low"
    if value <= p67:    return "Medium"
    return "High"

# Compute thresholds from all tracks
vals = audio_df["rms_energy"].dropna().values
p33, p67 = np.percentile(vals, 33), np.percentile(vals, 67)
```

---

## 3. Stage Timestamps and Window Extraction

Stage timestamps are seconds from session start (when Polar recording began, before audio). To map audio stages to R-R windows:

```python
# Example: P1 stage 4 window
VLAD_SEGMENTS = {
    "stage_4": (1740, 2040),  # seconds from session start
    # ...
}

# Extract HRV for that window
t, rr = load_rr(...)
metrics = metrics_in_window(t, rr, t0=1740, t1=2040)
```

For participants without stage timestamps (P4, P5, P6), only whole-session metrics are computed.

### Sync offset

When audio and R-R were recorded separately, `sync_offset_sec` shifts the audio timeline:
```python
audio_stage_start_sec = polar_stage_start_sec - sync_offset_sec
```
The 3-clap event is the alignment reference.

---

## 4. Key Findings from the Dec 2025 Cohort

| Participant | RMSSD (ms) | Mean HR | DFA α1 | Stage 4 pattern |
|---|---|---|---|---|
| P1 (athlete) | 65.5 | 57 bpm | 0.967 | Clear dip at Stage 4, rebound at Stage 10 |
| P2 (mindfulness) | 58.2 | 62 bpm | 0.891 | Gentler arc, consistent PNS recovery |
| P3 (interiorized) | 44.1 | 68 bpm | 0.923 | Similar arc, less pronounced |
| P4–P6 | no stage data | varies | varies | Whole-session trend only |

**The resilience arc (Stage 4 dip → Stage 10 peak) was visible in all 3 timed participants.** Stage 10 RMSSD was above pre-session baseline in P1 and P2.

**Acoustic feature most correlated with HRV response:** Bass Energy — Stage 4 (highest bass) coincides with DFA α1 minimum. Stage 10 (lowest bass) coincides with SD2 maximum.

---

## 5. Report Generation Pattern

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Place data files (or use sample/P1_2025-12-14_session01.csv)
# 3. Run
python analysis/03_qualitative_model_report.py

# Output: outputs/innerdance_model_report_v2.html
```

The script is tolerant of missing files — it skips any participant or audio track it cannot find and marks it as unavailable in the report. Missing Stage 1 audio (whale delta.mp3) is expected and handled.

The HTML report is self-contained (Plotly + Bootstrap embedded) and includes:
- An **AI-generated disclaimer banner** (sticky at top)
- All charts as interactive Plotly figures
- The full qualitative model table

---

## 6. Critical Constraints to Keep in Mind

| Constraint | Detail |
|---|---|
| RMSSD invalid during slow breathing | Use SD2 + DFA α1 for in-session windows |
| DFA α1 ambiguity | Slow breathing and SNS activation produce the same signal. Breathing belt resolves. |
| Tempo BPM unusable | Librosa returns ~120 BPM for all ambient tracks — exclude from model |
| n=3 timed participants | Statistical inference not valid. All findings are exploratory / descriptive only. |
| No comparison condition | Cannot distinguish innerdance effect from "any music" or "lying still" without passive rest sessions (B/C conditions from step5) |
| Self-report schema is fixed | Never change field names mid-study — all analyses join on these keys |
