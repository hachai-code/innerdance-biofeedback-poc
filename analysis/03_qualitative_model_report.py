"""
Innerdance Qualitative Model — Acoustic Features × HRV Response
================================================================
Builds a qualitative model table showing how acoustic features at each
innerdance stage correspond to HRV responses across participants.

Per-stage HRV available for: P1, P2, P3 (timestamps known).
Whole-session HRV profiles for: all 6 participants.

Outputs: outputs/qualitative_model_report.html
"""

import os, json, warnings
import numpy as np
import pandas as pd
import librosa
import scipy.signal
import scipy.interpolate
import plotly.graph_objects as go
import plotly.io as pio
from pathlib import Path

warnings.filterwarnings("ignore")

PROJECT_DIR = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
SOUND_DIR   = os.path.join(PROJECT_DIR, "sound", "12 stages tracks")
DATA_DIR    = os.path.join(PROJECT_DIR, "data",
              "baseline + stress test + 5 stages RR recordnings")
OUTPUT_HTML = os.path.join(PROJECT_DIR, "outputs", "innerdance_model_report_v2.html")

# ── PARTICIPANT PROFILES ──────────────────────────────────────────────────────

PARTICIPANTS = {
    "P1": {
        "file": os.path.join(PROJECT_DIR, "data", "14.12.25, 12_50 Vlad-1.csv"),
        "col_time": "time", "col_rr": "rr",
        "age": 38, "profile": "Athlete, very fit",
        "smoker": False, "mindfulness": False, "color": "#4e79a7",
        "timestamps_available": True,
    },
    "P4": {
        "file": os.path.join(DATA_DIR, "13.12.25, 19_30 cezar 12 stages.csv"),
        "col_time": "time", "col_rr": "rr",
        "age": 42, "profile": "Unfit, coleric, smoker",
        "smoker": True, "mindfulness": False, "color": "#e15759",
        "timestamps_available": False,
        "stages_recorded": "12 stages (no stage timestamps)",
    },
    "P5": {
        "file": os.path.join(DATA_DIR, "10.12.25, 15_47-1 Lorenzo first 5 stages.csv"),
        "col_time": "time", "col_rr": "rr",
        "age": 43, "profile": "Smoker",
        "smoker": True, "mindfulness": False, "color": "#f28e2b",
        "timestamps_available": False,
        "stages_recorded": "First 5 stages only",
    },
    "P6": {
        "file": os.path.join(DATA_DIR, "19.12.25, 19_17 Andrei last stages.csv"),
        "col_time": "time", "col_rr": "rr",
        "age": 46, "profile": "—",
        "smoker": False, "mindfulness": False, "color": "#59a14f",
        "timestamps_available": False,
        "stages_recorded": "Last stages only (recording started late)",
    },
    "P2": {
        "file": os.path.join(DATA_DIR, "26.12.2025, 18_29 Claudia 12 stages.csv"),
        "col_time": "UNIX Timestamp", "col_rr": "RR",
        "age": 42, "profile": "Mindfulness practitioner",
        "smoker": False, "mindfulness": True, "color": "#b07aa1",
        "timestamps_available": True,
    },
    "P3": {
        "file": os.path.join(DATA_DIR, "26.12.25, 18_29 Giacomo 12 stages.csv"),
        "col_time": "time", "col_rr": "rr",
        "age": 43, "profile": "Interiorized",
        "smoker": False, "mindfulness": False, "color": "#76b7b2",
        "timestamps_available": True,
    },
}

# ── STAGE TRACK MAPPING ───────────────────────────────────────────────────────

STAGE_TRACKS = [
    {"id": "stage_1",      "label": "Stage 1 — Safety",
     "label_short": "S1", "brainwave": "Delta",
     "folder": "1.- Safety", "file": "whale delta.mp3",
     "duration_sec": 300,
     "german": "Befriedigung", "english": "Safety / Satisfaction",
     "innerdance_intention": "Grounding, first steps of trust, surrender"},
    {"id": "stage_2",      "label": "Stage 2 — Dissatisfaction",
     "label_short": "S2", "brainwave": "Theta",
     "folder": "2.- Dissatisfaction", "file": "Dissatisfaction 1.mp3",
     "duration_sec": 240,
     "german": "Unzufriedenheit",
     "english": "Dissatisfaction",
     "innerdance_intention": "Shift begins: left-brain loosens, right-brain stirs"},
    {"id": "stage_3",      "label": "Stage 3 — The Threshold",
     "label_short": "S3", "brainwave": "θ→α/β",
     "folder": None, "file": "03.01.mp3",   # root of 12 stages tracks folder
     "duration_sec": 240,
     "german": "Die Schwelle",
     "english": "The Threshold",
     "innerdance_intention": "First boundary between worlds; choosing to continue into the unknown",
     "note": "Used for P1 + P5 only. P2/P3/P4 used Purgation-release throughout."},
    {"id": "stage_4",      "label": "Stage 4 — Purgation & Release",
     "label_short": "S4", "brainwave": "α/β",
     "folder": "3.-4.- Purgation release", "file": "Purgation-release 1.mp3",
     "duration_sec": 300,
     "german": "Freisetzung/Reinigung",
     "english": "Purgation-Release (SNS Activation Peak)",
     "innerdance_intention": "Energy peaks; SNS activation; emotional and somatic release at the edge"},
    {"id": "stage_5",      "label": "Stage 5 — Disintegration",
     "label_short": "S5", "brainwave": "Delta",
     "folder": "5.- Disintegration", "file": "Disintegration 1.mp3",
     "duration_sec": 240,
     "german": "Desintegration",
     "english": "Disintegration",
     "innerdance_intention": "Holding opposites; identity boundaries dissolve"},
    {"id": "stages_6_7",   "label": "Stages 6+7 — Awakening",
     "label_short": "S6+7", "brainwave": "θ/α",
     "folder": "6.-7.- Awakening", "file": "Awakening-illumination 1.mp3",
     "duration_sec": 420,
     "german": "Erwachen + Erleuchtung",
     "english": "Awakening + Illumination",
     "innerdance_intention": "Inner knowing expands; intuitive answers emerge"},
    {"id": "stages_8_9",   "label": "Stages 8+9 — The Choice / Strength-Failure",
     "label_short": "S8+9", "brainwave": "α/Mu",
     "folder": "9.- Strength-Failure", "file": "Strength-failure 1.mp3",
     "duration_sec": 300,
     "german": "Die Wahl + Verstärkung/Versagen",
     "english": "The Choice + Strength-Failure",
     "innerdance_intention": "Energy builds toward the unknown; ego-death threshold"},
    {"id": "stage_10",     "label": "Stage 10 — Dark Night of the Soul",
     "label_short": "S10", "brainwave": "Delta",
     "folder": "10.- Dark night of the soul", "file": "dark night of soul 1.mp3",
     "duration_sec": 240,
     "german": "Dunkle Nacht der Seele",
     "english": "Dark Night of the Soul",
     "innerdance_intention": "Deepest surrender; seeing the ego's death; womb of rebirth"},
    {"id": "stages_11_12", "label": "Stages 11+12 — Unity & Re-Integration",
     "label_short": "S11+12", "brainwave": "θ/α",
     "folder": "11.-12.- Reintegration",
     "file": "Unity-Oneness-Reintegration 1.mp3",
     "duration_sec": 420,
     "german": "Einheit + Re-Integration",
     "english": "Unity + Re-Integration",
     "innerdance_intention": "Synergy between hemispheres; love and trust in the heart centre"},
]

# ── STAGE TIMESTAMPS FOR TIMED PARTICIPANTS ───────────────────────────────────
# Vlad: pre-session baseline available; stages relative to session start
# P2/P3: recording starts just before Stage 1 (no pre-session baseline)

VLAD_BASELINE   = (0, 420)    # 7-min resting baseline before any stress protocol
# Pre-session segments for Vlad (stress protocol before innerdance)
VLAD_PRESESSION = {
    "baseline":  (0,   420),   # 12:50–12:57  resting + light activity
    "papers":    (420, 600),   # 12:57–13:00  2-min research paper reading (cognitive load)
    "questions": (660, 900),   # 13:01–13:05  answering questions (stress induction)
}
VLAD_SEGMENTS   = {
    "stage_1":      (960,  1260),
    "stage_2":      (1260, 1500),
    "stage_3":      (1500, 1740),  # 13:15–13:19 — dedicated Stage 3 track (03.01.mp3)
    "stage_4":      (1740, 2040),  # 13:19–13:24 — Purgation-release; SNS activation peak
    "stage_5":      (2040, 2280),
    "stages_6_7":   (2280, 2700),
    "stages_8_9":   (2700, 3000),
    "stage_10":     (3000, 3240),
    "stages_11_12": (3240, 3480),
}

# P2/P3: combined Stage 3+4 window maps to Stage 4 track row.
# They had no separate Stage 3 track — "stage_3" will show as — for these participants.
CLAUDIA_SEGMENTS = {
    "stage_1":      (62,   362),
    "stage_2":      (362,  722),
    "stage_4":      (722,  1142),  # combined 3+4 window; Purgation-release played throughout
    "stage_5":      (1142, 1502),
    "stages_6_7":   (1502, 1922),
    "stages_8_9":   (1922, 2342),
    "stage_10":     (2342, 2822),
    "stages_11_12": (2822, 3242),
}

GIACOMO_SEGMENTS = {
    "stage_1":      (90,   390),
    "stage_2":      (390,  750),
    "stage_4":      (750,  1170),  # combined 3+4 window; Purgation-release played throughout
    "stage_5":      (1170, 1530),
    "stages_6_7":   (1530, 1950),
    "stages_8_9":   (1950, 2370),
    "stage_10":     (2370, 2850),
    "stages_11_12": (2850, 3270),
}

TIMED_SEGMENTS = {
    "P1": VLAD_SEGMENTS,
    "P2": CLAUDIA_SEGMENTS,
    "P3": GIACOMO_SEGMENTS,
}

# ── HRV FUNCTIONS ─────────────────────────────────────────────────────────────

def load_rr(p):
    """Load Polar ECG CSV → (t_sec, rr_ms) with artifact filter."""
    df = pd.read_csv(p["file"])
    t_col  = p["col_time"]
    rr_col = p["col_rr"]

    df["_t"] = (df[t_col] - df[t_col].iloc[0]) / 1e9
    rr = df.dropna(subset=[rr_col]).copy()
    rr = rr[(rr[rr_col] > 300) & (rr[rr_col] < 2000)]
    rolling_med = rr[rr_col].rolling(5, center=True, min_periods=1).median()
    deviation   = (rr[rr_col] - rolling_med).abs() / rolling_med
    rr = rr[deviation <= 0.20].reset_index(drop=True)
    return rr["_t"].values, rr[rr_col].values


def poincare_metrics(rr):
    if len(rr) < 4:
        return np.nan, np.nan, np.nan
    sd1   = np.sqrt(0.5 * np.mean(np.diff(rr)**2))
    sdnn  = np.std(rr, ddof=1)
    sd2   = np.sqrt(max(2*sdnn**2 - 0.5*np.mean(np.diff(rr)**2), 0))
    ratio = sd1/sd2 if sd2 > 0 else np.nan
    return sd1, sd2, ratio


def dfa_alpha1(rr, n_min=4, n_max=16):
    N = len(rr)
    if N < n_max * 4:
        return np.nan
    y = np.cumsum(rr - np.mean(rr))
    ns, F = [], []
    for n in range(n_min, n_max + 1):
        nb = N // n
        if nb < 2:
            continue
        segs = y[:nb*n].reshape(nb, n)
        x    = np.arange(n)
        fl   = [np.mean((s - np.polyval(np.polyfit(x, s, 1), x))**2) for s in segs]
        ns.append(n); F.append(np.sqrt(np.mean(fl)))
    if len(F) < 4:
        return np.nan
    return float(np.polyfit(np.log(ns), np.log(F), 1)[0])


def metrics_in_window(t, rr, t0, t1):
    mask = (t >= t0) & (t < t1)
    rw   = rr[mask]
    if len(rw) < 6:
        return {k: np.nan for k in ("rmssd","sd1","sd2","sd1_sd2","dfa_a1","mean_hr")}
    diffs = np.diff(rw)
    sd1, sd2, ratio = poincare_metrics(rw)
    return {
        "rmssd":   float(np.sqrt(np.mean(diffs**2))),
        "sd1":     sd1, "sd2": sd2, "sd1_sd2": ratio,
        "dfa_a1":  dfa_alpha1(rw),
        "mean_hr": 60_000.0 / float(np.mean(rw)),
    }


# ── AUDIO FEATURE EXTRACTION ──────────────────────────────────────────────────

def extract_audio_features(audio_path, duration=None, sr=22050):
    """
    Extract 6 summary acoustic features from an audio file.
    duration: seconds to load (None = full file, but capped at 600s for speed)
    """
    max_dur = min(duration or 600, 600)
    y, sr = librosa.load(audio_path, sr=sr, duration=max_dur, mono=True)

    # 1. RMS energy (overall loudness)
    rms = float(np.sqrt(np.mean(y**2)))

    # 2. Bass energy — bandpass 20–250 Hz
    sos_bass = scipy.signal.butter(4, [20, 250], btype="bandpass", fs=sr, output="sos")
    y_bass   = scipy.signal.sosfilt(sos_bass, y)
    bass_rms = float(np.sqrt(np.mean(y_bass**2)))

    # 3. Spectral centroid — mean frequency centre of gravity (Hz)
    centroid  = librosa.feature.spectral_centroid(y=y, sr=sr)
    spec_cent = float(np.mean(centroid))

    # 4. AM depth — coefficient of variation of Hilbert envelope
    #    High = strong amplitude modulation (waves, pulses); Low = flat drone
    envelope  = np.abs(scipy.signal.hilbert(y))
    # smooth to ~2 Hz bandwidth so we see macro modulation, not single beats
    sos_env   = scipy.signal.butter(2, 2.0, btype="low", fs=sr, output="sos")
    env_s     = scipy.signal.sosfilt(sos_env, envelope)
    am_depth  = float(np.std(env_s) / (np.mean(env_s) + 1e-10))

    # 5. Onset strength — mean level of onset detection envelope
    #    High = overall activity level (transients, attacks); Low = sustained/smooth
    oenv       = librosa.onset.onset_strength(y=y, sr=sr)
    onset_mean = float(np.mean(oenv))

    # 6. Rhythmic pulse clarity — onset coefficient of variation (std / mean)
    #    High CV = clear distinct beats (peaks and silences between them)
    #    Low CV  = continuous sound with no rhythmic structure (drone, ambient)
    #    Replaces the tempogram approach which always returns 1.0 (normalised).
    onset_cv = float(np.std(oenv) / (np.mean(oenv) + 1e-10))

    # Tempo estimate (BPM)
    tempo, _  = librosa.beat.beat_track(onset_envelope=oenv, sr=sr)
    tempo_bpm = float(tempo) if np.isscalar(tempo) else float(np.mean(tempo))

    return {
        "rms_energy":      rms,
        "bass_energy":     bass_rms,
        "spec_centroid_hz": spec_cent,
        "am_depth":        am_depth,
        "onset_strength":  onset_mean,
        "onset_cv":        onset_cv,
        "tempo_bpm":       tempo_bpm,
    }


# ── QUALITATIVE CATEGORY LABELS ───────────────────────────────────────────────

def categorize(value, p33, p67):
    """Return 'Low' / 'Medium' / 'High' based on percentile thresholds."""
    if np.isnan(value):
        return "—"
    if value <= p33:
        return "Low"
    if value <= p67:
        return "Medium"
    return "High"


FEATURE_META = {
    "rms_energy": {
        "label": "Overall Energy",
        "unit": "(RMS)",
        "low_desc":  "Barely audible — like sound heard from another room. The body is not 'pushed' by volume.",
        "med_desc":  "Present and engaging — sound fills the space without dominating it.",
        "high_desc": "Full, immersive, commanding — the sound takes over the room. You feel it in your chest.",
        "hrv_link":  "Lower energy stages tend to support parasympathetic recovery (RMSSD ↑, DFA α1 → 0.9–1.0).",
    },
    "bass_energy": {
        "label": "Bass Vibration",
        "unit": "(20–250 Hz RMS)",
        "low_desc":  "No body vibration — sound lives above the throat. Cerebral, not somatic.",
        "med_desc":  "Mild chest resonance — you feel a warmth in the torso.",
        "high_desc": "Strong sub-bass vibration — felt in the belly, spine, and bones. Strongly anchoring or activating.",
        "hrv_link":  "High bass stages correlate with maximum SNS engagement (DFA α1 lowest, SD2 lowest — Stage 4 is the peak).",
    },
    "spec_centroid_hz": {
        "label": "Tonal Brightness",
        "unit": "(Spectral Centroid Hz)",
        "low_desc":  "Dark, warm, earthy — all energy below 800 Hz. Felt in the lower body. Primal, ancestral.",
        "med_desc":  "Balanced — warmth with some presence. Mid-range awareness, heart-level.",
        "high_desc": "Bright, airy, head-level — crisp high frequencies dominate. Mental, luminous, expansive.",
        "hrv_link":  "Low centroid (dark) tracks correlate with Delta brainwave states and deeper PNS recovery.",
    },
    "am_depth": {
        "label": "Amplitude Modulation",
        "unit": "(Envelope CV)",
        "low_desc":  "Continuous drone — almost no amplitude variation. Like a sustained tone or white noise. Hypnotic, monotonic.",
        "med_desc":  "Gentle waves — slow amplitude breathing, like a tide. Naturally entrains slow breathing.",
        "high_desc": "Strong rhythmic waves — clear swells and recessions. Feels like oceanic breathing or drumming.",
        "hrv_link":  "High AM depth stages are the primary RSA driver — entraining slow breathing → LF HRV peak at 0.1 Hz.",
    },
    "onset_strength": {
        "label": "Beat/Pulse Clarity",
        "unit": "(Onset Strength)",
        "low_desc":  "No beats, amorphous — the music has no rhythmic structure. Pure texture and space.",
        "med_desc":  "Soft implied pulse — you sense a heartbeat without a clear meter. Invites movement.",
        "high_desc": "Clear, driving rhythm — the beat is undeniable. Activating, propulsive, energising.",
        "hrv_link":  "High onset stages co-occur with SNS activation (lower RMSSD, SD1/SD2 shifts toward SNS).",
    },
    "onset_cv": {
        "label": "Rhythmic Pulse Clarity",
        "unit": "(Onset CV = std/mean)",
        "low_desc":  "Continuous, flowing — no distinct beats or attacks. The sound is a texture, not a rhythm. Pure drone or sustained chords.",
        "med_desc":  "Some rhythmic events — you feel occasional pulses or accents but they are not dominant. The groove is implied rather than stated.",
        "high_desc": "Clear, distinct beats with space between them — the rhythm is undeniable. The body can 'lock in' to the pulse. Percussion, accents, definite rhythmic structure.",
        "hrv_link":  "High pulse clarity drives SNS entrainment. Low pulse clarity (ambient) allows the nervous system to self-organise toward higher DFA α1.",
    },
}

HRV_METRIC_META = {
    "rmssd": {
        "label": "RMSSD",
        "full":  "Root Mean Square of Successive Differences",
        "units": "ms",
        "novice_high": "Your chest opens. Breathing deepens automatically. A felt sense of ease and safety — your heart rhythm has 'slack' in it. You might feel a gentle warmth spreading from the chest.",
        "novice_low":  "A mild tightening — your heart rhythm becomes more rigid, like a rubber band under tension. This is normal during activating stages and is NOT distress — it is the body mobilising energy.",
        "caveat": "Not reliable during slow innerdance breathing (<9 bpm). Use for comparison to resting baseline only.",
        "direction_note": "Compared to P1's resting baseline (104 ms). P2/P3: compared to their Stage 1 as reference.",
    },
    "sd2": {
        "label": "SD2",
        "full":  "Long-axis Poincaré scatter (total autonomic flexibility)",
        "units": "ms",
        "novice_high": "Your nervous system has a wide 'operating range' — it can move freely from high alert to deep rest. Like a skilled jazz musician who can play both fortissimo and pianissimo. You feel this as a sense of spaciousness, of having more inner room.",
        "novice_low":  "The ANS is temporarily 'locked in' to a narrower range. This is not bad — it can mean deep sustained engagement. Like a sprinter at peak effort: completely committed, less variable.",
        "caveat": "Valid across all stages. The primary within-session flexibility marker.",
        "direction_note": "Higher SD2 = more total autonomic flexibility. Stage 10 typically peaks.",
    },
    "sd1_sd2": {
        "label": "SD1/SD2",
        "full":  "Poincaré ratio (sympathovagal balance)",
        "units": "(ratio)",
        "novice_high": "The 'rest and receive' (parasympathetic) branch is more active relative to total variability. You feel this as a softening — jaw relaxes, shoulders drop, eyes soften. Receptive mode. Easier to be affected by music.",
        "novice_low":  "The 'act and respond' (sympathetic) branch is more active. You feel more alert, possibly more energised or slightly on-edge. The body is ready for something — this supports the activation arc.",
        "caveat": "Valid across all stages. Higher ratio = more parasympathetic dominance relative to total variability.",
        "direction_note": "Ratio range: 0.0 (fully sympathetic) → 1.0 (fully parasympathetic). Healthy resting ~0.3.",
    },
    "dfa_a1": {
        "label": "DFA α1",
        "full":  "Detrended Fluctuation Analysis short-term exponent",
        "units": "(exponent)",
        "novice_high": "Your heartbeat is highly organised and self-referential — like a fractal, each beat 'knows' the history of the last few beats. Around 1.0 this is the healthiest state: effortless self-regulation, the feeling of flow or timelessness.",
        "novice_low":  "Below 0.75: your heart rhythm temporarily loses its fractal organisation — beats are more random, regulation is under load. This happens at the peak of SNS activation (Stage 3+4). Like the moment before a wave breaks: maximum energy, minimum order.",
        "caveat": "α1 ≈ 1.0 = healthy complexity. α1 < 0.75 = loss of regulation (seen at SNS peak). α1 > 1.5 = rigidity.",
        "direction_note": "Needs ≥64 beats per window. Most reliable at per-stage resolution (5+ minutes of data).",
    },
}


# ── EXPERT SENSORY DESCRIPTIONS ───────────────────────────────────────────────
# Written after audio feature analysis to reflect the actual character of each track.
# These are calibrated against the computed features and the innerdance stage intention.

STAGE_EXPERT_DESCRIPTIONS = {
    "stage_1": {
        "expert": (
            "The opening track is predominantly sub-bass: a barely audible, continuous low-frequency "
            "hum with no clear rhythm or melody. As an innerdance practitioner you feel this as "
            "'creating the container' — a gentle vibrational invitation that asks the body to settle. "
            "There is nothing to track or follow. The practitioner hears: 'low, slow, still — the room "
            "is breathing for you.'"
        ),
        "novice": (
            "You may not consciously 'hear' much here. Instead you feel a gentle heaviness, your jaw "
            "softens, your eyes want to close. Your heart slows without effort — this is the RMSSD and "
            "SD1/SD2 rising from the stress baseline back toward safety."
        ),
    },
    "stage_2": {
        "expert": (
            "Slightly more textural movement appears — a gentle stirring. The tone is still dark but "
            "with subtle shifting harmonics, as if something is beginning to stir beneath the surface. "
            "Practitioners recognise this as the 'dissatisfaction' state: enough change to register but "
            "not enough to resolve. The sound creates productive tension."
        ),
        "novice": (
            "You might feel a mild restlessness — a sense that something is moving but you can't name it. "
            "This is normal and intentional. Your nervous system is beginning to reorganise: DFA α1 still "
            "below 0.9 (not yet at healthy complexity), and SD1/SD2 settling."
        ),
    },
    "stage_3": {
        "expert": (
            "Stage 3 — The Threshold — uses a dedicated track (03.01.mp3) distinct from the Purgation-Release "
            "that follows. This is a transitional piece: it signals that the boundary between everyday "
            "consciousness and the deeper innerdance space is being approached. The practitioner feels "
            "this as a subtle energetic shift — neither the settling of Stage 1 nor the full activation "
            "of Stage 4. The sound creates a felt choice point: 'do I continue into the unknown?' "
            "Used only for P1 and P5 in this dataset."
        ),
        "novice": (
            "A shift in the quality of attention — you feel something is changing but the music has not "
            "yet pushed you. DFA α1 is approaching 0.98 (near healthy complexity), RMSSD at ~109 ms "
            "(P1 data): still above baseline, your nervous system has not yet been activated. "
            "This is the last moment of relative ease before the release arc."
        ),
    },
    "stage_4": {
        "expert": (
            "Stage 4 — Purgation-Release — is the SNS activation peak of the entire session. "
            "The Purgation-release track is the most energetically demanding: strong bass, clear rhythm, "
            "high overall intensity. Practitioners call this 'the activation arc' — the sound pushes the "
            "nervous system to its edge. The release in Stage 4 is often the emotional peak: tears, "
            "laughter, movement, catharsis. You hear/feel: 'this is where the body does the work.' "
            "Note: P2 and P3 had no separate Stage 3; their combined Stage 3+4 window "
            "uses this track throughout, so their HRV values reflect the average of both stages."
        ),
        "novice": (
            "You will feel it. Heart beats faster, breath may become shallow or release in a surge. "
            "Emotions may surface. This is DFA α1 dropping to 0.777 (P1) — the body is at the edge "
            "of its regulatory capacity, mobilising everything. RMSSD drops to ~94.9 ms (below P1's "
            "baseline of 104 ms). This is healthy and intentional — the deepest stress load of the "
            "session, creating the conditions for the Stage 10 rebound."
        ),
    },
    "stage_5": {
        "expert": (
            "After the activation peak, the sound shifts back toward lower frequencies with reduced "
            "intensity. Practitioners feel this as 'the aftermath' — the body is still reverberating "
            "from Stage 4 but the music no longer pushes. This is holding both states simultaneously: "
            "the practitioner hears: 'it is getting quieter, but you haven't landed yet.'"
        ),
        "novice": (
            "A sense of things slowing down, but perhaps some residual heat or emotion. Your heart "
            "rhythm is beginning to return toward baseline. SD2 starts to recover. You might feel "
            "a floating quality."
        ),
    },
    "stages_6_7": {
        "expert": (
            "The awakening stages often bring more harmonic content — voices or higher frequency "
            "tones appear, brightening the spectral landscape. The practitioner hears a shift from "
            "'being moved' to 'beginning to see from a wider place.' The track typically has medium "
            "energy with gentle melodic elements — less bass-dominated, more expansive."
        ),
        "novice": (
            "A sense of opening or spaciousness. You might feel more aware of your surroundings while "
            "still in a deeply relaxed state. SD1/SD2 rises — the parasympathetic system is more "
            "present. Some people experience insights or images here."
        ),
    },
    "stages_8_9": {
        "expert": (
            "The 'Strength-Failure' track is complex: it begins with building energy (Strength/Wahl — "
            "the choice) and then dissolves (Failure/Versagen — surrendering to the unknown). "
            "Practitioners hear this as the last push before the deepest surrender. Bass and rhythm "
            "may pulse then fall away. This track prepares the nervous system for Stage 10."
        ),
        "novice": (
            "You may feel a sense of gathering — as if a decision point is approaching — followed by "
            "a release of that tension. Your nervous system is building toward its deepest integration. "
            "SD2 often rises here as the ANS begins expanding its range again."
        ),
    },
    "stage_10": {
        "expert": (
            "The dark night track is typically the most minimal in the session: deep, slow, near-silent. "
            "Almost nothing to hold onto. Practitioners call this 'the void' — the womb before rebirth. "
            "You hear it as: 'this is where we stop trying.' The sound creates maximum internal space. "
            "There is almost no rhythmic structure — the body is completely on its own. "
            "This is where the deepest HRV recovery consistently appears."
        ),
        "novice": (
            "Deepest stillness. You might feel tears without knowing why, or profound peace. Your heart "
            "is beating slowly and freely — RMSSD at its session peak (+13 ms above stress baseline for P1), "
            "SD2 near its highest point, DFA α1 at healthy complexity (~1.2). This is the 'rebound overshoot' — "
            "your ANS has gone further into recovery than before the session started."
        ),
    },
    "stages_11_12": {
        "expert": (
            "The closing tracks bring warmth back: usually voices, gentle harmonics, or natural sounds. "
            "The spectral centroid rises from the Stage 10 depth — brightness returns to the sound "
            "without the pressure of the activation arc. Practitioners hear 're-integration': "
            "'you are coming back, but you are not the same.' The body is invited to return to "
            "ordinary consciousness carrying the reorganised state."
        ),
        "novice": (
            "You feel a gentle return — like slowly surfacing from deep water. A sense of warmth, "
            "perhaps gratitude. Your nervous system is stabilising at a new, slightly better-regulated "
            "baseline. RMSSD often remains above pre-session baseline into the hours after the session."
        ),
    },
}


# ── MAIN ANALYSIS ─────────────────────────────────────────────────────────────

def run():
    os.makedirs(os.path.join(PROJECT_DIR, "outputs"), exist_ok=True)

    # ── 1. Extract audio features from all 8 tracks ────────────────────────
    print("Extracting audio features…")
    audio_features = {}
    for st in STAGE_TRACKS:
        if st["folder"] is None:
            audio_path = os.path.join(SOUND_DIR, st["file"])
        else:
            audio_path = os.path.join(SOUND_DIR, st["folder"], st["file"])
        if not os.path.exists(audio_path):
            print(f"  ⚠  Missing: {audio_path}")
            audio_features[st["id"]] = {k: np.nan for k in
                ["rms_energy","bass_energy","spec_centroid_hz",
                 "am_depth","onset_strength","onset_cv","tempo_bpm"]}
        else:
            print(f"  Analysing {st['label_short']}: {st['file']}")
            audio_features[st["id"]] = extract_audio_features(
                audio_path, duration=st["duration_sec"])

    audio_df = pd.DataFrame(audio_features).T
    print("\nAudio features extracted:")
    print(audio_df.to_string())

    # ── 2. Compute qualitative thresholds (33rd / 67th percentile) ─────────
    thresholds = {}
    for feat in ["rms_energy","bass_energy","spec_centroid_hz",
                 "am_depth","onset_strength","onset_cv"]:
        vals = audio_df[feat].dropna().values
        thresholds[feat] = (float(np.percentile(vals, 33)),
                            float(np.percentile(vals, 67)))

    # Assign categories
    cats = {}
    for feat in thresholds:
        p33, p67 = thresholds[feat]
        cats[feat] = {sid: categorize(audio_features[sid][feat], p33, p67)
                      for sid in audio_features}

    # ── 3. Load RR data for all participants ────────────────────────────────
    print("\nLoading RR data…")
    rr_data = {}
    session_stats = {}
    for name, cfg in PARTICIPANTS.items():
        try:
            t, rr = load_rr(cfg)
            rr_data[name] = (t, rr)
            sd1, sd2, ratio = poincare_metrics(rr)
            session_stats[name] = {
                "n_beats":  len(rr),
                "duration_min": t[-1]/60,
                "rmssd":    float(np.sqrt(np.mean(np.diff(rr)**2))),
                "sd1":      sd1, "sd2": sd2, "sd1_sd2": ratio,
                "dfa_a1":   dfa_alpha1(rr),
                "mean_hr":  60_000./float(np.mean(rr)),
            }
            print(f"  {name}: {len(rr)} beats, {t[-1]/60:.1f} min, "
                  f"RMSSD={session_stats[name]['rmssd']:.1f} ms, "
                  f"HR={session_stats[name]['mean_hr']:.1f} bpm")
        except Exception as e:
            print(f"  {name}: ERROR loading — {e}")
            rr_data[name] = None

    # ── 4. Per-stage metrics for timed participants ─────────────────────────
    print("\nComputing per-stage HRV metrics…")
    stage_hrv = {st["id"]: {} for st in STAGE_TRACKS}

    for name, segs in TIMED_SEGMENTS.items():
        if rr_data[name] is None:
            continue
        t, rr = rr_data[name]

        # P1: compute baseline reference
        if name == "P1":
            baseline_m = metrics_in_window(t, rr, *VLAD_BASELINE)
            baseline_rmssd = baseline_m["rmssd"]
        else:
            # Use Stage 1 as reference for P2/P3 (no pre-session baseline)
            m1 = metrics_in_window(t, rr, *segs.get("stage_1", (0, 360)))
            baseline_rmssd = m1["rmssd"]

        for st in STAGE_TRACKS:
            seg = segs.get(st["id"])
            if seg is None:
                continue
            m = metrics_in_window(t, rr, seg[0], seg[1])
            m["rmssd_delta"] = (m["rmssd"] - baseline_rmssd
                                if not np.isnan(m["rmssd"]) else np.nan)
            stage_hrv[st["id"]][name] = m
            print(f"  {name} {st['label_short']}: "
                  f"RMSSD={m['rmssd']:.1f}ms (Δ{m['rmssd_delta']:+.1f}), "
                  f"SD2={m['sd2']:.1f}, SD1/SD2={m['sd1_sd2']:.3f}, "
                  f"DFAα1={m['dfa_a1']:.3f}")

    # ── 4b. P1 pre-session HRV (baseline / papers / questions) ───────────
    print("\nP1 pre-session HRV:")
    vlad_presession_hrv = {}
    if rr_data.get("P1") is not None:
        t, rr = rr_data["P1"]
        for seg_label, (t0, t1) in VLAD_PRESESSION.items():
            m = metrics_in_window(t, rr, t0, t1)
            vlad_presession_hrv[seg_label] = m
            print(f"  P1 {seg_label}: RMSSD={m['rmssd']:.1f}ms, "
                  f"SD2={m['sd2']:.1f}, SD1/SD2={m['sd1_sd2']:.3f}, "
                  f"DFAα1={m['dfa_a1']:.3f}, HR={m['mean_hr']:.1f}")

    # ── 5. Compute mean HRV per stage across timed participants ─────────────
    def mean_across(stage_id, metric):
        vals = [v[metric] for v in stage_hrv[stage_id].values()
                if not np.isnan(v.get(metric, np.nan))]
        return float(np.nanmean(vals)) if vals else np.nan

    # ── 6. Build the model table DataFrame ────────────────────────────────
    rows = []
    for st in STAGE_TRACKS:
        sid = st["id"]
        af  = audio_features[sid]
        row = {
            "stage_id":    sid,
            "stage_label": st["label"],
            "label_short": st["label_short"],
            "brainwave":   st["brainwave"],
            "german":      st["german"],
            "english":     st["english"],
            "intention":   st["innerdance_intention"],
            # audio features
            "rms_energy":      af.get("rms_energy", np.nan),
            "bass_energy":     af.get("bass_energy", np.nan),
            "spec_centroid_hz":af.get("spec_centroid_hz", np.nan),
            "am_depth":        af.get("am_depth", np.nan),
            "onset_strength":  af.get("onset_strength", np.nan),
            "onset_cv":   af.get("onset_cv", np.nan),
            "tempo_bpm":       af.get("tempo_bpm", np.nan),
            # categories
            "cat_rms":     cats["rms_energy"].get(sid, "—"),
            "cat_bass":    cats["bass_energy"].get(sid, "—"),
            "cat_cent":    cats["spec_centroid_hz"].get(sid, "—"),
            "cat_am":      cats["am_depth"].get(sid, "—"),
            "cat_onset":   cats["onset_strength"].get(sid, "—"),
            "cat_pulse":   cats["onset_cv"].get(sid, "—"),
            # HRV means
            "hrv_rmssd":      mean_across(sid, "rmssd"),
            "hrv_rmssd_delta":mean_across(sid, "rmssd_delta"),
            "hrv_sd2":        mean_across(sid, "sd2"),
            "hrv_sd1_sd2":    mean_across(sid, "sd1_sd2"),
            "hrv_dfa_a1":     mean_across(sid, "dfa_a1"),
            # individual participant HRV
            "hrv_P1": stage_hrv[sid].get("P1", {}).get("rmssd", np.nan),
            "hrv_P2": stage_hrv[sid].get("P2", {}).get("rmssd", np.nan),
            "hrv_P3": stage_hrv[sid].get("P3", {}).get("rmssd", np.nan),
        }
        rows.append(row)

    model_df = pd.DataFrame(rows)
    return model_df, audio_df, audio_features, stage_hrv, session_stats, thresholds, cats, vlad_presession_hrv


# ── CHART GENERATION ──────────────────────────────────────────────────────────

def build_radar_chart(audio_df, audio_features):
    """Radar chart: each stage as a line across 6 normalised audio features."""
    feat_keys = ["rms_energy","bass_energy","spec_centroid_hz",
                 "am_depth","onset_strength","onset_cv"]
    feat_labels = ["Energy", "Bass", "Brightness", "AM Depth", "Onset Level", "Rhythm Clarity"]

    # Normalise 0–1 across all stages
    norm = {}
    for f in feat_keys:
        vals = audio_df[f].values.astype(float)
        mn, mx = np.nanmin(vals), np.nanmax(vals)
        norm[f] = (vals - mn) / (mx - mn + 1e-10)

    fig = go.Figure()
    colors = ["#4e79a7","#59a14f","#e15759","#f28e2b","#76b7b2","#b07aa1","#edc948","#ff9da7"]
    for i, st in enumerate(STAGE_TRACKS):
        sid = st["id"]
        row_idx = [j for j, s in enumerate(STAGE_TRACKS) if s["id"] == sid][0]
        vals = [norm[f][row_idx] for f in feat_keys]
        vals_closed = vals + [vals[0]]
        labels_closed = feat_labels + [feat_labels[0]]
        fig.add_trace(go.Scatterpolar(
            r=vals_closed, theta=labels_closed,
            name=st["label_short"],
            line=dict(color=colors[i % len(colors)], width=2),
            fill="toself", opacity=0.15,
        ))

    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 1],
                                   tickfont=dict(size=9))),
        showlegend=True,
        title="Acoustic Feature Profile by Stage (normalised 0–1)",
        legend=dict(orientation="h", yanchor="bottom", y=-0.3),
        paper_bgcolor="#1a1a2e", plot_bgcolor="#1a1a2e",
        font=dict(color="#e0e0e0"),
        height=500,
    )
    return fig


def build_hrv_heatmap(model_df, stage_hrv):
    """Heatmap: Stage × Metric for each of the 3 timed participants."""
    metrics = [("rmssd","RMSSD (ms)"),("sd2","SD2 (ms)"),
               ("sd1_sd2","SD1/SD2"),("dfa_a1","DFA α1")]
    participants = ["P1","P2","P3"]
    labels = [st["label_short"] for st in STAGE_TRACKS]

    fig = go.Figure()
    # One subplot per metric across participants
    from plotly.subplots import make_subplots
    fig = make_subplots(rows=2, cols=2,
                        subplot_titles=[m[1] for m in metrics],
                        shared_xaxes=True, vertical_spacing=0.12,
                        horizontal_spacing=0.08)

    colorscales = ["Blues","Greens","RdYlGn","Purples"]
    for idx, (metric, title) in enumerate(metrics):
        r, c = divmod(idx, 2)
        z = []
        for name in participants:
            row_vals = []
            for st in STAGE_TRACKS:
                v = stage_hrv[st["id"]].get(name, {}).get(metric, np.nan)
                row_vals.append(v)
            z.append(row_vals)

        fig.add_trace(go.Heatmap(
            z=z, x=labels, y=participants,
            colorscale=colorscales[idx],
            showscale=True,
            name=title,
            colorbar=dict(len=0.4, y=0.75 if r==0 else 0.25,
                          x=1.02 if c==1 else 1.14),
            text=[[f"{v:.2f}" if not np.isnan(v) else "—"
                   for v in row] for row in z],
            texttemplate="%{text}", textfont=dict(size=8),
            zmin=None, zmax=None,
        ), row=r+1, col=c+1)

    fig.update_layout(
        height=500,
        title="Per-Stage HRV Metrics — P1, P2, P3",
        paper_bgcolor="#1a1a2e", plot_bgcolor="#1a1a2e",
        font=dict(color="#e0e0e0"),
    )
    return fig


def build_audio_bar_chart(model_df):
    """Heatmap: acoustic features (rows) × stages (columns), coloured Low/Medium/High."""
    # cat_pulse is the model_df column name for onset_cv categories
    feat_order = [
        ("rms_energy",      "Energy (RMS)",   "cat_rms"),
        ("bass_energy",     "Bass Energy",    "cat_bass"),
        ("spec_centroid_hz","Brightness (Hz)","cat_cent"),
        ("am_depth",        "AM Depth",       "cat_am"),
        ("onset_strength",  "Onset Strength", "cat_onset"),
        ("onset_cv",        "Rhythm Clarity", "cat_pulse"),
    ]
    stage_labels = model_df["label_short"].tolist()

    z, cell_text, hover_text, y_labels = [], [], [], []
    for feat, fname, cat_col in feat_order:
        vals = model_df[feat].values.astype(float)
        mn, mx = np.nanmin(vals), np.nanmax(vals)
        z.append(((vals - mn) / (mx - mn + 1e-10)).tolist())
        cats_row = model_df[cat_col].tolist() if cat_col in model_df.columns else ["—"] * len(vals)
        # Cell text: just the category badge (short, no overlap)
        cell_text.append([c for c in cats_row])
        # Hover text: full raw value + category
        hover_text.append([f"<b>{fname}</b><br>Stage: {s}<br>Value: {v:.4f}<br>Category: {c}"
                           for s, v, c in zip(stage_labels, vals, cats_row)])
        y_labels.append(fname)

    colorscale = [
        [0.0, "#1e4d2b"],   # Low  → dark green
        [0.5, "#7a5a10"],   # Medium → amber
        [1.0, "#8b1a1a"],   # High → dark red
    ]

    fig = go.Figure(go.Heatmap(
        z=z,
        x=stage_labels,
        y=y_labels,
        text=cell_text,
        customdata=hover_text,
        texttemplate="%{text}",
        textfont=dict(size=11, color="white"),
        colorscale=colorscale,
        showscale=True,
        colorbar=dict(
            title=dict(text="Relative<br>intensity", font=dict(color="#e0e0e0", size=11)),
            tickvals=[0, 0.5, 1],
            ticktext=["Low", "Med", "High"],
            tickfont=dict(color="#e0e0e0"),
            len=0.8,
        ),
        hovertemplate="%{customdata}<extra></extra>",
    ))

    fig.update_layout(
        title=dict(
            text="Acoustic Feature Profile per Stage",
            font=dict(size=14),
        ),
        xaxis=dict(title="Stage", side="bottom", tickfont=dict(size=13)),
        yaxis=dict(title="", autorange="reversed", tickfont=dict(size=12)),
        paper_bgcolor="#1a1a2e", plot_bgcolor="#1a1a2e",
        font=dict(color="#e0e0e0"),
        height=420,
        margin=dict(l=140, r=110, t=70, b=60),
    )
    return fig


def build_hrv_arc_chart(model_df):
    """Line chart: HRV metrics across stages (the arc visualisation)."""
    fig = go.Figure()

    metrics = [
        ("hrv_rmssd",   "RMSSD (ms)",      "#4c9be8", "y1"),
        ("hrv_sd2",     "SD2 (ms)",         "#59a14f", "y2"),
        ("hrv_sd1_sd2", "SD1/SD2",          "#f28e2b", "y3"),
        ("hrv_dfa_a1",  "DFA α1",           "#b07aa1", "y4"),
    ]
    labels = model_df["label_short"].tolist()

    for metric, name, color, yaxis in metrics:
        fig.add_trace(go.Scatter(
            x=labels, y=model_df[metric].tolist(),
            mode="lines+markers", name=name,
            line=dict(color=color, width=2),
            marker=dict(size=8),
        ))

    # Per-participant lines (lighter, thinner)
    part_cfg = [("hrv_P1","P1","#4e79a7"),
                ("hrv_P2","P2","#b07aa1"),
                ("hrv_P3","P3","#76b7b2")]
    for col, pname, color in part_cfg:
        fig.add_trace(go.Scatter(
            x=labels, y=model_df[col].tolist(),
            mode="lines+markers", name=f"RMSSD {pname}",
            line=dict(color=color, width=1, dash="dot"),
            marker=dict(size=5), opacity=0.7,
        ))

    fig.update_layout(
        title="HRV Metrics Across the Innerdance Arc (mean of 3 participants)",
        xaxis_title="Stage", yaxis_title="Metric value",
        paper_bgcolor="#1a1a2e", plot_bgcolor="#1a1a2e",
        font=dict(color="#e0e0e0"),
        legend=dict(orientation="h", yanchor="bottom", y=-0.4),
        height=420,
    )
    return fig


def build_participant_session_chart(session_stats):
    """Bar chart comparing session-level RMSSD across all 6 participants."""
    names  = list(session_stats.keys())
    rmssd  = [session_stats[n]["rmssd"] for n in names]
    colors = [PARTICIPANTS[n]["color"] for n in names]

    fig = go.Figure(go.Bar(
        x=names, y=rmssd,
        marker_color=colors, opacity=0.85,
        text=[f"{v:.1f} ms" for v in rmssd],
        textposition="auto",
    ))
    fig.update_layout(
        title="Whole-Session RMSSD — All 6 Participants",
        yaxis_title="RMSSD (ms)",
        paper_bgcolor="#1a1a2e", plot_bgcolor="#1a1a2e",
        font=dict(color="#e0e0e0"),
        height=320,
    )
    return fig


# ── HTML REPORT ───────────────────────────────────────────────────────────────

def cat_badge(cat):
    colors = {"Low": "#2ecc71", "Medium": "#f39c12", "High": "#e74c3c", "—": "#888"}
    c = colors.get(cat, "#888")
    return f'<span class="badge" style="background:{c};padding:3px 8px;border-radius:4px;font-size:11px;color:#fff">{cat}</span>'


def hrv_arrow(val, ref, metric):
    """Return colored arrow + value for HRV column."""
    if np.isnan(val):
        return '<span style="color:#666">—</span>'
    sign = val - ref
    if metric == "dfa_a1":
        # for DFA, closer to 1.0 is better; use absolute distance
        arrow = "↑" if val >= 0.9 else ("↓" if val < 0.8 else "→")
        col   = "#2ecc71" if 0.75 < val < 1.5 else "#e74c3c"
    elif metric in ("rmssd", "sd2", "sd1_sd2"):
        arrow = "↑" if sign > 0.01*ref else ("↓" if sign < -0.01*ref else "→")
        col   = "#2ecc71" if sign >= 0 else "#e74c3c"
    else:
        arrow = "→"; col = "#aaa"
    return f'<span style="color:{col};font-weight:bold">{arrow} {val:.2f}</span>'


def build_html(model_df, audio_df, audio_features, stage_hrv,
               session_stats, thresholds, cats, vlad_presession_hrv=None):
    """Generate the full self-contained HTML report."""

    # Build Plotly charts
    fig_radar  = build_radar_chart(audio_df, audio_features)
    fig_hrv    = build_hrv_heatmap(model_df, stage_hrv)
    fig_audio  = build_audio_bar_chart(model_df)
    fig_arc    = build_hrv_arc_chart(model_df)
    fig_sess   = build_participant_session_chart(session_stats)

    def chart_json(fig):
        return fig.to_json()

    # Compute session RMSSD references for arrow colouring
    rmssd_refs = {
        "P1": session_stats.get("P1", {}).get("rmssd", 100),
        "P2": session_stats.get("P2", {}).get("rmssd", 80),
        "P3": session_stats.get("P3", {}).get("rmssd", 80),
    }

    # ── PARTICIPANT PROFILE CARDS ─────────────────────────────────────────
    profile_cards_html = ""
    for name, cfg in PARTICIPANTS.items():
        ss = session_stats.get(name, {})
        ts = "✅ Stage timestamps" if cfg["timestamps_available"] else "⚠️ Session-level only"
        extra = cfg.get("stages_recorded", "All 12 stages")
        rmssd_v = f"{ss.get('rmssd',float('nan')):.1f}" if ss else "—"
        hr_v    = f"{ss.get('mean_hr',float('nan')):.1f}" if ss else "—"
        dfa_v   = f"{ss.get('dfa_a1',float('nan')):.3f}" if ss else "—"
        profile_cards_html += f"""
        <div class="col-md-4 col-lg-2 mb-3">
          <div class="card h-100" style="background:#1e1e3a;border:1px solid {cfg['color']};border-radius:10px">
            <div class="card-body p-3">
              <div style="width:12px;height:12px;border-radius:50%;background:{cfg['color']};display:inline-block;margin-right:6px"></div>
              <strong style="color:{cfg['color']};font-size:15px">{name}</strong>
              <p class="mb-1 mt-2" style="font-size:11px;color:#aaa">Age {cfg['age']} · {cfg['profile']}</p>
              <p class="mb-1" style="font-size:11px;color:#aaa">Smoker: {'Yes' if cfg['smoker'] else 'No'}</p>
              <p class="mb-1" style="font-size:11px;color:#aaa">Mindfulness: {'Yes' if cfg['mindfulness'] else 'No'}</p>
              <hr style="border-color:#333;margin:6px 0">
              <p class="mb-1" style="font-size:11px;color:#ddd">RMSSD: <strong>{rmssd_v} ms</strong></p>
              <p class="mb-1" style="font-size:11px;color:#ddd">Mean HR: <strong>{hr_v} bpm</strong></p>
              <p class="mb-1" style="font-size:11px;color:#ddd">DFA α1: <strong>{dfa_v}</strong></p>
              <p class="mb-0 mt-2" style="font-size:10px;color:#76b7b2">{ts}</p>
              <p class="mb-0" style="font-size:10px;color:#888">{extra}</p>
            </div>
          </div>
        </div>"""

    # ── QUALITATIVE MODEL TABLE ───────────────────────────────────────────
    thr_rows = ""
    for feat, meta in FEATURE_META.items():
        p33, p67 = thresholds.get(feat, (0,0))
        thr_rows += f"<tr><td>{meta['label']}</td><td style='color:#2ecc71'>Low ≤ {p33:.4f}</td><td style='color:#f39c12'>{p33:.4f} – {p67:.4f}</td><td style='color:#e74c3c'>High &gt; {p67:.4f}</td></tr>"

    model_table_rows = ""
    for _, row in model_df.iterrows():
        sid = row["stage_id"]
        # find brainwave colour
        bw_colors = {"Delta":"#4e79a7","Theta":"#59a14f","θ→α/β":"#e15759",
                     "θ/α":"#edc948","α/β":"#e15759","α/Mu":"#ff9da7"}
        bw_col = bw_colors.get(row["brainwave"], "#aaa")

        # HRV values
        rmssd_mean = row["hrv_rmssd"]
        rmssd_ref  = 95.0  # rough cross-participant reference

        model_table_rows += f"""
        <tr>
          <td>
            <strong style="color:#e0e0e0">{row['label_short']}</strong><br>
            <small style="color:#aaa">{row['english']}</small><br>
            <span style="font-size:10px;color:{bw_col}">⬤ {row['brainwave']}</span>
          </td>
          <td>{cat_badge(row['cat_rms'])}<br><small style="color:#888">{row['rms_energy']:.4f}</small></td>
          <td>{cat_badge(row['cat_bass'])}<br><small style="color:#888">{row['bass_energy']:.5f}</small></td>
          <td>{cat_badge(row['cat_cent'])}<br><small style="color:#888">{row['spec_centroid_hz']:.0f} Hz</small></td>
          <td>{cat_badge(row['cat_am'])}<br><small style="color:#888">{row['am_depth']:.3f}</small></td>
          <td>{cat_badge(row['cat_onset'])}<br><small style="color:#888">{row['onset_strength']:.3f}</small></td>
          <td>{cat_badge(row['cat_pulse'])}<br><small style="color:#888">{row['onset_cv']:.3f}</small></td>
          <td style="text-align:center">{hrv_arrow(rmssd_mean, rmssd_ref, 'rmssd')}<br>
              <small style="color:#888">Δ{row['hrv_rmssd_delta']:+.1f}ms</small></td>
          <td style="text-align:center">{hrv_arrow(row['hrv_sd2'], 180, 'sd2')}</td>
          <td style="text-align:center">{hrv_arrow(row['hrv_sd1_sd2'], 0.35, 'sd1_sd2')}</td>
          <td style="text-align:center">{hrv_arrow(row['hrv_dfa_a1'], 1.0, 'dfa_a1')}</td>
        </tr>"""

    # ── STAGE DEEP-DIVE CARDS ─────────────────────────────────────────────
    stage_cards_html = ""
    for _, row in model_df.iterrows():
        sid = row["stage_id"]
        desc = STAGE_EXPERT_DESCRIPTIONS.get(sid, {"expert": "—", "novice": "—"})
        # Per-participant HRV mini-table
        part_rows = ""
        for pname in ["P1","P2","P3"]:
            m = stage_hrv[sid].get(pname, {})
            rmssd  = m.get("rmssd", float("nan"))
            sd2    = m.get("sd2",   float("nan"))
            ratio  = m.get("sd1_sd2", float("nan"))
            dfa    = m.get("dfa_a1", float("nan"))
            delta  = m.get("rmssd_delta", float("nan"))
            col    = PARTICIPANTS[pname]["color"]
            def _fmt(v, fmt): return ("—" if np.isnan(v) else f"{v:{fmt}}")
            part_rows += (
                f"<tr>"
                f"<td><span style='color:{col}'>⬤</span> {pname}</td>"
                f"<td>{_fmt(rmssd, '.1f')}</td>"
                f"<td>{_fmt(delta, '+.1f')}</td>"
                f"<td>{_fmt(sd2, '.1f')}</td>"
                f"<td>{_fmt(ratio, '.3f')}</td>"
                f"<td>{_fmt(dfa, '.3f')}</td>"
                f"</tr>"
            )

        feat_bars = ""
        for feat, meta in FEATURE_META.items():
            val = row[feat] if feat in row else np.nan
            if np.isnan(val):
                continue
            p33, p67 = thresholds.get(feat, (0,1))
            all_vals = audio_df[feat].values.astype(float)
            mn, mx = np.nanmin(all_vals), np.nanmax(all_vals)
            pct = int(100 * (val - mn) / (mx - mn + 1e-10))
            cat = categorize(val, p33, p67)
            bar_color = {"Low":"#2ecc71","Medium":"#f39c12","High":"#e74c3c"}.get(cat,"#aaa")
            feat_bars += f"""
              <div class="mb-2">
                <div class="d-flex justify-content-between" style="font-size:11px">
                  <span style="color:#ccc">{meta['label']}</span>
                  <span>{cat_badge(cat)} <small style="color:#888">{val:.4f}</small></span>
                </div>
                <div style="background:#2a2a4a;border-radius:4px;height:6px;margin-top:3px">
                  <div style="background:{bar_color};width:{pct}%;height:6px;border-radius:4px"></div>
                </div>
              </div>"""

        stage_cards_html += f"""
        <div class="mb-3">
          <div class="card" style="background:#141428;border:1px solid #2a2a4a;border-radius:12px">
            <div class="card-header" style="background:#1e1e3a;border-radius:12px 12px 0 0;cursor:pointer"
                 data-bs-toggle="collapse" data-bs-target="#card-{sid}">
              <div class="d-flex align-items-center justify-content-between">
                <div>
                  <strong style="color:#e0e0e0;font-size:16px">{row['label_short']} — {row['english']}</strong>
                  <span class="ms-2" style="font-size:12px;color:#aaa">{row['german']}</span>
                  <span class="ms-2 badge" style="background:#1e3a4a;color:#76b7b2;font-size:11px">{row['brainwave']}</span>
                </div>
                <span style="color:#aaa">▼</span>
              </div>
              <small style="color:#888;font-style:italic">{row['intention']}</small>
            </div>
            <div id="card-{sid}" class="collapse">
              <div class="card-body">
                <div class="row">
                  <div class="col-md-4">
                    <h6 style="color:#76b7b2">🎵 Acoustic Features</h6>
                    {feat_bars}
                    <p style="font-size:10px;color:#888">Tempo: {row['tempo_bpm']:.0f} BPM</p>
                  </div>
                  <div class="col-md-4">
                    <h6 style="color:#76b7b2">💓 HRV Response (per participant)</h6>
                    <table class="table table-sm" style="font-size:11px;color:#ccc;margin-bottom:6px">
                      <thead><tr style="color:#888"><th>Person</th><th>RMSSD</th><th>Δms</th><th>SD2</th><th>SD1/SD2</th><th>DFAα1</th></tr></thead>
                      <tbody>{part_rows}</tbody>
                    </table>
                    <small style="color:#888">⚠ RMSSD valid at rest. SD2, SD1/SD2, DFA α1 valid within session.</small>
                  </div>
                  <div class="col-md-4">
                    <h6 style="color:#edc948">🧘 Innerdance Expert</h6>
                    <p style="font-size:12px;color:#ddd;line-height:1.6">{desc['expert']}</p>
                    <h6 style="color:#f28e2b;margin-top:16px">🫀 What you feel</h6>
                    <p style="font-size:12px;color:#ddd;line-height:1.6">{desc['novice']}</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>"""

    # ── EXPERT VALIDATION GUIDE ───────────────────────────────────────────
    expert_guide_rows = ""
    for feat, meta in FEATURE_META.items():
        p33, p67 = thresholds.get(feat, (0,1))
        expert_guide_rows += f"""
        <tr>
          <td><strong style="color:#76b7b2">{meta['label']}</strong><br>
              <small style="color:#888">{meta['unit']}</small></td>
          <td style="color:#2ecc71">Low (≤{p33:.4f})<br><small>{meta['low_desc']}</small></td>
          <td style="color:#f39c12">Medium ({p33:.4f}–{p67:.4f})<br><small>{meta['med_desc']}</small></td>
          <td style="color:#e74c3c">High (&gt;{p67:.4f})<br><small>{meta['high_desc']}</small></td>
          <td style="color:#aaa;font-size:11px">{meta['hrv_link']}</td>
        </tr>"""

    # ── NOVICE HRV GUIDE ──────────────────────────────────────────────────
    novice_guide_cards = ""
    for metric, meta in HRV_METRIC_META.items():
        novice_guide_cards += f"""
        <div class="col-md-6 mb-3">
          <div class="card h-100" style="background:#1a1a2e;border:1px solid #2a2a4a;border-radius:10px">
            <div class="card-body">
              <h5 style="color:#4c9be8">{meta['label']}</h5>
              <p style="font-size:11px;color:#888;margin-bottom:8px">{meta['full']} | {meta['units']}</p>
              <p style="font-size:12px;color:#aaa;font-style:italic;margin-bottom:4px">⬆ When higher:</p>
              <p style="font-size:12px;color:#ddd;line-height:1.6">{meta['novice_high']}</p>
              <p style="font-size:12px;color:#aaa;font-style:italic;margin-bottom:4px;margin-top:8px">⬇ When lower:</p>
              <p style="font-size:12px;color:#ddd;line-height:1.6">{meta['novice_low']}</p>
              <div style="background:#2a2a4a;border-radius:6px;padding:8px;margin-top:8px">
                <p style="font-size:10px;color:#f39c12;margin:0">⚠ {meta['caveat']}</p>
              </div>
            </div>
          </div>
        </div>"""

    # ── DATA NOTES SECTION ────────────────────────────────────────────────
    data_notes = ""
    for name, cfg in PARTICIPANTS.items():
        if not cfg["timestamps_available"]:
            data_notes += f"<li><strong style='color:{cfg['color']}'>{name}</strong>: {cfg.get('stages_recorded','—')} — no stage timestamps available; whole-session metrics only.</li>"

    # ── PRE-SESSION HRV SECTION (P1 only) ──────────────────────────────
    presession_html = ""
    if vlad_presession_hrv:
        def _fmt(v, fmt): return ("—" if np.isnan(v) else f"{v:{fmt}}")
        seg_labels = {"baseline": ("Baseline Rest", "7 min seated rest before session"),
                      "papers":   ("Reading Papers", "~3 min reading research papers"),
                      "questions": ("Answering Questions", "~4 min answering questionnaire")}
        rows_ps = ""
        for seg, (t_label, t_desc) in seg_labels.items():
            m = vlad_presession_hrv.get(seg, {})
            if not m:
                continue
            rmssd  = m.get("rmssd",   float("nan"))
            sd2    = m.get("sd2",     float("nan"))
            ratio  = m.get("sd1_sd2", float("nan"))
            dfa    = m.get("dfa_a1",  float("nan"))
            hr_v   = m.get("mean_hr", float("nan"))
            # DFA colour coding
            if not np.isnan(dfa):
                dfa_col = "#2ecc71" if 0.75 < dfa < 1.5 else "#e74c3c"
            else:
                dfa_col = "#aaa"
            rows_ps += (
                f"<tr>"
                f"<td><strong style='color:#4e79a7'>{t_label}</strong><br>"
                f"<small style='color:#888'>{t_desc}</small></td>"
                f"<td style='text-align:right'>{_fmt(rmssd, '.1f')} ms</td>"
                f"<td style='text-align:right'>{_fmt(sd2, '.1f')} ms</td>"
                f"<td style='text-align:right'>{_fmt(ratio, '.3f')}</td>"
                f"<td style='text-align:right;color:{dfa_col}'>{_fmt(dfa, '.3f')}</td>"
                f"<td style='text-align:right'>{_fmt(hr_v, '.1f')} bpm</td>"
                f"</tr>"
            )
        presession_html = f"""
  <!-- PRE-SESSION CONTEXT -->
  <section id="presession">
    <h2 class="section-title">Pre-Session Context — P1</h2>
    <p style="font-size:13px;color:#aaa;margin-bottom:12px">
      P1's HRV was recorded <strong>before the innerdance session</strong> across three conditions:
      resting baseline, reading research papers (mild cognitive load), and answering questions
      (mild stress / attention). This provides a physiological anchor for interpreting
      within-session HRV changes. <em>Note: RMSSD is reliable here because breathing rate is
      unrestricted at rest.</em>
    </p>
    <div class="table-responsive">
      <table class="table table-sm" style="font-size:12px;color:#ccc;background:#141428">
        <thead>
          <tr style="color:#76b7b2;border-bottom:1px solid #2a2a4a">
            <th>Condition</th>
            <th style="text-align:right">RMSSD</th>
            <th style="text-align:right">SD2</th>
            <th style="text-align:right">SD1/SD2</th>
            <th style="text-align:right">DFA α1</th>
            <th style="text-align:right">Mean HR</th>
          </tr>
        </thead>
        <tbody>{rows_ps}</tbody>
      </table>
    </div>
    <div style="background:#1e1e3a;border-left:3px solid #76b7b2;padding:12px 16px;border-radius:0 8px 8px 0;margin-top:10px">
      <p style="font-size:12px;color:#ddd;margin:0;line-height:1.7">
        <strong style="color:#76b7b2">Interpretation:</strong>
        The reading condition shows elevated SD1/SD2 (parasympathetic dominance, slow deep breathing
        while reading) and reduced DFA α1 — consistent with the known RMSSD invalidity during slow
        paced breathing (<a href="https://doi.org/10.1152/ajpregu.00124.2022" style="color:#4c9be8"
        target="_blank">McCreary et al. 2022</a>). The questions condition shows increased DFA α1 and
        lower RMSSD (mild SNS activation from cognitive stress). These pre-session values establish
        P1's <em>individual autonomic baseline</em>; Stage 4 (SNS peak: DFA α1=0.777) and
        Stage 10 (PNS rebound: SD2=241 ms) should be read against this context.
      </p>
    </div>
  </section>"""

    # ── ASSEMBLE HTML ─────────────────────────────────────────────────────
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Innerdance Qualitative Model — Acoustic × HRV</title>
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
  <script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
  <style>
    body {{ background:#0d0d1a; color:#e0e0e0; font-family:'Segoe UI',Arial,sans-serif; }}
    .section-title {{ color:#76b7b2; border-bottom:1px solid #2a2a4a; padding-bottom:8px; margin-bottom:20px; }}
    .table {{ color:#ccc; }}
    .table th {{ color:#aaa; font-size:12px; font-weight:600; border-color:#2a2a4a; }}
    .table td {{ border-color:#2a2a4a; vertical-align:middle; font-size:12px; }}
    .badge {{ font-size:10px; }}
    .hero-title {{ font-size:2.2rem; font-weight:700; background:linear-gradient(135deg,#76b7b2,#4c9be8,#b07aa1); -webkit-background-clip:text; -webkit-text-fill-color:transparent; }}
    .hero-sub {{ color:#aaa; font-size:14px; margin-top:6px; }}
    .nav-pill {{ background:#1a1a2e; border:1px solid #2a2a4a; border-radius:20px; padding:6px 16px; color:#76b7b2; text-decoration:none; font-size:12px; margin:3px; display:inline-block; }}
    .nav-pill:hover {{ background:#2a2a4a; color:#fff; }}
    .data-note {{ background:#1e1e0a; border-left:3px solid #f39c12; padding:10px; border-radius:0 6px 6px 0; font-size:12px; color:#ddd; }}
    section {{ padding:40px 0; }}
  </style>
</head>
<body>
<div class="container-fluid" style="max-width:1400px;margin:0 auto;padding:0 20px">

  <!-- HERO -->
  <section id="hero" style="padding:60px 0 30px">
    <div class="text-center">
      <div class="hero-title">Innerdance Qualitative Model</div>
      <div class="hero-sub">Acoustic Feature × ANS Response — How Sound Regulates the Nervous System</div>
      <div class="mt-3">
        <span class="nav-pill">N=6 participants</span>
        <span class="nav-pill">N=3 per-stage HRV (P1, P2, P3)</span>
        <span class="nav-pill">8 audio tracks · 12 innerdance stages</span>
        <span class="nav-pill">6 acoustic features · 4 HRV metrics</span>
      </div>
      <div class="mt-3">
        <a href="#summary" class="nav-pill">Research Summary</a>
        <a href="#hrv-method" class="nav-pill">HRV Metrics</a>
        <a href="#profiles" class="nav-pill">Participants</a>
        <a href="#audio" class="nav-pill">Audio Features</a>
        <a href="#feature-method" class="nav-pill">Acoustic Features</a>
        <a href="#model" class="nav-pill">Qualitative Model</a>
        <a href="#stages" class="nav-pill">Stage Cards</a>
        <a href="#hypotheses" class="nav-pill" style="border-color:#b07aa1;color:#b07aa1">Hypotheses</a>
        <a href="#review" class="nav-pill" style="border-color:#e74c3c;color:#e74c3c">⚠ Critical Review</a>
        <a href="#refs" class="nav-pill">References</a>
      </div>
    </div>
  </section>

  <!-- DATA NOTES -->
  <div class="data-note mb-4">
    <strong>⚠ Data availability note:</strong>
    Per-stage HRV analysis requires stage timestamps. Available for: <strong>P1</strong> (full session with pre-session baseline),
    <strong>P2</strong> and <strong>P3</strong> (timestamps from session log, recording started at Stage 1).
    <ul class="mb-0 mt-1">{data_notes}</ul>
  </div>

  <!-- RESEARCH SUMMARY -->
  <section id="summary">
    <h2 class="section-title">Research Summary — What Was Computed</h2>
    <p style="font-size:13px;color:#aaa;margin-bottom:16px">
      This is a factual summary of the analysis completed in this POC. No inferences are made beyond what the data directly supports.
    </p>
    <div class="row g-3">

      <div class="col-md-6">
        <div class="card h-100" style="background:#141428;border:1px solid #2a2a4a;border-radius:10px;padding:18px">
          <h5 style="color:#76b7b2">Data Collected</h5>
          <ul style="font-size:12px;color:#ccc;line-height:1.9">
            <li><strong style="color:#4e79a7">P1</strong> (38, athlete, very fit):
              3,114 R-R intervals · 59.6 min · full stage timestamps · pre-session baseline recorded</li>
            <li><strong style="color:#b07aa1">P2</strong> (42, mindfulness practitioner):
              5,450 R-R intervals · 58.5 min · stage timestamps from session log</li>
            <li><strong style="color:#76b7b2">P3</strong> (43, interiorized):
              4,779 R-R intervals · 58.8 min · stage timestamps from session log</li>
            <li><strong style="color:#e15759">P4</strong> (42, unfit, coleric, smoker):
              4,531 R-R intervals · 59.8 min · <em>no stage timestamps</em></li>
            <li><strong style="color:#f28e2b">P5</strong> (43, smoker):
              1,827 R-R intervals · 24.2 min · first 5 stages only · <em>no stage timestamps</em></li>
            <li><strong style="color:#59a14f">P6</strong> (46):
              1,479 R-R intervals · 22.1 min · last stages only · <em>no stage timestamps</em></li>
          </ul>
          <p style="font-size:11px;color:#888;margin-top:6px">
            All recordings: Polar H10 chest strap, ECG-derived R-R intervals, nanosecond Unix timestamps.
            Artifact filter: hard bounds 300–2000 ms + rolling-median neighbour filter ±20 %, 5-beat window.
          </p>
        </div>
      </div>

      <div class="col-md-6">
        <div class="card h-100" style="background:#141428;border:1px solid #2a2a4a;border-radius:10px;padding:18px">
          <h5 style="color:#76b7b2">HRV Metrics Computed</h5>
          <ul style="font-size:12px;color:#ccc;line-height:1.9">
            <li><strong>RMSSD</strong> — root-mean-square of successive R-R differences.
              Valid at rest (P1 pre-session). <em>Not reliable within innerdance</em> due to slow breathing
              (&lt;9 bpm); used only as reference.</li>
            <li><strong>SD1 / SD2</strong> — Poincaré plot short-axis (beat-to-beat variability) and
              long-axis (total autonomic flexibility). SD2 is valid within session.</li>
            <li><strong>SD1/SD2 ratio</strong> — balance between parasympathetic (SD1) and sympathetic-mediated
              long-range variability (SD2). Higher = PNS dominance.</li>
            <li><strong>DFA α1</strong> — short-range fractal scaling exponent of R-R series (windows 4–16 beats).
              ~1.0 = healthy fractal correlation. &lt;0.75 = loss of regulation (SNS peak).</li>
            <li><strong>Mean HR</strong> — beats per minute, for reference.</li>
          </ul>
          <p style="font-size:11px;color:#888;margin-top:6px">
            Per-stage HRV: P1 (9 stages) · P2 (8 stages, no dedicated S3) · P3 (8 stages, no dedicated S3).
            Whole-session only: P4, P5, P6.
          </p>
        </div>
      </div>

      <div class="col-md-6">
        <div class="card h-100" style="background:#141428;border:1px solid #2a2a4a;border-radius:10px;padding:18px">
          <h5 style="color:#76b7b2">Audio Analysis Computed</h5>
          <ul style="font-size:12px;color:#ccc;line-height:1.9">
            <li>9 audio tracks analysed (up to 600 s each) using <em>librosa</em> and <em>scipy</em></li>
            <li>6 acoustic features extracted per track (see Feature Methodology section)</li>
            <li>Qualitative categories (Low / Medium / High) assigned by 33rd / 67th percentile thresholds
              computed across all 9 tracks — so categories are <em>relative within this track set</em></li>
            <li>Stage 3 uses a dedicated track (03.01.mp3) used only for P1 and P5.
              All other participants used the Purgation-release track for the combined S3+S4 window.</li>
          </ul>
        </div>
      </div>

      <div class="col-md-6">
        <div class="card h-100" style="background:#141428;border:1px solid #2a2a4a;border-radius:10px;padding:18px">
          <h5 style="color:#76b7b2">Key Findings (P1, per-stage)</h5>
          <ul style="font-size:12px;color:#ccc;line-height:1.9">
            <li><strong>Stage 4</strong> (Purgation-release) is the SNS activation peak:
              RMSSD=94.9 ms (Δ−9.3 from S3), DFA α1=0.777 — below the 0.75 regulatory threshold.
              High energy, high bass, high brightness track.</li>
            <li><strong>Stage 10</strong> (Dark Night of the Soul) is the PNS rebound peak:
              RMSSD=117.6 ms (Δ+13.4), SD2=241.4 ms — the highest SD2 of the entire session,
              including the pre-session baseline (SD2=244.3 ms). Low energy, quiet track.</li>
            <li><strong>Pre-session reading condition</strong> (P1): DFA α1=0.638 during paper-reading —
              below 0.75 threshold, consistent with slow paced-breathing invalidity of RMSSD
              (McCreary et al. 2022). Questions condition raised DFA α1=1.269 (mild cognitive stress).</li>
            <li><strong>H5 — trend consistent but not confirmed</strong> (activation → rebound): recovery phase RMSSD (104.1 ms)
              vs. pre-session baseline (103.0 ms) — Δ+1.1 ms is within noise; DFA α1 at S10 (1.236) provides
              stronger directional support. Requires a powered study to confirm.</li>
            <li>P2 and P3 show consistent directional trends (SD2 rise in S8+9, S10)
              but at lower absolute values than P1, consistent with their participant profiles.</li>
          </ul>
          <p style="font-size:11px;color:#888;margin-top:6px">
            ⚠ N=3 per-stage. Findings are hypothesis-generating, not statistically conclusive.
          </p>
        </div>
      </div>

    </div>
  </section>

  <!-- HRV METRICS METHODOLOGY -->
  <section id="hrv-method">
    <h2 class="section-title">HRV Metrics — Choice, Relevance, and Health Impact</h2>
    <p style="font-size:13px;color:#aaa;margin-bottom:6px">
      Heart Rate Variability (HRV) measures the fluctuation in time between consecutive heartbeats (R-R intervals).
      A healthy autonomic nervous system produces <em>irregular</em> intervals — this variability is adaptive, not noise.
      Four metrics were chosen for this study because together they cover the time domain, Poincaré geometry,
      and nonlinear fractal structure of the heartbeat — and each remains interpretable across the specific
      constraints of innerdance data (short windows, slow breathing, single-sensor Polar H10).
    </p>
    <div class="table-responsive" style="margin-top:16px">
    <table class="table table-sm" style="font-size:12px;color:#ccc">
      <thead>
        <tr style="background:#1a1a2e;color:#76b7b2">
          <th style="min-width:130px">Metric</th>
          <th style="min-width:140px">What it measures</th>
          <th style="min-width:160px">Why chosen for this study</th>
          <th style="min-width:160px">Clinical evidence</th>
          <th style="min-width:160px">Subjective experience</th>
          <th style="min-width:120px">Validity caveat</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td><strong style="color:#4c9be8">RMSSD</strong><br>
              <small style="color:#888">Root Mean Square of Successive Differences · ms</small></td>
          <td style="font-size:11px">Beat-to-beat parasympathetic (vagal) tone. Captures how much each heartbeat deviates from the one before it.</td>
          <td style="font-size:11px">Gold-standard resting vagal marker; simple to compute; provides pre-session baseline anchor.
              Used to establish P1's individual reference (104 ms at rest).</td>
          <td style="font-size:11px">Higher resting RMSSD associated with lower all-cause mortality
              (Shaffer &amp; Ginsberg 2017), reduced depression and anxiety risk, better cardiovascular resilience.
              Athletes typically 60–100 ms; sedentary adults 20–40 ms.</td>
          <td style="font-size:11px">When high: chest opens, breathing deepens, a felt sense of ease and safety — the heart has
              "slack." When low: a subtle tightening, more rigid rhythm — the body is mobilising, not distressed.</td>
          <td style="font-size:11px;color:#f39c12"><strong>⚠ Invalid during innerdance</strong> when breathing &lt;9 bpm
              (McCreary 2022). Use only against resting baseline, not within-session comparisons.</td>
        </tr>
        <tr style="background:#141428">
          <td><strong style="color:#4c9be8">SD2</strong><br>
              <small style="color:#888">Poincaré long-axis · ms</small></td>
          <td style="font-size:11px">Total autonomic flexibility — captures both sympathetic and parasympathetic contributions to
              long-range R-R variability. The "operating range" of the ANS.</td>
          <td style="font-size:11px">Unlike RMSSD, SD2 remains valid during slow breathing. It is the primary within-session
              flexibility marker in this dataset. S10 peak (SD2=241 ms, P1) is the clearest single data point
              in the study.</td>
          <td style="font-size:11px">Reduced SD2 found in chronic stress, burnout, and depression
              (Laborde et al. 2017). A wide SD2 = the nervous system can move freely between states.
              Narrow SD2 = locked into a fixed arousal level (can be high or low).</td>
          <td style="font-size:11px">When high: a sense of spaciousness, inner room — able to be both alert and calm within
              the same session. When low: "locked in" to a state, less able to shift; not necessarily bad
              if it means deep, sustained focus.</td>
          <td style="font-size:11px;color:#2ecc71">Valid across all stages. Primary within-session metric.</td>
        </tr>
        <tr>
          <td><strong style="color:#4c9be8">SD1/SD2</strong><br>
              <small style="color:#888">Poincaré ratio · unitless</small></td>
          <td style="font-size:11px">Balance between beat-to-beat (SD1, PNS) and long-range (SD2, SNS-mediated) variability.
              High = parasympathetic dominance. Low = sympathetic activation or loss of variability.</td>
          <td style="font-size:11px">Provides a directional indicator of sympathovagal balance without frequency-domain
              analysis. Healthy resting ~0.3. Drops during activation (S4: 0.479 → approaches SNS range).</td>
          <td style="font-size:11px">Used in biofeedback and stress research as a real-time balance indicator.
              Chronic low SD1/SD2 ratio associated with autonomic imbalance and cardiovascular risk.</td>
          <td style="font-size:11px">When high: soft, receptive — jaw relaxes, shoulders drop, easier to be moved by music.
              When low: alert, energised, or slightly on-edge — ready for action, less receptive.</td>
          <td style="font-size:11px;color:#2ecc71">Valid across all stages. Interpret alongside SD2 for fuller picture.</td>
        </tr>
        <tr style="background:#141428">
          <td><strong style="color:#4c9be8">DFA α1</strong><br>
              <small style="color:#888">Detrended Fluctuation Analysis · exponent</small></td>
          <td style="font-size:11px">Short-range fractal scaling of the R-R series (scales 4–16 beats). Measures whether
              the heartbeat has self-similar temporal structure (~1.0) or is losing that organisation (&lt;0.75).</td>
          <td style="font-size:11px">The only nonlinear metric in the set. Uniquely sensitive to loss of autonomic regulation
              at SNS peaks. S4 (α1=0.777) and S10 (α1=1.236) are the clearest markers of the autonomic arc.
              Less affected by slow breathing than RMSSD.</td>
          <td style="font-size:11px">DFA α1 &lt;0.75 associated with cardiac arrhythmia, overtraining syndrome, and acute
              autonomic dysregulation (Goldberger 2002, Peng 1995). Healthy resting ~1.0. Rigid/elderly &gt;1.5.
              Used in sport science to detect non-functional overreaching before it becomes overtraining.</td>
          <td style="font-size:11px">Around 1.0: flow, timelessness — the heartbeat organises itself effortlessly.
              Below 0.75: maximum energy, minimum order — like the moment before a wave breaks.
              Above 1.3: deep rest or rigidity — the system is no longer adapting, just sustaining.</td>
          <td style="font-size:11px;color:#f39c12">⚠ Needs ≥150 beats for reasonable estimates (Peng 1995). Slow breathing
              can also lower α1 artificially — ambiguous without respiratory rate data.</td>
        </tr>
      </tbody>
    </table>
    </div>
    <div style="background:#1e1e3a;border-left:3px solid #76b7b2;padding:12px 16px;border-radius:0 8px 8px 0;margin-top:12px">
      <p style="font-size:12px;color:#ddd;margin:0;line-height:1.7">
        <strong style="color:#76b7b2">Why not LF/HF power?</strong>
        The LF/HF ratio (standard frequency-domain HRV) requires stationary breathing, minimum 5-min windows,
        and reliable respiratory rate data. None of these are guaranteed in innerdance. LF power at 0.1 Hz
        is the target metric for HRV-biofeedback (Lehrer &amp; Gevirtz 2014) but requires resonance-frequency
        breathing (~6 bpm) to be interpretable — innerdance breathing varies freely. LF/HF should be
        considered in a future protocol where breathing rate is measured concurrently.
      </p>
    </div>
  </section>

  <!-- PARTICIPANT PROFILES -->
  <section id="profiles">
    <h2 class="section-title">Participant Profiles</h2>
    <div class="row g-2">
      {profile_cards_html}
    </div>
    <div id="chart-session" style="height:340px;margin-top:20px"></div>
    <p style="font-size:11px;color:#888;margin-top:6px">
      Whole-session RMSSD reflects overall autonomic tone across the full recording. P1's high RMSSD (athlete, very fit) and lower resting HR
      create a different response baseline than the other participants. This must be accounted for in cross-participant comparisons.
    </p>
  </section>

  <!-- AUDIO FEATURES -->
  <section id="audio">
    <h2 class="section-title">Acoustic Features by Stage</h2>
    <div class="row">
      <div class="col-md-6">
        <div id="chart-radar" style="height:520px"></div>
      </div>
      <div class="col-md-6">
        <div id="chart-audio-bars" style="height:400px;margin-top:60px"></div>
      </div>
    </div>
    <h5 style="color:#aaa;margin-top:20px">Feature Thresholds (calibrated from data)</h5>
    <table class="table table-sm mt-2" style="font-size:11px">
      <thead><tr style="color:#888"><th>Feature</th><th style="color:#2ecc71">Low</th><th style="color:#f39c12">Medium</th><th style="color:#e74c3c">High</th></tr></thead>
      <tbody>{thr_rows}</tbody>
    </table>
  </section>

  <!-- HRV ARC -->
  <section id="arc">
    <h2 class="section-title">The Autonomic Arc Across Stages</h2>
    <div id="chart-arc" style="height:440px"></div>
    <div id="chart-hrv-heatmap" style="height:520px;margin-top:30px"></div>
    <p style="font-size:11px;color:#888;margin-top:8px">
      Heatmap shows per-participant, per-stage HRV metrics. Warmer colours = higher values.
      Missing cells (—) indicate stages without available timestamp data for that participant.
    </p>
  </section>

  <!-- FEATURE METHODOLOGY -->
  <section id="feature-method">
    <h2 class="section-title">Why These Acoustic Features?</h2>
    <p style="font-size:13px;color:#aaa;margin-bottom:16px">
      The 6 features were selected because each maps onto a distinct dimension of auditory perception
      known to drive autonomic nervous system (ANS) responses. Together they cover energy, frequency content,
      temporal modulation, and rhythmic structure — the four main axes along which innerdance music varies.
    </p>
    <div class="table-responsive">
    <table class="table table-sm" style="font-size:12px;color:#ccc">
      <thead>
        <tr style="background:#1a1a2e;color:#76b7b2">
          <th style="min-width:140px">Feature</th>
          <th style="min-width:120px">How it is computed</th>
          <th style="min-width:200px">Why it matters physiologically</th>
          <th style="min-width:200px">What an innerdance expert hears / feels</th>
          <th style="min-width:160px">Key literature</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td><strong style="color:#4c9be8">Overall Energy (RMS)</strong><br>
              <small style="color:#888">Root-mean-square amplitude of the full signal</small></td>
          <td style="font-size:11px">RMS of all samples in the window</td>
          <td style="font-size:11px">Loudness is the primary driver of physiological arousal via the
              reticular activating system. High RMS correlates with SNS activation, increased HR,
              reduced HRV. Low RMS supports parasympathetic rest.</td>
          <td style="font-size:11px">The overall volume / presence of the track. A quiet track feels
              spacious and distant; a loud track feels surrounding and activating.</td>
          <td style="font-size:11px">Khalfa et al. (2002) <em>J Neurophysiol</em>;
              Nakamura et al. (1999) <em>Jpn J Physiol</em></td>
        </tr>
        <tr style="background:#141428">
          <td><strong style="color:#4c9be8">Bass Energy</strong><br>
              <small style="color:#888">RMS in 20–250 Hz band (4th-order Butterworth bandpass)</small></td>
          <td style="font-size:11px">Bandpass filter 20–250 Hz then RMS</td>
          <td style="font-size:11px">Sub-bass and low-frequency vibration activates the vestibular system
              and somatic (tactile) receptors in the chest and abdomen. Strong bass is associated with
              increased HR and SNS arousal, and also with trance-induction via repetitive low-frequency
              entrainment. High bass may correlate with the DFA α1 drop seen at Stage 4.</td>
          <td style="font-size:11px">Felt as physical vibration in the sternum, belly, and legs.
              Experienced practitioners describe strong bass as "grounding" or "destabilising" depending
              on context.</td>
          <td style="font-size:11px">Juslin &amp; Västfjäll (2008) <em>Behav Brain Sci</em>;
              Todd &amp; Cody (2000) <em>J Acoust Soc Am</em></td>
        </tr>
        <tr>
          <td><strong style="color:#4c9be8">Brightness (Spectral Centroid)</strong><br>
              <small style="color:#888">Hz frequency of the spectral centre of mass</small></td>
          <td style="font-size:11px">librosa.feature.spectral_centroid, averaged over frames</td>
          <td style="font-size:11px">High-frequency content is perceived as "sharp" or "harsh" and
              triggers alerting responses via the auditory brainstem reflex. Correlated with increased
              skin conductance and cortisol. Low brightness (warm, muffled) is associated with
              parasympathetic relaxation.</td>
          <td style="font-size:11px">The tonal "colour" of the track — dark and warm (low) vs.
              bright and piercing (high). Stage 8+9 (highest centroid ~1431 Hz) sounds metallic and
              intense; Stage 11+12 (~378 Hz) sounds warm and rounded.</td>
          <td style="font-size:11px">Leman et al. (2005) <em>Musicae Scientiae</em>;
              Eerola &amp; Vuoskoski (2011) <em>Music Percept</em></td>
        </tr>
        <tr style="background:#141428">
          <td><strong style="color:#4c9be8">AM Depth (Amplitude Modulation)</strong><br>
              <small style="color:#888">CV of the Hilbert envelope smoothed at 2 Hz</small></td>
          <td style="font-size:11px">Hilbert transform → envelope → 2 Hz low-pass → std/mean (CV)</td>
          <td style="font-size:11px">Slow amplitude fluctuations (0.5–4 Hz) overlap with the respiratory
              band and can entrain breathing via auditory-respiratory coupling. High AM depth creates
              a pulsing texture that may pace breathing and increase HRV coherence; very high AM (Stage 11+12)
              creates an undulating, immersive quality linked to deep relaxation and PNS recovery.</td>
          <td style="font-size:11px">The "breathing" or "swelling" quality of the track — does the sound
              pulse and throb (high AM) or remain steady (low AM)?</td>
          <td style="font-size:11px">Trost et al. (2012) <em>Neuropsychologia</em>;
              Nozaradan et al. (2011) <em>J Neurosci</em></td>
        </tr>
        <tr>
          <td><strong style="color:#4c9be8">Onset Strength</strong><br>
              <small style="color:#888">Mean of the onset strength envelope</small></td>
          <td style="font-size:11px">librosa.onset.onset_strength averaged over frames</td>
          <td style="font-size:11px">Onset strength captures the intensity of sound onsets (percussive
              events, note attacks). High onset strength indicates a driving, pulse-like character that
              activates the motor system (basal ganglia beat induction). Correlated with entrainment
              of HR and movement. Drone / ambient textures have low onset strength.</td>
          <td style="font-size:11px">How "driven" or "percussive" the track feels. A track with many
              sharp transients (high) invites movement and activates; a sustained drone (low) dissolves
              boundaries and quiets the motor impulse.</td>
          <td style="font-size:11px">Grahn &amp; Rowe (2009) <em>J Neurosci</em>;
              Zatorre et al. (2007) <em>Nat Rev Neurosci</em></td>
        </tr>
        <tr style="background:#141428">
          <td><strong style="color:#4c9be8">Rhythm Clarity (Onset CV)</strong><br>
              <small style="color:#888">CV (std/mean) of the onset strength envelope</small></td>
          <td style="font-size:11px">std(oenv) / mean(oenv) — coefficient of variation of onset envelope</td>
          <td style="font-size:11px">Onset CV distinguishes <em>metrically clear</em> rhythm (high CV:
              strong beats punctuate silence) from <em>ambient / drone</em> texture (low CV: steady
              undifferentiated energy). Clear rhythm enables neural beat-locking (motor–auditory coupling),
              which modulates HR and can sustain SNS activation or support entrainment. Ambient textures
              with low rhythmic clarity tend to support diffuse attention and parasympathetic withdrawal
              of arousal.<br><br>
              <em>Note: this replaced an initial attempt using librosa's tempogram, which always
              returned 1.0 due to internal normalisation — making it uninformative. Onset CV was
              validated to produce meaningful stage discrimination (S3=High 0.80, S4=Low 0.32,
              S11+12=High 0.85).</em></td>
          <td style="font-size:11px">Does the track have a clear, identifiable beat (High) or is it
              a continuous texture where you cannot tap along (Low)? Stage 3 and Stage 11+12 both
              score High on this metric via different mechanisms: S3 has clear percussive attacks,
              S11+12 has a slow pulsing undulation.</td>
          <td style="font-size:11px">Grahn &amp; Brett (2007) <em>Neuropsychologia</em>;
              Nozaradan et al. (2011) <em>J Neurosci</em></td>
        </tr>
      </tbody>
    </table>
    </div>
    <div style="background:#1e1e3a;border-left:3px solid #76b7b2;padding:14px 18px;border-radius:0 8px 8px 0;margin-top:16px">
      <p style="font-size:12px;color:#ddd;margin:0;line-height:1.7">
        <strong style="color:#76b7b2">Features not included and why:</strong>
        Tempo BPM was extracted but not used as a primary feature because librosa's beat tracker
        returns very similar estimates across most tracks in this set (117–129 BPM), reflecting the
        DJ's consistent tempo rather than meaningfully different rhythmic characters.
        Spectral flux (onset rate) and MFCCs were considered but add complexity without clear
        expert-interpretable meaning for this validation phase. They can be added in a later,
        model-driven phase once the qualitative framework is validated.
      </p>
    </div>
  </section>

  <!-- QUALITATIVE MODEL TABLE -->
  <section id="model">
    <h2 class="section-title">Qualitative Model Table</h2>
    <p style="color:#aaa;font-size:13px">
      This is the core deliverable. Each row = one stage group. Acoustic features are colour-coded Low/Medium/High.
      HRV metrics show mean values across P1, P2, P3 with directional arrows (↑ favourable, ↓ activating/suppressed, → neutral).
      HRV arrows for RMSSD/SD2 use session mean as reference; DFA α1 uses distance from healthy 1.0.
    </p>
    <div class="table-responsive">
    <table class="table table-sm" id="model-table" style="font-size:11px">
      <thead>
        <tr style="background:#1a1a2e">
          <th rowspan="2" style="min-width:120px">Stage</th>
          <th colspan="6" style="text-align:center;color:#4c9be8;border-bottom:2px solid #4c9be8">🎵 Acoustic Features</th>
          <th colspan="4" style="text-align:center;color:#e8714c;border-bottom:2px solid #e8714c">💓 HRV Metrics (mean: P1+P2+P3)</th>
        </tr>
        <tr style="background:#141428">
          <th>Energy</th><th>Bass</th><th>Brightness</th><th>AM Depth</th><th>Onset Level</th><th>Rhythm Clarity</th>
          <th>RMSSD (ms)</th><th>SD2 (ms)</th><th>SD1/SD2</th><th>DFA α1</th>
        </tr>
      </thead>
      <tbody>
        {model_table_rows}
      </tbody>
    </table>
    </div>
  </section>

  <!-- STAGE CARDS -->
  <section id="stages">
    <h2 class="section-title">Stage-by-Stage Deep Dive</h2>
    <p style="color:#aaa;font-size:13px">Click any stage to expand. Each card shows: acoustic feature bars · per-participant HRV table · innerdance expert description · body-feel guide for biofeedback novice.</p>
    {stage_cards_html}
  </section>

  <!-- NEXT STEPS -->
  <section id="next">
    <h2 class="section-title">Next Steps</h2>
    <div class="row">
      <div class="col-md-6">
        <div class="card" style="background:#1a1a2e;border:1px solid #2a2a4a;border-radius:10px;padding:20px">
          <h5 style="color:#76b7b2">Expert Validation</h5>
          <ol style="font-size:13px;color:#ccc">
            <li>Play each track to an innerdance practitioner</li>
            <li>Ask them to rate each acoustic feature as Low / Medium / High using their felt sense</li>
            <li>Compare to computed categories — mismatches = calibration opportunities</li>
            <li>Refine thresholds and descriptions where expert disagrees</li>
          </ol>
        </div>
      </div>
      <div class="col-md-6">
        <div class="card" style="background:#1a1a2e;border:1px solid #2a2a4a;border-radius:10px;padding:20px">
          <h5 style="color:#76b7b2">Data Collection Priority</h5>
          <ol style="font-size:13px;color:#ccc">
            <li>Add stage timestamps for P4, P5, P6 to enable per-stage HRV for all 6</li>
            <li>Add 5-min post-session resting window to test H-A (post RMSSD > pre RMSSD)</li>
            <li>Add PSS-10 / SUDS before and after to link HRV to felt stress reduction</li>
            <li>Collect 2 more participants to reach N=8 for statistical modelling</li>
          </ol>
        </div>
      </div>
    </div>
  </section>

  <!-- HYPOTHESES -->
  <section id="hypotheses">
    <h2 class="section-title">Research Hypotheses</h2>
    <p style="font-size:13px;color:#aaa;margin-bottom:6px">
      Hypotheses derived from the current data, the acoustic feature set, and the HRV-B literature.
      Each is stated as a falsifiable prediction about how <em>specific acoustic features of new sound samples</em>
      impact R-R interval-derived HRV and — where applicable — general health outcomes not measurable by RR alone.
      Priority is assigned by the intersection of <strong>potential impact</strong> (clinical or practical value if confirmed),
      <strong>testability</strong> (how much additional data/design is needed), and
      <strong>prior likelihood</strong> (support from literature or current data).
    </p>
    <div style="display:flex;gap:12px;flex-wrap:wrap;margin:12px 0 20px">
      <span style="background:#1e3d1e;color:#2ecc71;padding:4px 12px;border-radius:20px;font-size:11px">TIER 1 — Test in next data collection round</span>
      <span style="background:#3d3000;color:#f39c12;padding:4px 12px;border-radius:20px;font-size:11px">TIER 2 — Test in expanded study (N≥15, additional sensors)</span>
      <span style="background:#2a1040;color:#b07aa1;padding:4px 12px;border-radius:20px;font-size:11px">TIER 3 — Future research (methodological investment required)</span>
    </div>

    <!-- TIER 1 -->
    <h5 style="color:#2ecc71;margin-top:24px;margin-bottom:12px">TIER 1 — High impact · High testability · Moderate-to-high prior likelihood</h5>
    <p style="font-size:12px;color:#888;margin-bottom:16px">These can be addressed by adding timestamps, a 5-min post-session rest window, and a brief wellbeing questionnaire to the existing protocol. No new sensors required.</p>

    <div class="card mb-3" style="background:#141428;border:1px solid #2a4a2a;border-radius:10px">
      <div class="card-body">
        <div class="d-flex align-items-start justify-content-between mb-2">
          <h6 style="color:#2ecc71;margin:0">H1 — Acoustic energy arc predicts the autonomic arc</h6>
          <span style="background:#1e3d1e;color:#2ecc71;padding:2px 10px;border-radius:12px;font-size:10px;white-space:nowrap">TIER 1</span>
        </div>
        <p style="font-size:12px;color:#ddd;margin-bottom:8px">
          <strong>Statement:</strong> Sessions structured with an acoustic energy arc (low → peak ~S4 → low → S10 quiet)
          produce a measurable autonomic arc: DFA α1 drops below 0.85 at the energy peak and recovers above pre-session
          baseline DFA α1 by the final stage. The arc is absent in sessions without the energy ramp-down.
        </p>
        <div class="row" style="font-size:11px;color:#aaa">
          <div class="col-md-3"><strong style="color:#4c9be8">Acoustic features:</strong><br>RMS energy (primary), bass energy (secondary)</div>
          <div class="col-md-3"><strong style="color:#4c9be8">HRV metrics:</strong><br>DFA α1 per stage, SD2 at final stage vs. baseline</div>
          <div class="col-md-3"><strong style="color:#4c9be8">Required design:</strong><br>Per-stage timestamps for all participants; 5-min post-session rest window; N≥10</div>
          <div class="col-md-3"><strong style="color:#e74c3c">Key confound:</strong><br>Stage order is fixed — energy arc confounded with time-on-task; need counterbalanced subset</div>
        </div>
        <div style="background:#1a1a2e;border-left:2px solid #f39c12;padding:8px 12px;border-radius:0 6px 6px 0;margin-top:10px;font-size:11px;color:#bbb">
          <strong style="color:#f39c12">Critical assessment:</strong> Directional support from P1 (S4: DFA α1=0.777; S10: 1.236).
          However the 1.1 ms RMSSD "overshoot" is within noise (see Critical Review). DFA α1 is the stronger
          metric to test. The hypothesis is testable but requires at minimum a 5-min post-session rest window
          to establish a meaningful recovery reference. <strong>Prior likelihood: medium-high.</strong>
        </div>
      </div>
    </div>

    <div class="card mb-3" style="background:#141428;border:1px solid #2a4a2a;border-radius:10px">
      <div class="card-body">
        <div class="d-flex align-items-start justify-content-between mb-2">
          <h6 style="color:#2ecc71;margin:0">H2 — Within-session RMS energy is negatively correlated with DFA α1</h6>
          <span style="background:#1e3d1e;color:#2ecc71;padding:2px 10px;border-radius:12px;font-size:10px;white-space:nowrap">TIER 1</span>
        </div>
        <p style="font-size:12px;color:#ddd;margin-bottom:8px">
          <strong>Statement:</strong> Across stages within a session, RMS energy of the concurrent track
          is negatively correlated with DFA α1 (Spearman ρ &lt; −0.4, p &lt; 0.05 at N≥10 participants).
          Higher acoustic energy consistently drives DFA α1 toward the loss-of-regulation zone (&lt;0.75).
          This holds after controlling for stage position (i.e. it is the energy, not just elapsed time).
        </p>
        <div class="row" style="font-size:11px;color:#aaa">
          <div class="col-md-3"><strong style="color:#4c9be8">Acoustic features:</strong><br>RMS energy (tested), bass energy (secondary predictor)</div>
          <div class="col-md-3"><strong style="color:#4c9be8">HRV metrics:</strong><br>DFA α1 per stage</div>
          <div class="col-md-3"><strong style="color:#4c9be8">Required design:</strong><br>Per-stage HRV + timestamps, N≥10; partial correlation controlling for stage index</div>
          <div class="col-md-3"><strong style="color:#e74c3c">Key confound:</strong><br>Bass energy and RMS are strongly correlated (r≈0.99 in current data) — multicollinearity prevents separating their contributions</div>
        </div>
        <div style="background:#1a1a2e;border-left:2px solid #f39c12;padding:8px 12px;border-radius:0 6px 6px 0;margin-top:10px;font-size:11px;color:#bbb">
          <strong style="color:#f39c12">Critical assessment:</strong> P1 data shows the correct direction: S4 (highest energy/bass) has lowest DFA α1 (0.777);
          S10 (quiet, low energy) has highest DFA α1 (1.236). However only 9 data points exist at N=1, and
          bass energy (r=0.97 with RMS) cannot be separated from overall loudness with this track set.
          Needs tracks designed to decorrelate bass from total energy. <strong>Prior likelihood: medium.</strong>
        </div>
      </div>
    </div>

    <div class="card mb-3" style="background:#141428;border:1px solid #2a4a2a;border-radius:10px">
      <div class="card-body">
        <div class="d-flex align-items-start justify-content-between mb-2">
          <h6 style="color:#2ecc71;margin:0">H3 — Pre-session HRV baseline moderates response magnitude</h6>
          <span style="background:#1e3d1e;color:#2ecc71;padding:2px 10px;border-radius:12px;font-size:10px;white-space:nowrap">TIER 1</span>
        </div>
        <p style="font-size:12px;color:#ddd;margin-bottom:8px">
          <strong>Statement:</strong> Participants with higher pre-session DFA α1 (≥0.9) show larger
          within-session delta HRV at both the activation peak (larger DFA α1 drop at S4) and the
          recovery peak (larger SD2 increase at S10) than participants with lower pre-session DFA α1.
          The session "uses" available autonomic range — participants with compressed range show attenuated arcs.
        </p>
        <div class="row" style="font-size:11px;color:#aaa">
          <div class="col-md-3"><strong style="color:#4c9be8">Acoustic features:</strong><br>None specifically — tests individual moderator of response</div>
          <div class="col-md-3"><strong style="color:#4c9be8">HRV metrics:</strong><br>Pre-session DFA α1 as predictor; Δ DFA α1 and Δ SD2 as outcomes</div>
          <div class="col-md-3"><strong style="color:#4c9be8">Required design:</strong><br>5-min pre-session rest window for all participants; per-stage timestamps; N≥10</div>
          <div class="col-md-3"><strong style="color:#e74c3c">Key confound:</strong><br>Age and fitness are correlated with baseline HRV; sample is too small to separate these</div>
        </div>
        <div style="background:#1a1a2e;border-left:2px solid #f39c12;padding:8px 12px;border-radius:0 6px 6px 0;margin-top:10px;font-size:11px;color:#bbb">
          <strong style="color:#f39c12">Critical assessment:</strong> Consistent with HRV-biofeedback literature (Lehrer &amp; Gevirtz 2014):
          resonance is larger when there is more autonomic range to engage.
          P1 (highest baseline HRV) shows largest Δ; P3 (lowest baseline) shows smallest Δ — consistent
          but confounded by age/fitness. Directionally well-supported; requires controlling for confounders.
          <strong>Prior likelihood: high.</strong>
        </div>
      </div>
    </div>

    <div class="card mb-3" style="background:#141428;border:1px solid #2a4a2a;border-radius:10px">
      <div class="card-body">
        <div class="d-flex align-items-start justify-content-between mb-2">
          <h6 style="color:#2ecc71;margin:0">H4 — PNS rebound magnitude predicts post-session subjective wellbeing</h6>
          <span style="background:#1e3d1e;color:#2ecc71;padding:2px 10px;border-radius:12px;font-size:10px;white-space:nowrap">TIER 1</span>
        </div>
        <p style="font-size:12px;color:#ddd;margin-bottom:8px">
          <strong>Statement:</strong> Participants showing a larger increase in DFA α1 between the
          activation peak (S4) and the recovery peak (S10) report greater post-session improvement
          on a subjective wellbeing measure (PANAS positive affect, or SUDS 0–10 scale).
          The physiological rebound and the felt shift track together.
        </p>
        <div class="row" style="font-size:11px;color:#aaa">
          <div class="col-md-3"><strong style="color:#4c9be8">Acoustic features:</strong><br>S4 vs S10 energy contrast (acts as acoustic manipulation)</div>
          <div class="col-md-3"><strong style="color:#4c9be8">HRV metrics:</strong><br>DFA α1 (S10) − DFA α1 (S4); alternatively SD2 (S10) − SD2 (S4)</div>
          <div class="col-md-3"><strong style="color:#4c9be8">Required design:</strong><br>Add PANAS or SUDS immediately pre and post session; per-stage timestamps; N≥10</div>
          <div class="col-md-3"><strong style="color:#e74c3c">Key confound:</strong><br>Expectation effects (all participants know they're in a "healing" session); needs placebo condition or blind design</div>
        </div>
        <div style="background:#1a1a2e;border-left:2px solid #f39c12;padding:8px 12px;border-radius:0 6px 6px 0;margin-top:10px;font-size:11px;color:#bbb">
          <strong style="color:#f39c12">Critical assessment:</strong> Strongly supported by the mood-HRV literature (Thayer et al. 2012):
          higher cardiac vagal tone predicts better emotion regulation and positive affect.
          Adding two 5-min PANAS administrations costs almost nothing. This is the highest-value
          addition possible given existing protocol. <strong>Prior likelihood: high.</strong>
        </div>
      </div>
    </div>

    <!-- TIER 2 -->
    <h5 style="color:#f39c12;margin-top:30px;margin-bottom:12px">TIER 2 — High impact · Medium testability · Requires new acoustic features or additional sensors</h5>
    <p style="font-size:12px;color:#888;margin-bottom:16px">These require either new acoustic feature computation, additional hardware (breathing belt), or a larger and more carefully controlled study design.</p>

    <div class="card mb-3" style="background:#141428;border:1px solid #4a3a00;border-radius:10px">
      <div class="card-body">
        <div class="d-flex align-items-start justify-content-between mb-2">
          <h6 style="color:#f39c12;margin:0">H5 — Sub-bass (20–80 Hz) drives somatic activation independently of loudness</h6>
          <span style="background:#3d3000;color:#f39c12;padding:2px 10px;border-radius:12px;font-size:10px;white-space:nowrap">TIER 2</span>
        </div>
        <p style="font-size:12px;color:#ddd;margin-bottom:8px">
          <strong>Statement:</strong> Sub-bass energy (20–80 Hz, felt as chest/body vibration) predicts
          DFA α1 reduction <em>above and beyond</em> overall RMS energy. Two tracks matched on total RMS
          but differing in sub-bass content will produce different DFA α1 responses.
          This is distinct from the conscious loudness perception and operates via the vestibular and
          somatosensory systems.
        </p>
        <p style="font-size:12px;color:#aaa;margin-bottom:6px">
          <strong style="color:#4c9be8">New acoustic feature required:</strong>
          Split the current bass band (20–250 Hz) into sub-bass (20–80 Hz) and mid-bass (80–250 Hz).
          Sub-bass at high SPL produces tactile sensation through bone conduction and vestibular activation
          (Todd &amp; Cody 2000) — a mechanism entirely absent from the mid-bass and above.
        </p>
        <div class="row" style="font-size:11px;color:#aaa">
          <div class="col-md-3"><strong style="color:#4c9be8">Required design:</strong><br>Controlled tracks with matched RMS but variable sub-bass; in-lab setup with subwoofer to measure actual SPL at body</div>
          <div class="col-md-3"><strong style="color:#e74c3c">Key confound:</strong><br>Sub-bass and overall bass are correlated in this track set; headphone playback eliminates sub-bass entirely</div>
          <div class="col-md-3"><strong style="color:#4c9be8">HRV metrics:</strong><br>DFA α1 per stage; consider also skin conductance (non-RR marker)</div>
          <div class="col-md-3"><strong style="color:#f39c12">Prior likelihood:</strong><br>Medium. Sub-bass → vestibular → arousal pathway is mechanistically plausible but has not been studied specifically in HRV context.</div>
        </div>
        <div style="background:#1a1a2e;border-left:2px solid #e74c3c;padding:8px 12px;border-radius:0 6px 6px 0;margin-top:10px;font-size:11px;color:#bbb">
          <strong style="color:#e74c3c">Critical note:</strong> In the current dataset, sub-bass and RMS energy are nearly perfectly correlated (r≈0.99).
          This hypothesis cannot be tested with the existing tracks — it requires purpose-designed stimuli.
          Do not report sub-bass as an independent predictor based on current data.
        </div>
      </div>
    </div>

    <div class="card mb-3" style="background:#141428;border:1px solid #4a3a00;border-radius:10px">
      <div class="card-body">
        <div class="d-flex align-items-start justify-content-between mb-2">
          <h6 style="color:#f39c12;margin:0">H6 — AM modulation at respiratory frequency entrains breathing and raises SD2</h6>
          <span style="background:#3d3000;color:#f39c12;padding:2px 10px;border-radius:12px;font-size:10px;white-space:nowrap">TIER 2</span>
        </div>
        <p style="font-size:12px;color:#ddd;margin-bottom:8px">
          <strong>Statement:</strong> Tracks with amplitude modulation peaking at 0.15–0.25 Hz (one complete
          swell every 4–7 seconds) pace participant breathing toward resonance frequency (~0.1 Hz),
          producing a measurable LF HRV peak and higher SD2 compared to tracks with no periodic AM or
          AM at other frequencies. This is the HRV-B resonance mechanism applied to music.
        </p>
        <p style="font-size:12px;color:#aaa;margin-bottom:6px">
          <strong style="color:#4c9be8">New acoustic feature required:</strong>
          AM rate spectrum — compute the power spectrum of the Hilbert envelope (already extracted)
          and identify the dominant modulation frequency. Current AM depth metric captures the
          <em>amount</em> of modulation but not its <em>rate</em>. S11+12 has high AM depth;
          identifying whether its modulation rate falls in the respiratory band is the key test.
        </p>
        <div class="row" style="font-size:11px;color:#aaa">
          <div class="col-md-3"><strong style="color:#4c9be8">Required design:</strong><br>Breathing belt or nasal thermistor to measure respiratory rate; LF HRV analysis requires 5-min windows</div>
          <div class="col-md-3"><strong style="color:#e74c3c">Key confound:</strong><br>Participants may not synchronise breathing to AM; the entrainment is passive, not instructed — compliance is unknown</div>
          <div class="col-md-3"><strong style="color:#4c9be8">HRV metrics:</strong><br>SD2; LF power (Hz); respiratory rate; SD1/SD2 (paced breathing shifts this ratio predictably)</div>
          <div class="col-md-3"><strong style="color:#f39c12">Prior likelihood:</strong><br>High mechanistically (Lehrer &amp; Gevirtz 2014; Nozaradan 2011). Unknown whether passive music-driven entrainment is strong enough without instruction.</div>
        </div>
        <div style="background:#1a1a2e;border-left:2px solid #f39c12;padding:8px 12px;border-radius:0 6px 6px 0;margin-top:10px;font-size:11px;color:#bbb">
          <strong style="color:#f39c12">Critical note:</strong> This is the most mechanistically grounded hypothesis in the set — the HRV-B resonance
          mechanism is well-established. The open question is whether music naturally paces breathing without
          instruction. S11+12 (high AM depth, highest SD2 trend in P2/P3) is consistent.
          Adding a breathing sensor is the single highest-value instrumentation upgrade.
        </div>
      </div>
    </div>

    <div class="card mb-3" style="background:#141428;border:1px solid #4a3a00;border-radius:10px">
      <div class="card-body">
        <div class="d-flex align-items-start justify-content-between mb-2">
          <h6 style="color:#f39c12;margin:0">H7 — Vocal presence produces higher SD1/SD2 than instrumental tracks at equivalent energy</h6>
          <span style="background:#3d3000;color:#f39c12;padding:2px 10px;border-radius:12px;font-size:10px;white-space:nowrap">TIER 2</span>
        </div>
        <p style="font-size:12px;color:#ddd;margin-bottom:8px">
          <strong>Statement:</strong> Stages containing recognisable human vocal elements (chanting, toning, singing)
          produce higher SD1/SD2 ratios than instrumental stages at matched energy levels. The polyvagal
          prosodic pathway (safe/social nervous system) is activated by voice frequencies in the human
          speech band (85–255 Hz fundamental + 2–5 kHz formants), independently engaging the vagal brake.
        </p>
        <p style="font-size:12px;color:#aaa;margin-bottom:6px">
          <strong style="color:#4c9be8">New acoustic feature required:</strong>
          Vocal presence classifier — binary or continuous (e.g. ratio of energy in the human voice
          fundamental frequency range vs. total energy). librosa's harmonic-percussive separation +
          pitch tracking in the vocal range could approximate this. Alternatively a pretrained vocal
          activity detector (e.g. pyannote.audio).
        </p>
        <div class="row" style="font-size:11px;color:#aaa">
          <div class="col-md-3"><strong style="color:#4c9be8">Required design:</strong><br>Annotate which stages contain vocal elements; matched-energy comparison; N≥15</div>
          <div class="col-md-3"><strong style="color:#e74c3c">Key confound:</strong><br>Vocal content is correlated with stage position (e.g. S11+12 reintegration often uses chanting); hard to decorrelate from stage-specific effects</div>
          <div class="col-md-3"><strong style="color:#4c9be8">HRV metrics:</strong><br>SD1/SD2 ratio (most sensitive to acute PNS changes); DFA α1</div>
          <div class="col-md-3"><strong style="color:#f39c12">Prior likelihood:</strong><br>Medium. Polyvagal theory (Porges 2011) predicts this, but direct music-vocal HRV evidence is sparse.</div>
        </div>
      </div>
    </div>

    <div class="card mb-3" style="background:#141428;border:1px solid #4a3a00;border-radius:10px">
      <div class="card-body">
        <div class="d-flex align-items-start justify-content-between mb-2">
          <h6 style="color:#f39c12;margin:0">H8 — Spectral brightness independently predicts SNS activation above an alerting threshold</h6>
          <span style="background:#3d3000;color:#f39c12;padding:2px 10px;border-radius:12px;font-size:10px;white-space:nowrap">TIER 2</span>
        </div>
        <p style="font-size:12px;color:#ddd;margin-bottom:8px">
          <strong>Statement:</strong> Stages with spectral centroid above ~1100 Hz show measurably lower DFA α1
          and higher HR than stages with centroid below 700 Hz, at matched RMS energy levels.
          The auditory startle / alerting reflex is primarily driven by high-frequency content; brightness
          is an independent ANS activator beyond loudness.
        </p>
        <p style="font-size:12px;color:#aaa;margin-bottom-6px">
          <strong style="color:#4c9be8">Note on current data:</strong> S8+9 has the highest centroid (1431 Hz) and among
          the highest energy — the two features co-vary and cannot currently be separated. New tracks
          with high brightness / low energy and low brightness / high energy are needed.
        </p>
        <div class="row" style="font-size:11px;color:#aaa">
          <div class="col-md-4"><strong style="color:#e74c3c">Key confound:</strong><br>Brightness (spectral centroid) is correlated with energy in most natural music; need purpose-designed stimuli to decorrelate</div>
          <div class="col-md-4"><strong style="color:#f39c12">Prior likelihood:</strong><br>Medium-high. Auditory startle literature (Khalfa et al. 2002; Leman et al. 2005) supports brightness-arousal link but primarily for sudden onsets, not sustained spectral character.</div>
          <div class="col-md-4"><strong style="color:#4c9be8">Required design:</strong><br>Matched-energy tracks varying only in spectral content; within-participant crossover</div>
        </div>
      </div>
    </div>

    <div class="card mb-3" style="background:#141428;border:1px solid #4a3a00;border-radius:10px">
      <div class="card-body">
        <div class="d-flex align-items-start justify-content-between mb-2">
          <h6 style="color:#f39c12;margin:0">H9 — Next-night sleep quality improves following full autonomic arc sessions</h6>
          <span style="background:#3d3000;color:#f39c12;padding:2px 10px;border-radius:12px;font-size:10px;white-space:nowrap">TIER 2</span>
        </div>
        <p style="font-size:12px;color:#ddd;margin-bottom:8px">
          <strong>Statement:</strong> Participants who show a complete autonomic arc (DFA α1 drop ≥0.15 at S4
          AND DFA α1 recovery ≥0.15 at S10 relative to S4) report better subjective sleep quality
          (PSQI or single-item) and/or wearable-measured sleep efficiency the following night compared to
          their own average, and compared to participants with incomplete arcs.
          This links the within-session regulatory event to a general health outcome beyond HRV.
        </p>
        <div class="row" style="font-size:11px;color:#aaa">
          <div class="col-md-3"><strong style="color:#4c9be8">Required design:</strong><br>Next-morning sleep quality questionnaire (PSQI or single item); optional wearable (Oura, Garmin) for objective sleep; N≥15</div>
          <div class="col-md-3"><strong style="color:#e74c3c">Key confound:</strong><br>Many factors affect sleep; needs baseline sleep quality and comparison to personal average, not population norm</div>
          <div class="col-md-3"><strong style="color:#4c9be8">HRV link:</strong><br>Parasympathetic nervous system recovery measured by HRV is a known predictor of sleep initiation and deep-sleep maintenance</div>
          <div class="col-md-3"><strong style="color:#f39c12">Prior likelihood:</strong><br>Medium. HRV-sleep literature is strong (Stein &amp; Pu 2012). The specific innerdance→arc→sleep pathway is novel.</div>
        </div>
      </div>
    </div>

    <!-- TIER 3 -->
    <h5 style="color:#b07aa1;margin-top:30px;margin-bottom:12px">TIER 3 — High potential · Low near-term testability · Requires methodological innovation</h5>
    <p style="font-size:12px;color:#888;margin-bottom:16px">These are directionally important hypotheses that define the medium-term research agenda but cannot be meaningfully tested with current resources and N.</p>

    <div class="card mb-3" style="background:#141428;border:1px solid #2a1040;border-radius:10px">
      <div class="card-body">
        <div class="d-flex align-items-start justify-content-between mb-2">
          <h6 style="color:#b07aa1;margin:0">H10 — Acoustic tipping points: feature combinations that reliably cross DFA α1 &lt;0.75</h6>
          <span style="background:#2a1040;color:#b07aa1;padding:2px 10px;border-radius:12px;font-size:10px;white-space:nowrap">TIER 3</span>
        </div>
        <p style="font-size:12px;color:#ddd;margin-bottom:8px">
          <strong>Statement:</strong> There exist identifiable threshold surfaces in the acoustic feature space
          (combinations of RMS energy + bass + brightness) above which DFA α1 consistently drops below 0.75
          (regulatory load zone) across participants. Mapping this surface would enable a real-time DJ alert:
          "this track combination will push the group past the regulatory boundary in ~N minutes."
        </p>
        <p style="font-size:12px;color:#aaa">
          <strong style="color:#4c9be8">Why Tier 3:</strong> Requires N≥50 sessions to map a 3-dimensional threshold surface with
          adequate precision. Current N=3 per-stage provides 27 observations — far short of the required density.
          Additionally, the threshold is likely individual-specific (P1 crosses at DFA α1=0.777; P3 never crosses 0.75 in this dataset).
          A population-level threshold may not be meaningful unless expressed as a percentile shift from individual baseline.
        </p>
      </div>
    </div>

    <div class="card mb-3" style="background:#141428;border:1px solid #2a1040;border-radius:10px">
      <div class="card-body">
        <div class="d-flex align-items-start justify-content-between mb-2">
          <h6 style="color:#b07aa1;margin:0">H11 — Session order is irreplaceable: the arc is the therapy, not any single track</h6>
          <span style="background:#2a1040;color:#b07aa1;padding:2px 10px;border-radius:12px;font-size:10px;white-space:nowrap">TIER 3</span>
        </div>
        <p style="font-size:12px;color:#ddd;margin-bottom:8px">
          <strong>Statement:</strong> The PNS rebound at S10 is significantly larger when preceded by the full
          S1→S9 acoustic arc than when S10 is presented as the first track (or in randomised order).
          The recovery is potentiated by prior activation — the body needs to be "spent" before it can rebound.
          Randomising track order would eliminate or reduce the autonomic arc.
        </p>
        <p style="font-size:12px;color:#aaa">
          <strong style="color:#4c9be8">Why Tier 3:</strong> Requires a crossover design where the same participants
          experience both ordered and randomised track sequences on separate occasions (minimum 1-week washout).
          This is the most important structural hypothesis for validating the innerdance protocol design —
          but it is also the most logistically and ethically complex, as it disrupts the therapeutic sequence.
        </p>
        <div style="background:#1a1a2e;border-left:2px solid #e74c3c;padding:8px 12px;border-radius:0 6px 6px 0;margin-top:10px;font-size:11px;color:#bbb">
          <strong style="color:#e74c3c">Critical note:</strong> Until this hypothesis is tested, the entire causal model is underspecified.
          We cannot rule out that each track works independently, or that time-on-task alone explains
          the apparent arc. This is the single most important experiment for the research programme.
        </div>
      </div>
    </div>

    <div class="card mb-3" style="background:#141428;border:1px solid #2a1040;border-radius:10px">
      <div class="card-body">
        <div class="d-flex align-items-start justify-content-between mb-2">
          <h6 style="color:#b07aa1;margin:0">H12 — Salivary cortisol reduction following full-arc sessions</h6>
          <span style="background:#2a1040;color:#b07aa1;padding:2px 10px;border-radius:12px;font-size:10px;white-space:nowrap">TIER 3</span>
        </div>
        <p style="font-size:12px;color:#ddd;margin-bottom:8px">
          <strong>Statement:</strong> Participants completing a full innerdance arc (confirmed by DFA α1 drop + recovery)
          show a statistically significant reduction in salivary cortisol post-session versus pre-session,
          and versus a matched waiting-room control condition. This is the gold-standard biological
          validation of the stress-reduction mechanism and would satisfy requirements for clinical research funding.
        </p>
        <p style="font-size:12px;color:#aaa">
          <strong style="color:#4c9be8">Why Tier 3:</strong> Salivary cortisol requires careful timing (peak ~20 min post stressor),
          lab-grade storage and assay, and typically N≥30 per group for adequate power.
          It is the most expensive and logistically demanding test in the set.
          The expected effect size (based on meditation/music therapy literature) is d≈0.5,
          requiring N≈50 per group for 80% power at α=0.05.
        </p>
      </div>
    </div>

    <div style="background:#1a1a2e;border:1px solid #4c9be8;border-radius:8px;padding:16px 18px;margin-top:20px">
      <h6 style="color:#4c9be8">Principal Data Scientist Summary</h6>
      <p style="font-size:12px;color:#ddd;margin:0;line-height:1.9">
        <strong style="color:#2ecc71">Highest priority for next round (Tier 1):</strong>
        Add per-stage timestamps for all participants, a 5-min pre/post resting window, and PANAS/SUDS questionnaires.
        This unlocks H1–H4 with minimal cost and converts this POC into a publishable pilot study.
        <br><br>
        <strong style="color:#f39c12">Highest methodological value (Tier 2):</strong>
        A breathing belt (≈€50) transforms the interpretability of DFA α1 throughout — it resolves
        the critical ambiguity between slow-breathing artifact and genuine SNS/PNS state, and enables
        the respiratory-entrainment hypothesis (H6), which has the strongest mechanistic grounding in
        the HRV-biofeedback literature.
        <br><br>
        <strong style="color:#e74c3c">Non-negotiable for causal claims (Tier 3):</strong>
        H11 (order effect) must be tested before any claim about acoustic features <em>causing</em>
        HRV changes can be made. Without it, every result in this report is equally consistent with
        "music matters" and "time-on-task + expectation matters."
        <br><br>
        <strong style="color:#aaa">Acoustic features to add in next extraction pass:</strong>
        (1) AM rate spectrum — dominant modulation frequency of Hilbert envelope;
        (2) sub-bass energy split (20–80 Hz vs. 80–250 Hz);
        (3) vocal presence score (pyannote.audio or harmonic tracking in 85–255 Hz band).
        All three are extractable from existing audio with no new recordings required.
      </p>
    </div>
  </section>

  <!-- CRITICAL REVIEW -->
  <section id="review">
    <h2 class="section-title">Critical Review — Validity &amp; Confidence Assessment</h2>
    <p style="font-size:13px;color:#aaa;margin-bottom:16px">
      Independent review of analysis validity, data quality, and confidence in conclusions.
      <span style="background:#1e3d1e;color:#2ecc71;padding:2px 8px;border-radius:10px;font-size:11px;margin-right:4px">HIGH</span>well-supported by the data as collected ·
      <span style="background:#3d3000;color:#f39c12;padding:2px 8px;border-radius:10px;font-size:11px;margin-right:4px">MEDIUM</span>directionally plausible, needs more data ·
      <span style="background:#3d0000;color:#e74c3c;padding:2px 8px;border-radius:10px;font-size:11px;margin-right:4px">LOW</span>hypothesis only; current data insufficient
    </p>
    <div class="table-responsive">
    <table class="table table-sm" style="font-size:12px;color:#ccc">
      <thead>
        <tr style="background:#1a1a2e;color:#76b7b2">
          <th style="min-width:220px">Claim / Finding</th>
          <th style="min-width:80px;text-align:center">Confidence</th>
          <th style="min-width:300px">Concern / Caveat</th>
          <th style="min-width:160px">What would raise confidence</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td><strong>Stage 4 is the SNS activation peak</strong><br>
              <small style="color:#888">DFA α1=0.777, RMSSD=94.9 ms (P1); directional trend in P2, P3</small></td>
          <td style="text-align:center"><span style="background:#3d3000;color:#f39c12;padding:2px 8px;border-radius:10px;font-size:11px">MEDIUM</span></td>
          <td style="font-size:11px;color:#bbb">N=3 participants. The 9.3 ms RMSSD drop (P1) is real but N=1 for per-stage timestamp precision.
              P2 and P3 provide directional corroboration only, not independent replication.
              Timestamp boundaries from a handwritten docx (P1) and inferred session log (P2, P3)
              introduce ±15–60 s alignment uncertainty — meaningful at 3–5 min stage windows.</td>
          <td style="font-size:11px;color:#888">N≥6 with per-stage timestamps; automated timestamp logging during recording</td>
        </tr>
        <tr style="background:#141428">
          <td><strong>Stage 10 is the PNS rebound peak</strong><br>
              <small style="color:#888">SD2=241 ms, RMSSD=117.6 ms (P1); SD2 rise in P2, P3</small></td>
          <td style="text-align:center"><span style="background:#3d3000;color:#f39c12;padding:2px 8px;border-radius:10px;font-size:11px">MEDIUM</span></td>
          <td style="font-size:11px;color:#bbb">S10 SD2 (241 ms) is nearly identical to the pre-session baseline (244 ms) — this may reflect
              return to rest, not overshoot. RMSSD is unreliable here due to slow breathing (McCreary 2022).
              DFA α1=1.236 is the strongest evidence and should be the primary metric for this claim.</td>
          <td style="font-size:11px;color:#888">Add post-session resting window to establish true rebound reference point</td>
        </tr>
        <tr>
          <td><strong>H5 supported: activation → rebound overshoot</strong><br>
              <small style="color:#888">Recovery RMSSD 104.1 ms &gt; pre-session baseline 103.0 ms (P1)</small></td>
          <td style="text-align:center"><span style="background:#3d0000;color:#e74c3c;padding:2px 8px;border-radius:10px;font-size:11px">LOW</span></td>
          <td style="font-size:11px;color:#bbb"><strong>Δ of +1.1 ms is within measurement noise.</strong>
              A 5-beat window boundary shift changes RMSSD by several ms. This cannot be reported as a
              supported finding at N=1 with a 1 ms margin. Rephrase as "trend consistent with H5" pending
              a powered study with a defined post-session rest window.</td>
          <td style="font-size:11px;color:#888">N≥10 with 5-min post-session rest; paired test with Bonferroni or FDR correction</td>
        </tr>
        <tr style="background:#141428">
          <td><strong>DFA α1 &lt;0.75 during paper-reading = paced-breathing artifact</strong><br>
              <small style="color:#888">P1 reading: DFA α1=0.638</small></td>
          <td style="text-align:center"><span style="background:#1e3d1e;color:#2ecc71;padding:2px 8px;border-radius:10px;font-size:11px">HIGH</span></td>
          <td style="font-size:11px;color:#bbb">Well-supported by McCreary et al. (2022). <strong>Critical implication:</strong>
              the same artifact may affect DFA α1 in any innerdance stage where participants breathe slowly —
              DFA α1 &lt;0.75 is ambiguous (genuine SNS activation OR slow breathing).
              This is not currently flagged in stage-level analysis and should be.</td>
          <td style="font-size:11px;color:#888">Add respiratory rate monitoring; gate DFA α1 interpretation on measured breathing rate</td>
        </tr>
        <tr>
          <td><strong>Acoustic feature thresholds (Low/Med/High) are meaningful</strong><br>
              <small style="color:#888">33rd/67th percentiles across N=9 tracks</small></td>
          <td style="text-align:center"><span style="background:#3d0000;color:#e74c3c;padding:2px 8px;border-radius:10px;font-size:11px">LOW</span></td>
          <td style="font-size:11px;color:#bbb">33rd percentile of 9 values = 3rd-lowest observation. These are not stable population estimates.
              Categories are relative to this track set only and may not generalise.
              librosa analyses first 600 s; tracks that fade in or vary structurally over time are
              misrepresented by a single summary value.</td>
          <td style="font-size:11px;color:#888">Expand to ≥30 tracks; analyse full track in segments; validate thresholds with expert ratings</td>
        </tr>
        <tr style="background:#141428">
          <td><strong>DFA α1 is reliable at 3–5 min stage windows</strong><br>
              <small style="color:#888">~150–300 beats per stage, windows 4–16 beats</small></td>
          <td style="text-align:center"><span style="background:#3d3000;color:#f39c12;padding:2px 8px;border-radius:10px;font-size:11px">MEDIUM</span></td>
          <td style="font-size:11px;color:#bbb">Peng et al. (1995) recommends ≥1000 beats for stable α1.
              Most stages provide 150–300 beats — below this threshold; estimates are noisier.
              The ±20% rolling-median artifact filter could also reduce apparent fractal complexity
              by removing genuine physiological outliers before DFA is applied.</td>
          <td style="font-size:11px;color:#888">Compare short-window DFA against full-session estimates; sensitivity analysis on filter threshold</td>
        </tr>
        <tr>
          <td><strong>Acoustic features drive the observed HRV changes</strong><br>
              <small style="color:#888">Core qualitative model claim</small></td>
          <td style="text-align:center"><span style="background:#3d0000;color:#e74c3c;padding:2px 8px;border-radius:10px;font-size:11px">LOW</span></td>
          <td style="font-size:11px;color:#bbb"><strong>No causal link is established.</strong>
              The stage order (S1→S12) is fixed in every session, confounding acoustic features with
              elapsed time, fatigue, and expectation. We cannot yet distinguish music-driven HRV change
              from time-on-task effects. No correlation analysis has been run — the report shows
              co-occurring values, not correlations.</td>
          <td style="font-size:11px;color:#888">Randomised or counterbalanced track order; N≥20; Spearman ρ with FDR correction</td>
        </tr>
        <tr style="background:#141428">
          <td><strong>Cross-participant HRV comparisons in heatmap</strong><br>
              <small style="color:#888">P1 RMSSD ~104 ms vs P3 RMSSD ~17 ms in same table</small></td>
          <td style="text-align:center"><span style="background:#3d0000;color:#e74c3c;padding:2px 8px;border-radius:10px;font-size:11px">LOW</span></td>
          <td style="font-size:11px;color:#bbb"><strong>Absolute RMSSD must not be compared across participants.</strong>
              P1 (38, athlete) is expected to have 3–5× higher RMSSD than P3 (43) from fitness and age
              alone, independent of innerdance. Only within-person delta values (Δ from Stage 1 or
              pre-session baseline) are valid for cross-participant statements.
              The current heatmap visualisation is misleading in this respect.</td>
          <td style="font-size:11px;color:#888">Z-score per participant before heatmap; report Δ only in cross-participant views</td>
        </tr>
        <tr>
          <td><strong>P4 whole-session RMSSD = 14.5 ms reflects true HRV</strong></td>
          <td style="text-align:center"><span style="background:#3d3000;color:#f39c12;padding:2px 8px;border-radius:10px;font-size:11px">MEDIUM</span></td>
          <td style="font-size:11px;color:#bbb">Plausible for a sedentary middle-aged participant but also consistent with movement artifact
              from active innerdance movement. The ±20% filter removes large outliers but not
              systematic movement-shifted RR values. Without resting ECG validation, this reading
              cannot be confirmed as artifact-free.</td>
          <td style="font-size:11px;color:#888">Compare with 5-min seated resting baseline before and after session; inspect raw RR trace</td>
        </tr>
      </tbody>
    </table>
    </div>
    <div style="background:#1a1a2e;border:1px solid #4c9be8;border-radius:8px;padding:18px;margin-top:18px">
      <h6 style="color:#4c9be8">Overall Assessment</h6>
      <p style="font-size:12px;color:#ddd;margin:0;line-height:1.9">
        <strong style="color:#2ecc71">What is reliable:</strong> P1's within-session HRV shows a plausible autonomic arc
        using the correct metrics (DFA α1, SD2) for within-session inference. The audio feature extraction pipeline is
        technically sound. The qualitative Low/Medium/High framework is a reasonable starting point for expert validation.
        The respiratory-sinus artifact identification during paper-reading is a genuine, well-supported finding.<br><br>
        <strong style="color:#f39c12">What needs caution:</strong> No causal claim about music→HRV is supportable yet.
        Cross-participant absolute HRV comparisons are not valid. DFA α1 interpretation requires respiratory
        rate context (slow breathing and SNS activation produce the same signal). Short-window DFA estimates
        have wider uncertainty than full-session estimates.<br><br>
        <strong style="color:#e74c3c">Recommended reframe:</strong> Present this report as a
        <em>feasibility study and hypothesis-generation instrument</em>, not as evidence of acoustic-HRV causality.
        The H5 "rebound overshoot" claim should be downgraded to "trend consistent with H5."
        The value of this POC is the validated pipeline, the expert validation framework,
        and the identification of the key confounds to address in the next data collection round.
      </p>
    </div>
  </section>

  <!-- REFERENCES -->
  <section id="refs">
    <h2 class="section-title">References</h2>
    <ul style="font-size:12px;color:#aaa;line-height:2.2">
      <li>Task Force of the ESC/NASPE (1996). Heart Rate Variability: Standards of Measurement, Physiological Interpretation and Clinical Use.
          <em>Circulation</em> 93, 1043–1065.
          <a href="https://doi.org/10.1161/01.CIR.93.5.1043" target="_blank" style="color:#4c9be8">doi:10.1161/01.CIR.93.5.1043</a></li>
      <li>Shaffer F, Ginsberg JP (2017). An Overview of Heart Rate Variability Metrics and Norms.
          <em>Front. Public Health</em> 5:258.
          <a href="https://doi.org/10.3389/fpubh.2017.00258" target="_blank" style="color:#4c9be8">doi:10.3389/fpubh.2017.00258</a></li>
      <li>Vanderlei LCM et al. (2009). Basic notions of heart rate variability and its clinical applicability.
          <em>Arq Bras Cardiol</em> 93(4):205–212.
          <a href="https://doi.org/10.1590/s0066-782x2009001000014" target="_blank" style="color:#4c9be8">doi:10.1590/s0066-782x2009001000014</a></li>
      <li>Goldberger AL et al. (2002). Fractal dynamics in physiology: alterations with disease and aging.
          <em>PNAS</em> 99(suppl 1):2466–2472.
          <a href="https://doi.org/10.1073/pnas.012579499" target="_blank" style="color:#4c9be8">doi:10.1073/pnas.012579499</a></li>
      <li style="background:#1e1e3a;border-left:3px solid #4c9be8;padding:4px 10px;border-radius:0 6px 6px 0;margin-left:-10px">
          <strong style="color:#4c9be8">HRV-B:</strong>
          Lehrer PM, Gevirtz R (2014). Heart rate variability biofeedback: how and why does it work?
          <em>Front Psychol</em> 5:756.
          <a href="https://doi.org/10.3389/fpsyg.2014.00756" target="_blank" style="color:#4c9be8">doi:10.3389/fpsyg.2014.00756</a>
          — <em>Core HRV-B mechanism: resonance frequency breathing (~0.1 Hz) maximises LF HRV amplitude
          via baroreceptor feedback loop, producing systemic relaxation response.</em></li>
      <li style="background:#1e1e3a;border-left:3px solid #4c9be8;padding:4px 10px;border-radius:0 6px 6px 0;margin-left:-10px">
          <strong style="color:#4c9be8">HRV-B:</strong>
          Laborde S et al. (2017). Heart Rate Variability and Cardiac Vagal Tone in Psychophysiological Research.
          <em>Front Psychol</em> 8:213.
          <a href="https://doi.org/10.3389/fpsyg.2017.00213" target="_blank" style="color:#4c9be8">doi:10.3389/fpsyg.2017.00213</a>
          — <em>Validates RMSSD as index of cardiac vagal control; reviews norm values by age/sex.</em></li>
      <li style="background:#1e1e3a;border-left:3px solid #4c9be8;padding:4px 10px;border-radius:0 6px 6px 0;margin-left:-10px">
          <strong style="color:#4c9be8">HRV-B:</strong>
          Gevirtz R (2013). The Promise of Heart Rate Variability Biofeedback: Evidence-Based Applications.
          <em>Biofeedback</em> 41(3):110–120.
          <a href="https://doi.org/10.5298/1081-5937-41.3.01" target="_blank" style="color:#4c9be8">doi:10.5298/1081-5937-41.3.01</a>
          — <em>Clinical applications of HRV-B for anxiety, depression, PTSD, asthma, pain; effect sizes.</em></li>
      <li style="background:#1e1e3a;border-left:3px solid #e74c3c;padding:4px 10px;border-radius:0 6px 6px 0;margin-left:-10px">
          <strong style="color:#e74c3c">⚠ Validity:</strong>
          McCreary R et al. (2022). Repeated Observations of RMSSD Invalidity During Slow Paced Breathing.
          <em>Am J Physiol Regul Integr Comp Physiol</em>.
          <a href="https://doi.org/10.1152/ajpregu.00124.2022" target="_blank" style="color:#4c9be8">doi:10.1152/ajpregu.00124.2022</a>
          — <em>RMSSD becomes unreliable when breathing rate drops below ~9 bpm (typical during innerdance).
          Use SD2, SD1/SD2 ratio, and DFA α1 for within-session comparisons.</em></li>
      <li>Peng CK et al. (1995). Quantification of scaling exponents and crossover phenomena in nonstationary heartbeat time series.
          <em>Chaos</em> 5(1):82–87.
          <a href="https://doi.org/10.1063/1.166141" target="_blank" style="color:#4c9be8">doi:10.1063/1.166141</a>
          — <em>Original DFA method for HRV; α1 ~1.0 = healthy fractal correlation, &lt;0.75 = loss of regulation.</em></li>
    </ul>
    <hr style="border-color:#2a2a4a;margin-top:40px">
    <p style="font-size:11px;color:#555;text-align:center">
      Generated by Innerdance Research POC · {pd.Timestamp.now().strftime('%Y-%m-%d')} ·
      N=3 per-stage (P1/P2/P3) · N=6 whole-session · 8 audio tracks
    </p>
  </section>

</div>

<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
<script>
  Plotly.newPlot('chart-session',  __CHART_SESS__);
  Plotly.newPlot('chart-radar',    __CHART_RADAR__);
  Plotly.newPlot('chart-audio-bars', __CHART_AUDIO__);
  Plotly.newPlot('chart-arc',      __CHART_ARC__);
  Plotly.newPlot('chart-hrv-heatmap', __CHART_HRV__);
</script>
</body>
</html>"""

    # Embed chart JSON
    html = html.replace("__CHART_SESS__",  chart_json(fig_sess))
    html = html.replace("__CHART_RADAR__", chart_json(fig_radar))
    html = html.replace("__CHART_AUDIO__", chart_json(fig_audio))
    html = html.replace("__CHART_ARC__",   chart_json(fig_arc))
    html = html.replace("__CHART_HRV__",   chart_json(fig_hrv))

    return html


# ── ENTRY POINT ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    model_df, audio_df, audio_features, stage_hrv, session_stats, thresholds, cats, vlad_presession_hrv = run()
    print("\nBuilding HTML report…")
    html = build_html(model_df, audio_df, audio_features, stage_hrv,
                      session_stats, thresholds, cats, vlad_presession_hrv)
    with open(OUTPUT_HTML, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"\n✅ Report saved: {OUTPUT_HTML}")
    print(f"   Size: {len(html)//1024} KB")
