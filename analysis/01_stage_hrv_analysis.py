"""
Innerdance Stage-HRV Analysis
==============================
Tests H1 (the arc exists) and H5 (activation precedes recovery) using existing
RR-interval recordings that have stage timestamps.

Expected inputs
---------------
Option A — Polar Beat CSV export:
    rr_file: CSV with columns [Phone timestamp, RR-interval [ms]]
             (Polar Beat: "Export to CSV" in session view)

Option B — Custom / already-processed CSV:
    rr_file: Any CSV with at least two columns: a time column and an RR column.
             Set RR_COL and TIME_COL below.

Stage timestamps:
    stages_file: CSV with columns [stage, start_sec]
    'start_sec' = seconds from session start (when stage transitions in the audio).
    If you have absolute timestamps instead, convert them: subtract session_start_time.

    Example stages_file content:
        stage,start_sec,label
        baseline,0,Baseline (smalltalk)
        stress,300,Stress induction (video+questions)
        1,720,Stage 1 - Befriedigung
        2,960,Stage 2 - Unzufriedenheit
        ...
        12,4200,Stage 12 - Re-Integration

Output
------
- Console: per-stage RMSSD mean and SD, H1 arc test result
- Plots: 3 figures saved to outputs/figures/
"""

import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import seaborn as sns
from scipy import stats
from scipy.interpolate import interp1d

# ── CONFIGURATION ────────────────────────────────────────────────────────────

PROJECT_DIR = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
OUTPUT_DIR  = os.path.join(PROJECT_DIR, "outputs", "figures")

# ── Session registry ─────────────────────────────────────────────────────────
# Add new sessions here; analysis will loop over all of them.
# segments: dict of {label: (start_sec, end_sec)} measured from session start.
SESSIONS = [
    {
        "id":       "P1_20251214",
        "rr_file":  os.path.join(PROJECT_DIR, "data", "14.12.25, 12_50 Vlad-1.csv"),
        # Polar ECG export format: nanosecond timestamp + rr column (NaN on non-peak rows)
        "format":   "polar_ecg",
        "segments": {
            "baseline":     (0,    420),   # 12:50-12:57  resting baseline + smalltalk
            "papers":       (420,  600),   # 12:57-13:00  read research papers (mild cognitive stress)
            "questions":    (660,  900),   # 13:01-13:05  answer questions (stress induction)
            "stage_1":      (960,  1260),  # Stage 1 — Befriedigung (Delta)
            "stage_2":      (1260, 1500),  # Stage 2 — Unzufriedenheit (Theta)
            "stage_3":      (1500, 1740),  # Stage 3 — Die Schwelle (θ→α/β)
            "stage_4":      (1740, 2040),  # Stage 4 — Freisetzung / SNS activation peak (α/β)
            "stage_5":      (2040, 2280),  # Stage 5 — Desintegration (Delta)
            "stages_6-7":   (2280, 2700),  # Stages 6-7 — Erwachen / Erleuchtung (θ/α)
            "stages_8-9":   (2700, 3000),  # Stages 8-9 — Die Wahl / Verstärkung (α/Mu)
            "stage_10":     (3000, 3240),  # Stage 10 — Dunkle Nacht (Delta)
            "stages_11-12": (3240, 3480),  # Stages 11-12 — Einheit / Re-Integration (θ/α)
        },
    },
    # Add more sessions here as you collect them:
    # {
    #     "id":      "Participant2_20260101",
    #     "rr_file": os.path.join(PROJECT_DIR, "data", "participant2_session1_rr.csv"),
    #     "format":  "polar_beat",   # Polar Beat app CSV export
    #     "segments": { ... },
    # },
]

# Rolling window for RMSSD computation (seconds)
RMSSD_WINDOW_SEC = 60   # 60-second window for smoother curve on real data

# Resampling rate for uniform time axis (Hz)
RESAMPLE_HZ = 4  # 4 Hz matches standard HRV literature resampling

# ── STAGE METADATA ───────────────────────────────────────────────────────────

_STAGE_CORE = {
    "baseline":     {"label": "Baseline\n(smalltalk)", "brainwave": "—",      "color": "#aaaaaa"},
    "papers":       {"label": "Read papers",            "brainwave": "—",      "color": "#88aacc"},
    "questions":    {"label": "Questions\n(stress)",    "brainwave": "—",      "color": "#ff7f7f"},
    "stress":       {"label": "Stress\n(video/Q&A)",    "brainwave": "—",      "color": "#ff7f7f"},
    "1":            {"label": "S1 Befriedigung",        "brainwave": "Delta",  "color": "#4e79a7"},
    "2":            {"label": "S2 Unzufriedenheit",     "brainwave": "Theta",  "color": "#59a14f"},
    "3":            {"label": "S3 Die Schwelle",        "brainwave": "θ→α/β", "color": "#f28e2b"},
    "4":            {"label": "S4 Freisetzung",         "brainwave": "α/β",   "color": "#e15759"},
    "5":            {"label": "S5 Desintegration",      "brainwave": "Delta",  "color": "#76b7b2"},
    "6":            {"label": "S6 Erwachen",            "brainwave": "θ/α",   "color": "#edc948"},
    "7":            {"label": "S7 Erleuchtung",         "brainwave": "α/β",   "color": "#b07aa1"},
    "8":            {"label": "S8 Die Wahl",            "brainwave": "α/θ",   "color": "#ff9da7"},
    "9":            {"label": "S9 Verstärkung",         "brainwave": "Mu",     "color": "#9c755f"},
    "10":           {"label": "S10 Dunkle Nacht",       "brainwave": "Delta",  "color": "#bab0ac"},
    "11":           {"label": "S11 Einheit",            "brainwave": "θ/α",   "color": "#4e79a7"},
    "12":           {"label": "S12 Re-Integration",     "brainwave": "δ/α",   "color": "#59a14f"},
}

# Also accept "stage_N" and "stages_N-M" keys (format used in existing analysis script)
STAGE_META = dict(_STAGE_CORE)
for k, v in _STAGE_CORE.items():
    if k.isdigit():
        STAGE_META[f"stage_{k}"] = v
# Combined stages used in existing script
STAGE_META["stages_6-7"]   = {"label": "S6-7 Erwachen/\nErleuchtung", "brainwave": "θ/α",  "color": "#edc948"}
STAGE_META["stages_8-9"]   = {"label": "S8-9 Wahl/\nVerstärkung",     "brainwave": "α/Mu", "color": "#ff9da7"}
STAGE_META["stages_11-12"] = {"label": "S11-12 Einheit/\nRe-Integ.",  "brainwave": "θ/α",  "color": "#4e79a7"}

# Stages that represent SNS activation (used for H5 test) — covers both naming styles
ACTIVATION_STAGES = {"stress", "questions", "3", "stage_3", "4", "stage_4"}
# Stages that represent PNS recovery / integration
RECOVERY_STAGES   = {
    "5", "stage_5", "6", "stage_6", "7", "stage_7",
    "8", "stage_8", "9", "stage_9",
    "10", "stage_10", "11", "stage_11", "12", "stage_12",
    "stages_6-7", "stages_8-9", "stages_11-12",
}


# ── HELPER FUNCTIONS ─────────────────────────────────────────────────────────

def load_rr_polar_ecg(rr_file):
    """
    Load Polar ECG/raw export (H10 with ECG enabled).
    Columns: time [ns], ecg, hr, rr [ms], marker
    Only rows where rr is not NaN are R-peak detections.
    Applies a two-pass artifact filter matching source/1_analyze_vlad_rr.py.
    Returns (times_sec, rr_ms) as numpy arrays, time relative to session start.
    """
    df = pd.read_csv(rr_file)
    df["time_sec"] = (df["time"] - df["time"].iloc[0]) / 1e9

    rr = df.dropna(subset=["rr"]).copy()
    rr = rr[(rr["rr"] > 300) & (rr["rr"] < 2000)]

    # Rolling-median neighbour filter — removes ectopics / motion artefacts
    rolling_med = rr["rr"].rolling(window=5, center=True, min_periods=1).median()
    deviation   = (rr["rr"] - rolling_med).abs() / rolling_med
    rr = rr[deviation <= 0.20].reset_index(drop=True)

    return rr["time_sec"].values, rr["rr"].values


def load_rr_polar_beat(rr_file):
    """
    Load Polar Beat app CSV export.
    Typical columns: 'Phone timestamp', 'RR-interval [ms]'
    Returns (times_sec, rr_ms) as numpy arrays.
    """
    df = pd.read_csv(rr_file)
    # Try to auto-detect column names
    time_col = next((c for c in df.columns if "time" in c.lower()), df.columns[0])
    rr_col   = next((c for c in df.columns if "rr" in c.lower()), df.columns[1])

    rr = df[rr_col].values.astype(float)
    t_raw = df[time_col]
    if t_raw.dtype == object:
        t_dt  = pd.to_datetime(t_raw)
        t_sec = (t_dt - t_dt.iloc[0]).dt.total_seconds().values
    else:
        t_sec = t_raw.values.astype(float)

    valid = (rr > 300) & (rr < 2000)
    return t_sec[valid], rr[valid]


def load_rr(session: dict):
    """Dispatch to the correct loader based on session['format']."""
    fmt = session.get("format", "polar_ecg")
    if fmt == "polar_ecg":
        return load_rr_polar_ecg(session["rr_file"])
    elif fmt == "polar_beat":
        return load_rr_polar_beat(session["rr_file"])
    else:
        raise ValueError(f"Unknown format '{fmt}'. Use 'polar_ecg' or 'polar_beat'.")


def rr_to_uniform(t_sec, rr_ms, target_hz=4):
    """Resample irregular RR series onto a uniform time grid."""
    # Each RR interval ends at t_sec[i]; the interval itself is rr_ms[i]
    rr_end_times = t_sec
    uniform_t = np.arange(rr_end_times[0], rr_end_times[-1], 1.0 / target_hz)
    rr_uniform = interp1d(rr_end_times, rr_ms, kind="linear", bounds_error=False,
                          fill_value="extrapolate")(uniform_t)
    return uniform_t, rr_uniform


def poincare_metrics(rr_ms):
    """
    SD1, SD2, SD1/SD2 from a window of raw RR intervals.
    SD1 = short-term beat-to-beat scatter (≡ RMSSD/√2) — fast parasympathetic signal.
    SD2 = long-term scatter — total autonomic flexibility (both ANS branches).
    SD1/SD2 = sympathovagal balance proxy; high = more PNS relative to total variability.
    """
    if len(rr_ms) < 4:
        return np.nan, np.nan, np.nan
    sd1 = np.sqrt(0.5 * np.mean(np.diff(rr_ms) ** 2))           # = RMSSD / sqrt(2)
    sdnn = np.std(rr_ms, ddof=1)
    sd2_sq = max(2 * sdnn**2 - 0.5 * np.mean(np.diff(rr_ms)**2), 0)
    sd2 = np.sqrt(sd2_sq)
    ratio = sd1 / sd2 if sd2 > 0 else np.nan
    return sd1, sd2, ratio


def dfa_alpha1(rr_ms, n_min=4, n_max=16):
    """
    Short-term DFA scaling exponent α1.
    α1 ≈ 1.0  →  healthy fractal complexity (self-similar regulation)
    α1 < 0.75 →  uncorrelated / loss of regulation
    α1 > 1.5  →  pathological over-correlation / rigidity
    Requires ≥ 4 * n_max beats (64 minimum with default n_max=16).
    """
    N = len(rr_ms)
    if N < n_max * 4:
        return np.nan
    y = np.cumsum(rr_ms - np.mean(rr_ms))
    ns, F = [], []
    for n in range(n_min, n_max + 1):
        n_boxes = N // n
        if n_boxes < 2:
            continue
        segs = y[:n_boxes * n].reshape(n_boxes, n)
        x = np.arange(n)
        fluct = [np.mean((s - np.polyval(np.polyfit(x, s, 1), x))**2) for s in segs]
        ns.append(n)
        F.append(np.sqrt(np.mean(fluct)))
    if len(F) < 4:
        return np.nan
    return float(np.polyfit(np.log(ns), np.log(F), 1)[0])


def rolling_hrv_metrics(rr_ms, t_sec, window_sec=60, target_hz=4):
    """
    Rolling window computation of RMSSD, SD1, SD2, SD1/SD2, and DFA α1.
    All computed directly on raw (irregular) RR intervals — no resampling artefact.
    Returns (uniform_t, dict_of_metric_arrays).
    """
    uniform_t  = np.arange(t_sec[0], t_sec[-1], 1.0 / target_hz)
    half = window_sec / 2.0
    out = {k: np.full(len(uniform_t), np.nan)
           for k in ("rmssd", "sd1", "sd2", "sd1_sd2", "dfa_a1")}

    for i, tc in enumerate(uniform_t):
        mask   = (t_sec >= tc - half) & (t_sec < tc + half)
        rr_win = rr_ms[mask]
        if len(rr_win) < 6:
            continue
        diffs = np.diff(rr_win)
        out["rmssd"][i]   = float(np.sqrt(np.mean(diffs**2)))
        sd1, sd2, ratio   = poincare_metrics(rr_win)
        out["sd1"][i]     = sd1
        out["sd2"][i]     = sd2
        out["sd1_sd2"][i] = ratio
        out["dfa_a1"][i]  = dfa_alpha1(rr_win)

    return uniform_t, out


# kept for backward compatibility
def rolling_rmssd(rr_ms, t_sec, window_sec=60, target_hz=4):
    t, metrics = rolling_hrv_metrics(rr_ms, t_sec, window_sec, target_hz)
    return t, metrics["rmssd"]


def load_stages(stage_file):
    """
    Load stage timestamps.
    Returns DataFrame with columns: stage (str), start_sec (float), label (str).
    Adds an 'end_sec' column by shifting starts forward.
    """
    df = pd.read_csv(stage_file)
    df["stage"] = df["stage"].astype(str)
    df = df.sort_values("start_sec").reset_index(drop=True)
    df["end_sec"] = df["start_sec"].shift(-1)
    # Last stage ends at session end (will be filled from RR data)
    return df


def mean_rmssd_in_window(t, rmssd, t_start, t_end):
    """Mean RMSSD between t_start and t_end seconds."""
    mask = (t >= t_start) & (t < t_end) & ~np.isnan(rmssd)
    if mask.sum() < 3:
        return np.nan
    return np.nanmean(rmssd[mask])


# ── SYNTHETIC DATA FOR DEMONSTRATION ─────────────────────────────────────────
# Remove this block once you point the script at real files.

def make_demo_session():
    """
    Generate a plausible synthetic session matching the stage arc.
    Baseline → slow recovery from stress → Stage 4 dip → long PNS rebound.
    """
    np.random.seed(42)
    session_duration_min = 80
    # average HR ~77 BPM → ~777 ms per beat → 80*60/0.777 ≈ 6178 beats for 80 min
    n_beats = int(session_duration_min * 60 / 0.777)

    # Baseline RR ~750 ms (HR ~80)
    # Stress: RR drops to ~620 ms (HR ~97)
    # Stage 1-3: slow recovery to ~800 ms
    # Stage 4: dip to ~680 ms (activation)
    # Stage 5+: rise to ~900+ ms (PNS rebound)

    stages_sec = [
        ("baseline",  0),
        ("stress",    300),   # 5 min in
        ("1",         600),   # 10 min
        ("2",         900),
        ("3",         1350),
        ("4",         1800),  # 30 min — SNS activation
        ("5",         2100),
        ("6",         2400),
        ("7",         2700),
        ("8",         3000),
        ("9",         3150),
        ("10",        3450),
        ("11",        3750),
        ("12",        4200),
    ]
    session_end = session_duration_min * 60

    # Beat-to-beat variation is what drives RMSSD.
    # We simulate it as: mean_rr (slow drift) + RSA-like oscillation (0.25 Hz, ±30 ms)
    # + white noise (±10 ms). This gives realistic RMSSD of 40-90 ms range.
    beat_times = np.cumsum(np.full(n_beats, 750)) / 1000.0  # initial placeholder
    target_rr_mean = np.interp(
        np.linspace(0, session_end, n_beats),
        [s[1] for s in stages_sec] + [session_end],
        [750, 750, 620, 620, 760, 820, 680, 850, 900, 920, 940, 900, 920, 950, 900]
    )
    # RSA amplitude scales with PNS state: higher in integration stages
    rsa_amp = np.interp(
        np.linspace(0, session_end, n_beats),
        [s[1] for s in stages_sec] + [session_end],
        [30,  30,  15,  15,  35,  40,  20,  60,  70,  75,  75,  70,  70,  80,  65]
    )
    rsa_phase = np.linspace(0, session_end * 0.25 * 2 * np.pi, n_beats)  # 0.25 Hz breathing
    rsa = rsa_amp * np.sin(rsa_phase)
    white_noise = np.random.normal(0, 10, n_beats)
    rr_ms = np.clip(target_rr_mean + rsa + white_noise, 350, 1600)

    # Cumulative time axis (each RR interval determines the timestamp of the NEXT beat)
    t_sec = np.cumsum(rr_ms) / 1000.0
    t_sec = t_sec - t_sec[0]  # start at 0

    # Build stages DataFrame
    stages_df = pd.DataFrame(stages_sec, columns=["stage", "start_sec"])
    stages_df["label"] = [
        STAGE_META.get(str(s[0]), {}).get("label", s[0]) for s in stages_sec
    ]
    stages_df["end_sec"] = stages_df["start_sec"].shift(-1).fillna(session_end)

    return t_sec, rr_ms, stages_df


# ── MAIN ANALYSIS ─────────────────────────────────────────────────────────────

def metrics_in_window(t_sec, rr_ms, t_start, t_end):
    """Compute all HRV metrics for RR beats falling in [t_start, t_end)."""
    mask   = (t_sec >= t_start) & (t_sec < t_end)
    rr_win = rr_ms[mask]
    if len(rr_win) < 6:
        return {k: np.nan for k in ("rmssd","sd1","sd2","sd1_sd2","dfa_a1","mean_hr","sdnn")}
    diffs = np.diff(rr_win)
    rmssd = float(np.sqrt(np.mean(diffs**2)))
    sd1, sd2, ratio = poincare_metrics(rr_win)
    return {
        "rmssd":    rmssd,
        "sd1":      sd1,
        "sd2":      sd2,
        "sd1_sd2":  ratio,
        "dfa_a1":   dfa_alpha1(rr_win),
        "mean_hr":  60_000.0 / float(np.mean(rr_win)),
        "sdnn":     float(np.std(rr_win, ddof=1)),
    }


def run_analysis(t_sec, rr_ms, stages_df, session_id="demo"):
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    session_end = t_sec[-1]
    stages_df["end_sec"] = stages_df["end_sec"].fillna(session_end)

    # ── 1. Compute rolling metrics ───────────────────────────────────────────
    t_uniform, roll = rolling_hrv_metrics(rr_ms, t_sec, window_sec=RMSSD_WINDOW_SEC)
    rmssd = roll["rmssd"]
    t_min = t_uniform / 60.0

    # ── 2. Per-stage summary ──────────────────────────────────────────────────
    print(f"\n{'─'*60}")
    print(f"Session: {session_id}")
    print(f"{'─'*60}")
    print(f"{'Stage':<14} {'Brainwave':<8} {'RMSSD':>7} {'SD1':>7} {'SD2':>7} {'SD1/SD2':>8} {'DFA α1':>7} {'HR':>6}")
    print(f"{'─'*70}")

    stage_stats = []
    for _, row in stages_df.iterrows():
        s    = str(row["stage"])
        meta = STAGE_META.get(s, {"label": s, "brainwave": "—"})
        m    = metrics_in_window(t_sec, rr_ms, row["start_sec"], row["end_sec"])
        label_short = meta["label"].replace("\n", " ")
        bw   = meta.get("brainwave", "—")
        print(f"{s:<14} {bw:<8} "
              f"{m['rmssd']:>7.1f} {m['sd1']:>7.1f} {m['sd2']:>7.1f} "
              f"{m['sd1_sd2']:>8.3f} {m['dfa_a1']:>7.3f} {m['mean_hr']:>6.1f}")
        stage_stats.append({
            "stage": s, "label": label_short, "brainwave": bw,
            "start_sec": row["start_sec"],
            **{k: m[k] for k in ("rmssd","sd1","sd2","sd1_sd2","dfa_a1","mean_hr","sdnn")}
        })

    stats_df = pd.DataFrame(stage_stats)

    # ── 3. H1 — Does the arc exist? ───────────────────────────────────────────
    # Compare first third vs last third of the session (stages only, after stress induction)
    PRE_SESSION_LABELS = {"baseline", "stress", "papers", "questions"}
    session_stages = stages_df[~stages_df["stage"].isin(PRE_SESSION_LABELS)]
    if len(session_stages) > 0:
        session_start = session_stages["start_sec"].min()
        duration = session_end - session_start
        first_third_end   = session_start + duration / 3
        last_third_start  = session_end   - duration / 3

        first_rmssd = rmssd[(t_uniform >= session_start) & (t_uniform < first_third_end) & ~np.isnan(rmssd)]
        last_rmssd  = rmssd[(t_uniform >= last_third_start) & ~np.isnan(rmssd)]

        if len(first_rmssd) > 5 and len(last_rmssd) > 5:
            t_stat, p_val = stats.ttest_ind(first_rmssd, last_rmssd)
            recovered = last_rmssd.mean() > first_rmssd.mean()
            direction = "↑ RMSSD recovers (arc present)" if recovered else "↓ no recovery (arc absent)"
            print(f"\n── H1: Arc test (first-third vs last-third of session stages) ──")
            print(f"   First-third mean RMSSD : {first_rmssd.mean():.1f} ms")
            print(f"   Last-third mean RMSSD  : {last_rmssd.mean():.1f} ms")
            print(f"   Independent t-test     : t={t_stat:.2f}, p={p_val:.4f}  {direction}")
            if recovered and p_val < 0.05:
                print("   → H1 SUPPORTED: activation phase followed by significant RMSSD recovery.")
            elif recovered and p_val >= 0.05:
                print("   → H1 trend in right direction, not yet significant (collect more sessions).")
            else:
                print("   → H1 not supported in this session: no RMSSD recovery in final third.")

    # ── 4. H5 — Activation → Rebound ─────────────────────────────────────────
    baseline_row = stages_df[stages_df["stage"] == "baseline"]
    pre_rmssd = np.nan
    if len(baseline_row):
        pre_rmssd = mean_rmssd_in_window(
            t_uniform, rmssd,
            baseline_row.iloc[0]["start_sec"], baseline_row.iloc[0]["end_sec"]
        )

    activation_rmssd_vals = []
    recovery_rmssd_vals   = []
    for _, row in stages_df.iterrows():
        s = str(row["stage"])
        mu = mean_rmssd_in_window(t_uniform, rmssd, row["start_sec"], row["end_sec"])
        if s in ACTIVATION_STAGES:
            activation_rmssd_vals.append(mu)
        elif s in RECOVERY_STAGES:
            recovery_rmssd_vals.append(mu)

    if activation_rmssd_vals and recovery_rmssd_vals and not np.isnan(pre_rmssd):
        act_mean = np.nanmean(activation_rmssd_vals)
        rec_mean = np.nanmean(recovery_rmssd_vals)
        print(f"\n── H5: Activation → Rebound test ──")
        print(f"   Pre-session baseline RMSSD : {pre_rmssd:.1f} ms")
        print(f"   Activation phase mean RMSSD: {act_mean:.1f} ms  (Δ {act_mean - pre_rmssd:+.1f})")
        print(f"   Recovery phase mean RMSSD  : {rec_mean:.1f} ms  (Δ {rec_mean - pre_rmssd:+.1f})")
        if rec_mean > pre_rmssd:
            print("   → H5 SUPPORTED: recovery phase RMSSD exceeds pre-session baseline (rebound overshoot).")
        else:
            print("   → H5 partial: recovery RMSSD does not exceed baseline (return to baseline only).")

    # ── 5. Plot 1: Full RMSSD trace with stage bands ──────────────────────────
    fig, ax = plt.subplots(figsize=(16, 5))

    for _, row in stages_df.iterrows():
        s = str(row["stage"])
        meta = STAGE_META.get(s, {"color": "#dddddd", "label": s})
        ax.axvspan(row["start_sec"] / 60, row["end_sec"] / 60,
                   alpha=0.15, color=meta["color"], linewidth=0)
        mid = (row["start_sec"] + row["end_sec"]) / 2 / 60
        ax.text(mid, ax.get_ylim()[1] if ax.get_ylim()[1] > 0 else 1,
                s if s not in ("baseline", "stress") else s[:3],
                ha="center", va="top", fontsize=7, color="#555555")

    from scipy.ndimage import uniform_filter1d

    def _smooth(arr, size=60):
        filled = np.where(np.isnan(arr), np.nanmean(arr), arr)
        return uniform_filter1d(filled, size=size)

    ax.plot(t_min, rmssd, color="#1a5276", linewidth=0.8, alpha=0.5, label="RMSSD")
    ax.plot(t_min, _smooth(rmssd), color="#e74c3c", linewidth=2.0, label="RMSSD smoothed")
    if not np.isnan(pre_rmssd):
        ax.axhline(pre_rmssd, color="#27ae60", linestyle="--", linewidth=1.2,
                   label=f"Baseline = {pre_rmssd:.0f} ms")
    ax.set_ylabel("RMSSD (ms)", fontsize=10)
    ax.set_title(f"Session metrics — {session_id}", fontsize=13)
    ax.legend(fontsize=8, loc="upper right")
    ax.set_xlim(0, t_min[-1])
    sns.despine(ax=ax)
    ylim = ax.get_ylim()
    for _, row in stages_df.iterrows():
        s    = str(row["stage"])
        meta = STAGE_META.get(s, {"color": "#dddddd"})
        ax.axvspan(row["start_sec"]/60, row["end_sec"]/60, alpha=0.10,
                   color=meta["color"], linewidth=0)
        mid = (row["start_sec"] + row["end_sec"]) / 2 / 60
        ax.text(mid, ylim[1]*0.98, s if s not in ("baseline","stress","papers","questions") else s[:3],
                ha="center", va="top", fontsize=7, color=meta["color"], fontweight="bold")

    plt.tight_layout()
    out_path = os.path.join(OUTPUT_DIR, f"{session_id}_rmssd_trace.png")
    plt.savefig(out_path, dpi=150, bbox_inches="tight")
    print(f"\nSaved: {out_path}")
    plt.show()

    # ── 6. Plot 2: Multi-metric trace (SD1/SD2 + DFA α1) ─────────────────────
    fig, axes = plt.subplots(3, 1, figsize=(16, 10), sharex=True)
    fig.subplots_adjust(hspace=0.08)

    panels = [
        ("sd1_sd2", "SD1/SD2\n(sympathovagal balance)", "#f28e2b", "higher = more PNS"),
        ("sd2",     "SD2 (ms)\n(autonomic flexibility)", "#59a14f", "wider range = more flexibility"),
        ("dfa_a1",  "DFA α1\n(fractal complexity)",     "#b07aa1", "~1.0 = healthy regulation"),
    ]
    for ax, (key, ylabel, color, note) in zip(axes, panels):
        ax.set_facecolor("#fafafa")
        arr = roll[key]
        ax.plot(t_min, arr, color=color, linewidth=0.8, alpha=0.5)
        ax.plot(t_min, _smooth(arr, 80), color=color, linewidth=2.2)
        ax.set_ylabel(ylabel, fontsize=9)
        ax.text(0.99, 0.95, note, transform=ax.transAxes,
                ha="right", va="top", fontsize=8, color="#777777")
        for _, row in stages_df.iterrows():
            s    = str(row["stage"])
            meta = STAGE_META.get(s, {"color": "#dddddd"})
            ax.axvspan(row["start_sec"]/60, row["end_sec"]/60,
                       alpha=0.10, color=meta["color"], linewidth=0)
        sns.despine(ax=ax)

    # Reference lines for DFA α1
    axes[2].axhline(1.0, color="#b07aa1", linestyle="--", linewidth=1, alpha=0.6,
                    label="α1=1.0 (healthy complexity)")
    axes[2].axhline(0.75, color="#e15759", linestyle=":", linewidth=1, alpha=0.6,
                    label="α1=0.75 (loss of regulation)")
    axes[2].legend(fontsize=8, loc="upper right")
    axes[2].set_xlabel("Session time (minutes)", fontsize=11)

    # Stage labels on top panel
    ylim = axes[0].get_ylim()
    for _, row in stages_df.iterrows():
        s    = str(row["stage"])
        meta = STAGE_META.get(s, {"color": "#dddddd"})
        mid  = (row["start_sec"] + row["end_sec"]) / 2 / 60
        axes[0].text(mid, ylim[1]*0.97, s if s not in ("baseline","stress","papers","questions") else s[:3],
                     ha="center", va="top", fontsize=7, color=meta["color"], fontweight="bold")

    fig.suptitle(f"Autonomic flexibility metrics — {session_id}", fontsize=13, y=1.01)
    out_path = os.path.join(OUTPUT_DIR, f"{session_id}_flexibility_trace.png")
    plt.savefig(out_path, dpi=150, bbox_inches="tight")
    print(f"Saved: {out_path}")
    plt.show()

    # ── 7. Plot 3: Per-stage multi-metric bar chart ───────────────────────────
    stage_order = [s for s in stages_df["stage"].astype(str).tolist()
                   if s in stats_df["stage"].values]
    plot_df = stats_df.set_index("stage").loc[stage_order].reset_index()
    colors  = [STAGE_META.get(s, {"color": "#aaaaaa"})["color"] for s in plot_df["stage"]]
    xlabels = [STAGE_META.get(s, {"label": s})["label"].replace("\n", " ") for s in plot_df["stage"]]
    x       = np.arange(len(plot_df))
    w       = 0.22

    fig, axes = plt.subplots(2, 1, figsize=(16, 10))
    # Top: absolute metrics (RMSSD, SD1, SD2) with shared scale
    ax = axes[0]
    ax.bar(x - w,   plot_df["rmssd"], w, label="RMSSD",    color="#4e79a7", alpha=0.85)
    ax.bar(x,       plot_df["sd1"],   w, label="SD1",      color="#f28e2b", alpha=0.85)
    ax.bar(x + w,   plot_df["sd2"],   w, label="SD2",      color="#59a14f", alpha=0.85)
    if not np.isnan(pre_rmssd):
        ax.axhline(pre_rmssd, color="#27ae60", linestyle="--", linewidth=1.2,
                   label=f"Pre-session RMSSD baseline = {pre_rmssd:.0f} ms")
    ax.set_xticks(x); ax.set_xticklabels(xlabels, rotation=35, ha="right", fontsize=8)
    ax.set_ylabel("ms", fontsize=10)
    ax.set_title("RMSSD · SD1 · SD2 per stage  (SD2 = autonomic flexibility)", fontsize=11)
    ax.legend(fontsize=9); sns.despine(ax=ax)

    # Bottom: ratio metrics (SD1/SD2, DFA α1)
    ax2 = axes[1]
    c1  = ax2.bar(x - w/2, plot_df["sd1_sd2"], w, label="SD1/SD2 (sympathovagal balance)",
                  color="#f28e2b", alpha=0.85)
    ax3 = ax2.twinx()
    c2  = ax3.bar(x + w/2, plot_df["dfa_a1"],  w, label="DFA α1 (fractal complexity)",
                  color="#b07aa1", alpha=0.85)
    ax3.axhline(1.0,  color="#b07aa1", linestyle="--", linewidth=1, alpha=0.5)
    ax3.axhline(0.75, color="#e15759", linestyle=":",  linewidth=1, alpha=0.5)
    ax2.set_xticks(x); ax2.set_xticklabels(xlabels, rotation=35, ha="right", fontsize=8)
    ax2.set_ylabel("SD1/SD2 ratio", fontsize=10, color="#f28e2b")
    ax3.set_ylabel("DFA α1",        fontsize=10, color="#b07aa1")
    handles = [c1, c2]
    ax2.legend(handles=[c1.patches[0], c2.patches[0]],
               labels=["SD1/SD2", "DFA α1"], fontsize=9)
    ax2.set_title("SD1/SD2 & DFA α1 per stage", fontsize=11)
    sns.despine(ax=ax2)

    plt.tight_layout()
    out_path = os.path.join(OUTPUT_DIR, f"{session_id}_metrics_per_stage.png")
    plt.savefig(out_path, dpi=150, bbox_inches="tight")
    print(f"Saved: {out_path}")
    plt.show()

    # ── 8. Plot 4: Δ from baseline (RMSSD + SD2 + SD1/SD2) ───────────────────
    if not np.isnan(pre_rmssd):
        pre_metrics = metrics_in_window(t_sec, rr_ms,
                                        stages_df[stages_df["stage"]=="baseline"].iloc[0]["start_sec"],
                                        stages_df[stages_df["stage"]=="baseline"].iloc[0]["end_sec"]) \
                      if "baseline" in stages_df["stage"].values else {}

        fig, axes = plt.subplots(1, 3, figsize=(18, 5))
        for ax, (col, label, color, base_val) in zip(axes, [
            ("rmssd",   "ΔRMSSD (ms)",              "#4e79a7", pre_rmssd),
            ("sd2",     "ΔSD2 (ms)\nautonomic flexibility", "#59a14f", pre_metrics.get("sd2", np.nan)),
            ("sd1_sd2", "ΔSD1/SD2\nsympathovic balance",   "#f28e2b", pre_metrics.get("sd1_sd2", np.nan)),
        ]):
            if np.isnan(base_val):
                ax.set_title(f"{label}\n(no baseline)"); continue
            deltas = plot_df[col] - base_val
            bar_colors = ["#e74c3c" if d < 0 else "#2ecc71" for d in deltas]
            ax.bar(x, deltas, color=bar_colors, edgecolor="white", linewidth=0.4)
            ax.axhline(0, color="#555555", linewidth=1)
            ax.set_xticks(x); ax.set_xticklabels(xlabels, rotation=35, ha="right", fontsize=8)
            ax.set_ylabel(label, fontsize=10); sns.despine(ax=ax)

        fig.suptitle(f"Change from pre-session baseline — {session_id}", fontsize=13)
        plt.tight_layout()
        out_path = os.path.join(OUTPUT_DIR, f"{session_id}_metrics_delta.png")
        plt.savefig(out_path, dpi=150, bbox_inches="tight")
        print(f"Saved: {out_path}")
        plt.show()

    return stats_df


# ── MULTI-SESSION WRAPPER ─────────────────────────────────────────────────────

def run_multi_session(sessions: list[tuple]):
    """
    sessions: list of (session_id, t_sec_array, rr_ms_array, stages_df)
    Produces a cross-session comparison of intra-session RMSSD range (H3).
    """
    records = []
    for session_id, t_sec, rr_ms, stages_df in sessions:
        t_u, rmssd = rolling_rmssd(rr_ms, t_sec, window_sec=RMSSD_WINDOW_SEC)
        session_stages = stages_df[~stages_df["stage"].isin(["baseline", "stress"])]
        if len(session_stages) == 0:
            continue
        s_start = session_stages["start_sec"].min()
        mask = (t_u >= s_start) & ~np.isnan(rmssd)
        rmssd_range = np.nanmax(rmssd[mask]) - np.nanmin(rmssd[mask])
        records.append({"session_id": session_id, "rmssd_range": rmssd_range})

    if not records:
        return

    df = pd.DataFrame(records)
    print("\n── H3: Intra-session RMSSD range across sessions ──")
    print(df.to_string(index=False))

    fig, ax = plt.subplots(figsize=(8, 4))
    ax.plot(range(len(df)), df["rmssd_range"], "o-", color="#1a5276")
    ax.set_xticks(range(len(df)))
    ax.set_xticklabels(df["session_id"], rotation=30, ha="right", fontsize=8)
    ax.set_ylabel("Intra-session RMSSD range (ms)", fontsize=11)
    ax.set_title("H3: Does autonomic flexibility grow over sessions?", fontsize=12)
    sns.despine(ax=ax)
    plt.tight_layout()
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    out_path = os.path.join(OUTPUT_DIR, "h3_rmssd_range_across_sessions.png")
    plt.savefig(out_path, dpi=150, bbox_inches="tight")
    print(f"Saved: {out_path}")
    plt.show()


def segments_to_df(segments: dict, session_end_sec: float) -> pd.DataFrame:
    """
    Convert the segment dict used in source/1_analyze_vlad_rr.py into the DataFrame
    format expected by run_analysis().
    segments: {label: (start_sec, end_sec)}
    """
    rows = []
    for label, (start, end) in segments.items():
        rows.append({"stage": label, "start_sec": float(start),
                     "end_sec": float(end), "label": label.replace("_", " ")})
    df = pd.DataFrame(rows).sort_values("start_sec").reset_index(drop=True)
    # Clip end times that exceed available data
    df["end_sec"] = df["end_sec"].clip(upper=session_end_sec)
    return df


# ── ENTRY POINT ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    all_stats = {}

    for session in SESSIONS:
        sid = session["id"]
        rr_file = session["rr_file"]

        if not os.path.exists(rr_file):
            print(f"\n⚠  File not found for {sid}: {rr_file}")
            print("   Running demo mode instead.\n")
            t_sec, rr_ms, stages_df = make_demo_session()
            sid = f"{sid}_DEMO"
        else:
            print(f"\nLoading {sid} from {rr_file}")
            t_sec, rr_ms = load_rr(session)
            stages_df = segments_to_df(session["segments"], t_sec[-1])
            print(f"  → {len(rr_ms)} R-R intervals, {t_sec[-1]/60:.1f} min total")
            print(f"  → RR range: {rr_ms.min():.0f}–{rr_ms.max():.0f} ms")

        stats_df = run_analysis(t_sec, rr_ms, stages_df, session_id=sid)
        all_stats[sid] = stats_df

    # Cross-session H3 plot (meaningful only once you have 3+ sessions)
    if len(all_stats) >= 3:
        multi_input = []
        for session in SESSIONS:
            sid = session["id"]
            if sid in all_stats and os.path.exists(session["rr_file"]):
                t, rr = load_rr(session)
                segs  = segments_to_df(session["segments"], t[-1])
                multi_input.append((sid, t, rr, segs))
        if multi_input:
            run_multi_session(multi_input)
