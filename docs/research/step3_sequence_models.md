# Innerdance POC — Time Series & Sequence Model Approaches: Sound Signal → HRV Signal

**Framing:** HRV is not a scalar metric — it is a continuous signal (the R-R interval series) that evolves under the influence of another continuous signal (the sound). The correct modeling frame is therefore **signal-to-signal temporal coupling**, not feature-to-scalar regression.  
**Date:** 2026-05-19  
**Builds on:** step2_metrics_hypothesis_v2.md

---

## 1. The Coupled Signal Problem

```
Sound signal X(t)  ──[auditory-vagal pathway, lag τ]──►  R-R interval series Y(t)
   44.1 kHz raw                                              ~1 beat/sec (~1 Hz)
   → acoustic envelopes at 1–10 Hz                          unevenly sampled, resampled to 4 Hz
```

**Key properties of the coupling:**

| Property | Detail | Implication for modeling |
|----------|--------|--------------------------|
| **Multi-scale** | Breathing-driven RSA at 0.1–0.4 Hz; slower autonomic drift at 0.04–0.15 Hz; session arc over minutes | Model must capture multiple temporal resolutions |
| **Lagged** | ANS responds to acoustic change with ~10–60 sec delay (vagal efferent conduction + SA node) | Requires explicit lag structure or causal convolution |
| **Non-stationary** | Baseline RMSSD drifts across session as arousal state shifts | Time-varying parameters needed |
| **Person-specific** | Vagal tone, respiratory coupling, sensory sensitivity all differ | Personalized (per-participant) components required |
| **Low SNR for small N** | 4 participants × ~56 sessions; individual variability large | Data-efficient methods required; priors critical |

---

## 2. Signal Representation

Before any model is applied, both signals must be brought to a **common time grid**.

### Sound → acoustic feature envelope (1–4 Hz)
Extract per 0.5-second window, 50% overlap, using `librosa` or `essentia`:

| Feature | Physical meaning | Freq. range of variation |
|---------|-----------------|--------------------------|
| RMS energy (20–250 Hz) | Bass / sub-bass power | 0–2 Hz |
| Amplitude modulation depth (Hilbert envelope) | Pulsation rate of sound | 0–4 Hz |
| AM rate (instantaneous freq of envelope) | Rhythm density | 0–4 Hz |
| Spectral centroid | Timbre brightness | 0–1 Hz |
| Onset density | Event rate / percussiveness | 0–2 Hz |
| Tempo (BPM) | Beat period | Very slow — near DC |
| Silence ratio | Presence/absence of sound | Discrete events |

### R-R series → uniform grid
Resample the unevenly sampled R-R series to 4 Hz using cubic spline interpolation (`pyHRV`, `biosppy`, or `scipy.interpolate`). This gives a standard time series compatible with all signal processing and ML methods below.

---

## 3. Approach 1: Cross-Spectral Coherence + Temporal Response Function (TRF)

**What it is:** A pure signal processing approach. Measures the linear coupling between acoustic feature envelope X(t) and R-R series Y(t) as a function of frequency and time lag. No training data required.

**Method:**

```
1. Compute cross-spectrum: Sxy(f) = FFT(X) · conj(FFT(Y))
2. Coherence: C(f) = |Sxy(f)|² / (Sxx(f) · Syy(f))  — ranges 0–1
3. TRF (Temporal Response Function):
   H(τ) = IFFT(Sxy(f) / Sxx(f))  — impulse response of the sound→HRV system
```

The TRF tells you: "given a unit impulse in acoustic feature X, what is the predicted R-R response as a function of lag τ (seconds after the impulse)?"

**Implementation:**
- Python: `mne` library (`mne.decoding.ReceptiveField`) or `scipy.signal.csd`
- R: `spec.pgram` + `spec.coh` for coherence; `expm` for TRF
- The MNE ReceptiveField (ridge regression on lagged acoustic features) is the standard tool from auditory neuroscience for exactly this type of audio → physiological response mapping

**Why this first:**
- Requires zero training samples — computable from a single session
- Directly answers: "at which frequency band and which lag does the sound influence the R-R series?"
- If coherence at 0.1 Hz (resonance frequency band) is high between AM rate and R-R: this is the mechanistic proof your study needs for funding
- Produces the **lag structure τ** that all other models need as a hyperparameter
- Precedent: the auditory neuroscience field uses TRF routinely to model EEG from speech envelopes (Lalor lab, Trinity College Dublin; Crosse et al. 2021, *Frontiers in Human Neuroscience*)

**For/against for our context:**

| For | Against |
|-----|---------|
| Zero data requirement | Linear only — misses nonlinear dynamics |
| Directly interpretable (Hz and seconds) | Assumes stationarity within a window |
| Rigorous test of causal direction | Cannot be used for real-time sound adjustment |
| Standard in auditory neuroscience | Requires clean acoustic feature extraction |

**Source reliability:** ★★★★★ MNE ReceptiveField validated in dozens of EEG-audio studies; cross-spectral methods are classical signal processing (Bendat & Piersol).

---

## 4. Approach 2: ARMAX — Autoregressive Model with Exogenous Acoustic Input

**What it is:** The R-R series is modeled as an autoregression on its own past values plus a filtered version of the lagged acoustic feature series. This is the standard time series regression for "signal Y driven by signal X."

**Model:**

```
Y(t) = Σ aₚ Y(t-p) + Σ bₙ X(t-n-d) + ε(t)
         p=1..P           n=0..N
```

Where:
- `Y(t)` = R-R interval at time t (or RMSSD in a sliding window)
- `X(t)` = acoustic feature at time t (e.g., AM depth, bass RMS)
- `d` = estimated lag from TRF (above)
- `P` = AR order (typically 4–8 for HRV)
- `N` = number of past acoustic lags (typically 10–30, covering 5–15 sec)
- `ε(t)` = white noise residual

**Time-varying version:** Use Kalman filter to track time-varying AR and B coefficients — captures non-stationarity across the session.

From the ScienceDirect 2017 paper: ARMAX with respiratory signal as exogenous input is already validated for time-varying HRV parameter estimation. Replacing "respiration" with "acoustic feature envelope" is the direct extension.

**Implementation:**
- Python: `statsmodels.tsa.arima.model.ARIMA` with exog parameter; or `control` library for state-space form
- R: `arima()` with `xreg`, or `dse` package for ARMAX
- Time-varying: `pykalman` (Python) or `KFAS` (R)

**For/against:**

| For | Against |
|-----|---------|
| Works well with ~50–100 time points per person | Linear model — won't capture complex AM-rate/HRV interactions |
| Explicitly models lag structure d | Requires stationarity or differencing |
| Produces interpretable impulse response function | Individual models per participant (no cross-participant generalization) |
| Time-varying ARMAX via Kalman handles session drift | Hyperparameter sensitivity (P, N, d) |
| Strong precedent in HRV literature (ScienceDirect 2017) | |

**Source reliability:** ★★★★★ ARMAX/Kalman for HRV is a gold standard in biomedical signal processing literature.

---

## 5. Approach 3: Echo State Network (ESN) / Reservoir Computing

**What it is:** A fixed large random recurrent network (the "reservoir") with internal dynamics. Only the linear readout layer is trained. Input = acoustic feature stream; output = next R-R interval. The reservoir's rich dynamics naturally capture temporal dependencies across multiple timescales.

**Architecture:**

```
X(t) [acoustic features] ──► [Fixed random RNN reservoir, N=200–500 units]
                                              │
                                         r(t) [reservoir state]
                                              │
                                    [Trained linear readout W_out]
                                              │
                                         Ŷ(t) [predicted R-R]
```

**Why ESN for small data:**
- Only W_out (output weights) is trained — a linear regression on reservoir states
- With N=200 reservoir units and ~2000 time steps (500 sec session at 4 Hz), the regression is well-posed even with N >> training points if regularized (ridge regression)
- MDPI Applied Sciences 2019: ESN with non-random cyclic topology classifies ventricular heartbeats from RR series with high accuracy
- PMC8502981 (2021): ESN outperforms LSTM for long-term cardiac action potential prediction — specifically because it doesn't require backpropagation through time

**Transfer learning with ESN:** The reservoir is fixed, so "transfer" = collect new data on new participant → retrain only the linear readout layer (~minutes of computation). Directly applicable to personalization across 4 participants.

**Implementation:**
- Python: `reservoirpy` library (dedicated ESN library with documentation)
- Reservoir hyperparameters: spectral radius ~0.9, sparsity ~0.1, input scaling tuned by cross-validation
- ~50 lines of code for a working prototype

**For/against:**

| For | Against |
|-----|---------|
| Trains only linear output — works with 50–200 samples | Black-box reservoir (not interpretable) |
| Naturally captures multi-timescale dynamics | Output linear — can't model nonlinear HRV coupling well at output |
| Fast retraining per participant (seconds) | Spectral radius / reservoir size are sensitive hyperparameters |
| Validated on cardiac prediction tasks | Less studied for sound → HRV specifically |
| Real-time capable (reservoir updates online) | |

**Source reliability:** ★★★★ ESN validated for cardiac signals (PMC8502981, MDPI 2019); not yet published specifically for audio-driven HRV.

---

## 6. Approach 4: Temporal Convolutional Network (TCN) with Pre-training

**What it is:** A 1D fully convolutional network with dilated causal convolutions. Each layer sees a larger temporal context via dilation (layer 1: lag 1, layer 2: lag 2, layer 3: lag 4, ..., layer k: lag 2^k). Input = multivariate acoustic feature time series; output = R-R interval prediction.

**Architecture (suggested):**

```
Input: [T × F] acoustic feature matrix (T timesteps, F features)
  ↓
TCN block 1: 1D dilated causal conv, dilation=1, 64 filters, kernel=3
  ↓
TCN block 2: dilation=2
  ↓
TCN block 3: dilation=4
  ↓
TCN block 4: dilation=8
  ↓
[T × 64] feature map
  ↓
Linear head → R-R interval prediction Ŷ(t)
```

With 4 dilation levels and kernel size 3, receptive field = (3-1) × (1+2+4+8) = 30 timesteps = 7.5 seconds at 4 Hz. This covers the primary autonomic lag.

**Pre-training strategy (critical for small N):**
1. Pre-train on PhysioNet databases (MIT-BIH, BIDMC, or similar) on the task of R-R series forecasting (self-supervised: predict next R-R from past R-R history, no sound input)
2. Fine-tune on our 4-participant data: freeze lower TCN layers, train upper layers + acoustic feature input branch

This is directly analogous to transfer learning in NLP (pre-train on large corpus → fine-tune on domain text) but for physiological time series.

**For/against:**

| For | Against |
|-----|---------|
| Causal convolutions: no information leakage from future | Requires pre-training pipeline (setup cost ~1 week) |
| Parallelizable (unlike LSTM: no sequential dependency) | Receptive field fixed at architecture time |
| Dilated convolutions naturally multi-scale | ~10k-100k parameters — might overfit at small N without aggressive regularization |
| Transfer learning path is clear | More complex than ARMAX or ESN |

**Source reliability:** ★★★★ TCN (Bai et al. 2018, arXiv 1803.01271) established for sequence modeling; PhysioNet pre-training for cardiac signals is standard practice.

---

## 7. Approach 5: LSTM Encoder-Decoder (Seq2Seq) with Acoustic Conditioning

**What it is:** Bidirectional LSTM encoder processes acoustic feature history; LSTM decoder autoregressively predicts future R-R intervals, conditioned on encoder hidden state at each step.

**Architecture:**

```
Acoustic features X(t-L..t) → BiLSTM Encoder → context vector c
                                                          │
R-R history Y(t-M..t) ──────────────────────► LSTM Decoder → Ŷ(t+1..t+H)
```

The decoder's initial hidden state is set to the encoder's final state — the acoustic context is "injected" into the R-R prediction at each step.

**For small N:** Requires aggressive regularization: dropout (0.3–0.5), weight decay, and early stopping. Cross-validated leave-one-session-out per participant. With 14 sessions per participant, this gives ~12 training / 2 test.

**Pre-training on PhysioNet:** Same as TCN: pre-train R-R decoder on large corpus without acoustic conditioning; add and fine-tune acoustic encoder branch on our data.

**For/against:**

| For | Against |
|-----|---------|
| Most expressive sequence model | Highest data requirements of all approaches |
| Can model long-range session dynamics | Gradient vanishing even with LSTM at >100 timestep sessions |
| Seq2seq enables session-level forecasting | Overfitting risk at n=4 without pretraining |
| Conditioning on acoustic context is natural | Requires careful curriculum (start with short sequences) |

**Source reliability:** ★★★ LSTM for HRV forecasting published (ScienceDirect 2024, PMID 39198095); audio conditioning for physiological prediction: arXiv 2020 (indirect).

---

## 8. Approach 6: Bayesian State Space Model with Acoustic Forcing

**What it is:** A probabilistic state space model where the latent autonomic state `s(t)` evolves according to dynamics driven by the acoustic input, and the R-R interval is an observation of this state with noise.

**Model:**

```
State:       s(t) = A·s(t-1) + B·X(t-d) + w(t),   w ~ N(0, Q)
Observation: Y(t) = C·s(t) + v(t),                  v ~ N(0, R)
```

Where `s(t)` could be a 2D latent state: [parasympathetic tone, sympathetic tone]. Priors on A, B, C, Q, R encode domain knowledge (e.g., autonomic time constant ~10–30 sec, parasympathetic response to slow sound is positive).

The Bayesian treatment (via `pymc`, Stan, or Kalman smoother) produces **posterior distributions** over the autonomic state — honest uncertainty quantification. At n=4, the posterior will be wide, but the prior structure prevents implausible estimates.

**Connection to published work:**
- arXiv 2303.04863 "Bayesian at heart": Generative state-space model for HRV, fits latent ANS dynamics directly from R-R series — directly extendable by adding acoustic input `B·X(t-d)`
- ScienceDirect 2017 (time-varying ARMAX + Kalman): Validated acoustic/respiratory exogenous input for state estimation

**For/against:**

| For | Against |
|-----|---------|
| Principled uncertainty quantification — critical at n=4 | Model specification requires domain knowledge (prior elicitation) |
| Online: Kalman filter updates with each new heartbeat | Linear state space (Extended KF for nonlinear, but more complex) |
| Priors encode innerdance mechanism directly | Less flexible than neural approaches |
| Interpretable states: parasympathetic tone trajectory | Requires choosing lag d (use TRF output) |

**Source reliability:** ★★★★ Kalman/state space for HRV: gold standard; Bayesian extension (arXiv 2303.04863) promising but preprint.

---

## 9. Recommended Sequence for Implementation

Given the dataset constraints, here is the correct order — each approach informs and enables the next:

```
SESSION 1-2
├── Approach 1 (TRF / coherence)
│   → Proves coupling exists
│   → Identifies dominant acoustic features and lag τ
│   → No model training needed
│
SESSIONS 3-10
├── Approach 2 (ARMAX with lag τ from above)
│   → First quantitative model: which acoustic features predict R-R?
│   → Produces residuals → check ESN improvement
│
├── Approach 6 (Bayesian SSM in parallel)
│   → Real-time online Kalman state estimation per session
│   → Dashboard: live latent "parasympathetic tone" curve
│
SESSIONS 10-56 (end of 14-day study)
├── Approach 3 (ESN)
│   → Trains on accumulated data, captures nonlinear dynamics
│   → Retrain per participant: 30 min of compute
│
PHASE 2 (with data from multiple cohorts)
├── Approach 4 (TCN) or Approach 5 (LSTM)
│   → Pre-trained on PhysioNet → fine-tuned on innerdance data
│   → Enables session-level forecasting: "given planned sound arc, predict HRV trajectory"
```

---

## 10. Acoustic Feature → R-R Signal Pipeline (Concrete)

```python
import librosa
import numpy as np
from scipy.signal import resample
from scipy.interpolate import interp1d

# 1. SOUND SIDE: extract feature envelopes at 4 Hz
def extract_acoustic_envelopes(audio_path, sr=44100, target_hz=4):
    y, sr = librosa.load(audio_path, sr=sr)
    hop = sr // target_hz  # 11025 samples per window at 4 Hz

    rms_bass    = librosa.feature.rms(y=librosa.effects.trim(y)[0],
                                       frame_length=hop*2, hop_length=hop)[0]
    spec_cent   = librosa.feature.spectral_centroid(y=y, sr=sr, hop_length=hop)[0]
    zcr         = librosa.feature.zero_crossing_rate(y, hop_length=hop)[0]

    # AM envelope via Hilbert transform
    analytic    = librosa.onset.onset_strength(y=y, sr=sr, hop_length=hop)
    am_depth    = np.abs(analytic - np.mean(analytic))

    return np.stack([rms_bass, spec_cent, zcr, am_depth], axis=1)  # [T, 4]

# 2. HRV SIDE: resample R-R series to 4 Hz
def rr_to_uniform(rr_intervals_ms, target_hz=4):
    # rr_intervals_ms: array of R-R intervals in ms, e.g. [820, 810, 795, ...]
    cumtime = np.cumsum(rr_intervals_ms) / 1000.0  # seconds
    uniform_t = np.arange(cumtime[0], cumtime[-1], 1.0/target_hz)
    rr_uniform = interp1d(cumtime, rr_intervals_ms, kind='cubic')(uniform_t)
    return rr_uniform, uniform_t

# 3. ALIGN: both now at 4 Hz — trim to same length, merge into dataset
# 4. FIT: ARMAX, ESN, or TRF on aligned [acoustic_envelopes, rr_uniform]
```

---

## 11. Evaluation Protocol for Small N

Since n=4 participants × ~14 sessions each:

| Strategy | Description |
|----------|-------------|
| **Leave-one-session-out CV** | Train on 13 sessions, test on 1, for each participant separately |
| **Leave-one-participant-out** | Train on 3 participants, test on 1 — tests cross-person generalization |
| **Within-session forecast** | Use first 30 min of session to predict HRV trajectory in final 30 min |
| **Metrics** | MAE on R-R intervals (ms); Pearson r on RMSSD sliding window; coherence preserved post-prediction |
| **Baseline** | Always compare to: (a) naïve persistence (Ŷ(t) = Y(t-1)), (b) session mean, (c) ARMAX without acoustic input |

**Important:** At n=4, the goal is NOT to report a population-level predictive accuracy. The goal is to demonstrate within-person coupling is **plausible and consistent** across participants — sufficient for research funding and the next cohort design.

---

## 12. Summary Table

| Approach | Data requirement | Interpretable | Real-time | Handles small N | Recommended for |
|----------|-----------------|---------------|-----------|-----------------|-----------------|
| TRF / Coherence | Single session | ★★★★★ | No | ★★★★★ | First session, prove coupling |
| ARMAX (time-varying) | 50–100 windows | ★★★★★ | Yes (Kalman) | ★★★★★ | Sessions 3–10, primary model |
| Bayesian SSM | 20+ windows | ★★★★ | Yes (Kalman) | ★★★★★ | Live dashboard, uncertainty |
| Echo State Network | 200+ windows | ★★ | Yes | ★★★★ | Nonlinear refinement |
| TCN (pretrained) | 1000+ (pretrain) + 50 (fine-tune) | ★★★ | Yes | ★★★ | Phase 2 with more data |
| LSTM seq2seq (pretrained) | 1000+ (pretrain) + 56 sessions (fine-tune) | ★★ | Yes | ★★ | Phase 2 / grant deliverable |

---

## Sources

- [MNE ReceptiveField — TRF for audio-physiological coupling](https://mne.tools/stable/generated/mne.decoding.ReceptiveField.html)
- [arXiv 2303.04863 — Bayesian state-space model for HRV](https://arxiv.org/abs/2303.04863)
- [ScienceDirect 2017 — ARMAX + Kalman for time-varying HRV](https://www.sciencedirect.com/article/abs/pii/S0010482517302469)
- [PMC8502981 — ESN for cardiac action potential prediction](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC8502981/)
- [MDPI Applied Sciences 2019 — ESN for ventricular beat classification from RR](https://www.mdpi.com/2076-3417/9/4/702)
- [arXiv 2107.14028 — LSTM estimating respiratory rate from audio](https://arxiv.org/abs/2107.14028)
- [ScienceDirect 2024 — LSTM optimized for RR interval prediction (cardiovascular)](https://www.sciencedirect.com/article/abs/pii/S1746809424009625)
- [arXiv 2003.00007 — Generating EEG features from acoustic features (CNN)](https://arxiv.org/abs/2003.00007)
- [TCN paper — Bai et al. 2018, arXiv 1803.01271](https://arxiv.org/abs/1803.01271)
- [PMC5339732 — Acoustic tempo → HR coupling (Scientific Reports 2017)](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC5339732/)
- [ScienceDirect 2021 — GAN bidirectional HMI ↔ HRV model](https://www.sciencedirect.com/science/article/abs/pii/S1746809421006923)
- [PMC7099475 — Neural entrainment to music spectral envelope](https://pmc.ncbi.nlm.nih.gov/articles/PMC7099475/)
