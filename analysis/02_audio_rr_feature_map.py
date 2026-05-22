"""
Audio + RR Feature Map — Stage 1 (whale_delta.mp3)
====================================================
Extracts acoustic features from the stage audio and plots them alongside
the RR-derived metrics (HR, RMSSD, breathing rate) on a shared time axis.

Alignment assumption
--------------------
We assume the audio file starts at the moment Stage 1 begins in the session
(t = 960 s from session start). The RR data is trimmed to the Stage 1 window
and remapped to audio-relative time (t=0 at Stage 1 onset).

If you later collect a 3-clap sync event, replace STAGE_START_SEC with the
computed offset. Everything else stays the same.
"""

import os
import sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import matplotlib.ticker as ticker
from scipy.interpolate import interp1d
from scipy.signal import welch
from scipy.ndimage import uniform_filter1d

import librosa
import librosa.display

# ── PATHS ────────────────────────────────────────────────────────────────────

PROJECT_DIR = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
AUDIO_FILE  = os.path.join(PROJECT_DIR, "sound", "whale delta.mp3")
RR_FILE     = os.path.join(PROJECT_DIR, "data",  "14.12.25, 12_50 Vlad-1.csv")
OUT_DIR     = os.path.join(PROJECT_DIR, "outputs", "figures")

# Stage 1 window in the session (seconds from session start)
STAGE_START_SEC = 960
STAGE_END_SEC   = 1260

# Resampling rate shared between audio features and RR metrics
TARGET_HZ = 4   # 4 Hz = 250 ms resolution — standard HRV resampling rate

# ── AUDIO FEATURE EXTRACTION ─────────────────────────────────────────────────

def extract_audio_features(audio_file, target_hz=4):
    """
    Extract a suite of acoustic features at TARGET_HZ resolution.
    Returns a dict of {feature_name: (time_array, values_array)}.
    """
    print(f"Loading audio: {os.path.basename(audio_file)}")
    y, sr = librosa.load(audio_file, sr=44100, mono=True)
    duration = len(y) / sr
    print(f"  {duration:.1f} s  ({sr} Hz)")

    hop = sr // target_hz          # samples per frame at target_hz
    t   = np.arange(0, duration, 1.0 / target_hz)

    # ── 1. Waveform envelope (RMS of raw signal) ─────────────────────────────
    rms_full = librosa.feature.rms(y=y, frame_length=hop * 2, hop_length=hop)[0]
    rms_full = _trim(rms_full, len(t))

    # ── 2. Bass energy (20–250 Hz) ────────────────────────────────────────────
    # Filter to sub-bass / bass band before computing RMS
    from scipy.signal import butter, sosfilt
    sos = butter(4, [20, 250], btype="band", fs=sr, output="sos")
    y_bass = sosfilt(sos, y)
    rms_bass = librosa.feature.rms(y=y_bass, frame_length=hop * 2, hop_length=hop)[0]
    rms_bass = _trim(rms_bass, len(t))

    # ── 3. Mid energy (250–2000 Hz) ───────────────────────────────────────────
    sos_mid = butter(4, [250, 2000], btype="band", fs=sr, output="sos")
    y_mid = sosfilt(sos_mid, y)
    rms_mid = librosa.feature.rms(y=y_mid, frame_length=hop * 2, hop_length=hop)[0]
    rms_mid = _trim(rms_mid, len(t))

    # ── 4. Spectral centroid (brightness) ────────────────────────────────────
    centroid = librosa.feature.spectral_centroid(y=y, sr=sr, hop_length=hop)[0]
    centroid = _trim(centroid, len(t))

    # ── 5. Amplitude modulation depth (AM depth) ─────────────────────────────
    # Analytic signal envelope → deviation from mean → proxy for AM depth
    from scipy.signal import hilbert
    analytic  = np.abs(hilbert(y))
    # Downsample the envelope to target_hz
    am_env = np.array([
        analytic[i * hop: (i + 1) * hop].mean()
        for i in range(len(t))
    ])
    am_depth = np.abs(am_env - uniform_filter1d(am_env, size=int(target_hz * 10)))
    am_depth = _trim(am_depth, len(t))

    # ── 6. Onset strength (rhythmic / percussive activity) ───────────────────
    onset = librosa.onset.onset_strength(y=y, sr=sr, hop_length=hop)
    onset = _trim(onset, len(t))

    # ── 7. Zero-crossing rate ─────────────────────────────────────────────────
    zcr = librosa.feature.zero_crossing_rate(y, frame_length=hop * 2, hop_length=hop)[0]
    zcr = _trim(zcr, len(t))

    # ── 8. Mel spectrogram (full resolution, stored separately) ──────────────
    n_mels = 128
    mel_spec = librosa.feature.melspectrogram(
        y=y, sr=sr, hop_length=hop, n_mels=n_mels,
        fmin=20, fmax=8000
    )
    mel_db = librosa.power_to_db(mel_spec, ref=np.max)

    features = {
        "rms_full":  (t, rms_full),
        "rms_bass":  (t, rms_bass),
        "rms_mid":   (t, rms_mid),
        "centroid":  (t, centroid),
        "am_depth":  (t, am_depth),
        "onset":     (t, onset),
        "zcr":       (t, zcr),
    }
    return features, mel_db, hop, sr, duration


def _trim(arr, target_len):
    """Trim or pad array to exactly target_len samples."""
    if len(arr) >= target_len:
        return arr[:target_len]
    return np.pad(arr, (0, target_len - len(arr)), mode="edge")


# ── RR METRIC EXTRACTION ──────────────────────────────────────────────────────

def load_rr_stage_window(rr_file, stage_start, stage_end):
    """
    Load the Polar ECG CSV, apply artifact filter, and return the
    RR data remapped to audio-relative time (t=0 at stage_start).
    """
    df = pd.read_csv(rr_file)
    df["time_sec"] = (df["time"] - df["time"].iloc[0]) / 1e9

    rr = df.dropna(subset=["rr"]).copy()
    rr = rr[(rr["rr"] > 300) & (rr["rr"] < 2000)]
    rolling_med = rr["rr"].rolling(window=5, center=True, min_periods=1).median()
    deviation   = (rr["rr"] - rolling_med).abs() / rolling_med
    rr = rr[deviation <= 0.20].reset_index(drop=True)

    # Trim to stage window
    mask  = (rr["time_sec"] >= stage_start) & (rr["time_sec"] < stage_end)
    stage = rr[mask].copy()
    stage["t_rel"] = stage["time_sec"] - stage_start    # audio-relative time
    return stage


def compute_rr_metrics(stage_df, target_hz=4, window_sec=30):
    """
    Compute HR, RMSSD, and breathing rate on a uniform TARGET_HZ grid
    over the stage window.
    Returns DataFrame with columns: t_sec, hr, rmssd, breathing_rate.
    """
    t_end = stage_df["t_rel"].max()
    uniform_t = np.arange(0, t_end, 1.0 / target_hz)

    hr_out = np.full(len(uniform_t), np.nan)
    rmssd_out = np.full(len(uniform_t), np.nan)
    br_out = np.full(len(uniform_t), np.nan)

    half = window_sec / 2.0
    t_arr  = stage_df["t_rel"].values
    rr_arr = stage_df["rr"].values

    for i, tc in enumerate(uniform_t):
        mask = (t_arr >= tc - half) & (t_arr < tc + half)
        rr_win = rr_arr[mask]
        t_win  = t_arr[mask]
        if len(rr_win) < 6:
            continue

        hr_out[i]    = 60_000.0 / np.mean(rr_win)
        diffs        = np.diff(rr_win)
        rmssd_out[i] = np.sqrt(np.mean(diffs ** 2))

        # Breathing rate from HF band of uniformly resampled RR
        if len(rr_win) >= 10:
            fs_r  = 4.0
            t_uni = np.arange(t_win[0], t_win[-1], 1.0 / fs_r)
            if len(t_uni) < 8:
                continue
            try:
                rr_uni = interp1d(t_win, rr_win, kind="linear",
                                  bounds_error=False, fill_value="extrapolate")(t_uni)
                nperseg = min(len(rr_uni), 128)
                f, pxx  = welch(rr_uni, fs=fs_r, nperseg=nperseg)
                hf_mask = (f >= 0.15) & (f <= 0.40)
                if pxx[hf_mask].size > 0:
                    br_out[i] = f[hf_mask][np.argmax(pxx[hf_mask])] * 60
            except Exception:
                pass

    return pd.DataFrame({
        "t_sec": uniform_t,
        "hr":    hr_out,
        "rmssd": rmssd_out,
        "br":    br_out,
    })


# ── PLOTTING ──────────────────────────────────────────────────────────────────

def plot_feature_map(audio_features, mel_db, hop, sr, audio_dur,
                     rr_metrics, stage_dur_sec, out_path):
    """
    Stacked feature map: Mel spectrogram + 5 acoustic features + 3 HRV metrics.
    Shared x-axis = time in seconds (audio-relative).
    Vertical dashed line marks the end of the Stage 1 session window.
    """
    t_audio, _ = audio_features["rms_full"]
    t_rr       = rr_metrics["t_sec"].values

    # ── layout: 1 spectrogram + 5 audio rows + divider + 3 HRV rows ─────────
    row_heights = [3, 1, 1, 1, 1, 1,   1, 1, 1]  # spectrogram is taller
    n_rows = len(row_heights)

    fig = plt.figure(figsize=(18, 16), facecolor="#0d0d0d")
    gs  = gridspec.GridSpec(n_rows, 1, hspace=0.08, height_ratios=row_heights)
    axes = [fig.add_subplot(gs[i]) for i in range(n_rows)]

    for ax in axes:
        ax.set_facecolor("#0d0d0d")
        ax.tick_params(colors="#aaaaaa", labelsize=8)
        for spine in ax.spines.values():
            spine.set_edgecolor("#333333")
        ax.set_xlim(0, audio_dur)

    # shared x limits — only bottom axis gets labels
    for ax in axes[:-1]:
        ax.tick_params(labelbottom=False)

    # ── Row 0: Mel spectrogram ────────────────────────────────────────────────
    ax = axes[0]
    img = librosa.display.specshow(
        mel_db, sr=sr, hop_length=hop,
        x_axis="time", y_axis="mel", fmin=20, fmax=8000,
        ax=ax, cmap="magma"
    )
    ax.set_ylabel("Mel freq (Hz)", color="#aaaaaa", fontsize=8)
    ax.set_xlabel("")
    ax.set_title("Stage 1 — whale delta.mp3 · Audio features + RR metrics",
                 color="white", fontsize=12, pad=6)
    plt.colorbar(img, ax=ax, format="%+2.0f dB", pad=0.01).ax.tick_params(colors="#aaaaaa")
    _add_stage_line(ax, stage_dur_sec, audio_dur)

    # ── Row 1: RMS energy (full + bass) ──────────────────────────────────────
    ax = axes[1]
    t, v = audio_features["rms_full"]
    ax.fill_between(t, 0, v, color="#4c9be8", alpha=0.5, linewidth=0)
    ax.plot(t, v, color="#4c9be8", linewidth=0.7, label="RMS (full)")
    t, v = audio_features["rms_bass"]
    ax.fill_between(t, 0, v, color="#e8714c", alpha=0.5, linewidth=0)
    ax.plot(t, v, color="#e8714c", linewidth=0.7, label="RMS bass 20–250 Hz")
    ax.set_ylabel("Amplitude", color="#aaaaaa", fontsize=8)
    _legend(ax)
    _add_stage_line(ax, stage_dur_sec, audio_dur)

    # ── Row 2: Spectral centroid ──────────────────────────────────────────────
    ax = axes[2]
    t, v = audio_features["centroid"]
    ax.plot(t, v / 1000, color="#4ce87a", linewidth=0.8)
    ax.fill_between(t, 0, v / 1000, color="#4ce87a", alpha=0.2, linewidth=0)
    ax.set_ylabel("Centroid\n(kHz)", color="#aaaaaa", fontsize=8)
    _add_stage_line(ax, stage_dur_sec, audio_dur)

    # ── Row 3: AM depth ───────────────────────────────────────────────────────
    ax = axes[3]
    t, v = audio_features["am_depth"]
    ax.plot(t, v, color="#f7c948", linewidth=0.8)
    ax.fill_between(t, 0, v, color="#f7c948", alpha=0.25, linewidth=0)
    ax.set_ylabel("AM depth", color="#aaaaaa", fontsize=8)
    _add_stage_line(ax, stage_dur_sec, audio_dur)

    # ── Row 4: Onset strength ─────────────────────────────────────────────────
    ax = axes[4]
    t, v = audio_features["onset"]
    ax.plot(t, v, color="#c77dff", linewidth=0.7)
    ax.fill_between(t, 0, v, color="#c77dff", alpha=0.25, linewidth=0)
    ax.set_ylabel("Onset\nstrength", color="#aaaaaa", fontsize=8)
    _add_stage_line(ax, stage_dur_sec, audio_dur)

    # ── Row 5: ZCR ────────────────────────────────────────────────────────────
    ax = axes[5]
    t, v = audio_features["zcr"]
    ax.plot(t, v, color="#90e0ef", linewidth=0.7)
    ax.fill_between(t, 0, v, color="#90e0ef", alpha=0.2, linewidth=0)
    ax.set_ylabel("ZCR", color="#aaaaaa", fontsize=8)
    # Divider label
    ax.text(0.01, 0.92, "▼  HRV metrics (Stage 1 window only, 0–300 s)",
            transform=ax.transAxes, color="#888888", fontsize=8, va="top")
    _add_stage_line(ax, stage_dur_sec, audio_dur)

    # ── Row 6: Heart rate ─────────────────────────────────────────────────────
    ax = axes[6]
    valid = ~np.isnan(rr_metrics["hr"].values)
    ax.plot(t_rr[valid], rr_metrics["hr"].values[valid],
            color="#e8714c", linewidth=1.4, label="HR (bpm)")
    ax.set_ylabel("HR (bpm)", color="#e8714c", fontsize=8)
    ax.yaxis.label.set_color("#e8714c")
    _add_stage_line(ax, stage_dur_sec, audio_dur)

    # ── Row 7: RMSSD ─────────────────────────────────────────────────────────
    ax = axes[7]
    valid = ~np.isnan(rr_metrics["rmssd"].values)
    raw = rr_metrics["rmssd"].values.copy()
    raw[~valid] = np.nan
    sm  = uniform_filter1d(np.where(np.isnan(raw), np.nanmean(raw), raw), size=8)
    ax.plot(t_rr[valid], raw[valid], color="#4c9be8", linewidth=0.7, alpha=0.5)
    ax.plot(t_rr, sm, color="#4c9be8", linewidth=1.8, label="RMSSD (ms)")
    ax.set_ylabel("RMSSD (ms)", color="#4c9be8", fontsize=8)
    ax.yaxis.label.set_color("#4c9be8")
    _add_stage_line(ax, stage_dur_sec, audio_dur)

    # ── Row 8: Breathing rate ─────────────────────────────────────────────────
    ax = axes[8]
    valid = ~np.isnan(rr_metrics["br"].values)
    ax.plot(t_rr[valid], rr_metrics["br"].values[valid],
            color="#4ce87a", linewidth=1.4, label="Breathing rate (bpm)")
    ax.set_ylabel("Breath\n(bpm)", color="#4ce87a", fontsize=8)
    ax.yaxis.label.set_color("#4ce87a")
    ax.set_xlabel("Time (seconds, audio-relative — t=0 = Stage 1 onset)", color="#aaaaaa", fontsize=9)
    ax.tick_params(labelbottom=True)
    _add_stage_line(ax, stage_dur_sec, audio_dur)

    # ── Global annotation ─────────────────────────────────────────────────────
    fig.text(0.01, 0.5,
             "← AUDIO FEATURES                HRV METRICS →",
             va="center", ha="left", rotation=90,
             color="#555555", fontsize=8)

    plt.savefig(out_path, dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor())
    print(f"Saved: {out_path}")
    return fig


def _add_stage_line(ax, stage_dur, audio_dur):
    """Vertical dashed line where Stage 1 session window ends."""
    if stage_dur < audio_dur:
        ax.axvline(stage_dur, color="#ff4444", linewidth=0.8,
                   linestyle="--", alpha=0.7, zorder=5)


def _legend(ax):
    leg = ax.legend(fontsize=7, loc="upper right", framealpha=0.15,
                    labelcolor="white", facecolor="#111")


# ── MAIN ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    os.makedirs(OUT_DIR, exist_ok=True)

    # 1. Audio features
    audio_features, mel_db, hop, sr, audio_dur = extract_audio_features(
        AUDIO_FILE, target_hz=TARGET_HZ
    )

    # 2. RR metrics for Stage 1 window
    stage_dur = STAGE_END_SEC - STAGE_START_SEC   # 300 s
    if os.path.exists(RR_FILE):
        print("Loading RR data for Stage 1 window...")
        stage_df = load_rr_stage_window(RR_FILE, STAGE_START_SEC, STAGE_END_SEC)
        print(f"  {len(stage_df)} beats in Stage 1 window")
        rr_metrics = compute_rr_metrics(stage_df, target_hz=TARGET_HZ, window_sec=30)
    else:
        print(f"RR file not found: {RR_FILE}\nGenerating synthetic RR for demo.")
        # Synthetic Stage 1 RR: mild recovery arc (HR 80→72, RMSSD 95→115 ms)
        np.random.seed(1)
        n = int(stage_dur / 0.78)
        rr_mean = np.linspace(750, 840, n)
        rsa_amp  = np.linspace(30, 55, n)
        rr_vals  = rr_mean + rsa_amp * np.sin(np.linspace(0, stage_dur * 0.25 * 2 * np.pi, n))
        rr_vals += np.random.normal(0, 8, n)
        t_beats  = np.cumsum(rr_vals) / 1000.0
        t_beats -= t_beats[0]
        stage_df = pd.DataFrame({"t_rel": t_beats, "rr": rr_vals})
        rr_metrics = compute_rr_metrics(stage_df, target_hz=TARGET_HZ, window_sec=30)

    # 3. Plot
    out_path = os.path.join(OUT_DIR, "stage1_audio_rr_feature_map.png")
    plot_feature_map(
        audio_features, mel_db, hop, sr, audio_dur,
        rr_metrics, stage_dur, out_path
    )
    plt.show()
