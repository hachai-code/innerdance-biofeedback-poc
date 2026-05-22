# notebooks/

Jupyter workspace for AI engineers. Exploratory analysis, model prototyping, and feature engineering.

---

## Connecting to Supabase

```python
from supabase import create_client
import pandas as pd

url  = "https://your-project.supabase.co"
key  = "your-anon-key"
sb   = create_client(url, key)

# Read the feature dataset (all sessions, all participants)
rows = sb.table("feature_dataset").select("*").execute().data
df   = pd.DataFrame(rows)
```

Or directly via SQLAlchemy:
```python
from sqlalchemy import create_engine
engine = create_engine("postgresql://postgres:<password>@db.<project>.supabase.co:5432/postgres")
df = pd.read_sql("SELECT * FROM feature_dataset", engine)
```

---

## Suggested notebook sequence

| Notebook | Purpose | ML Phase |
|---|---|---|
| `01_explore_feature_dataset.ipynb` | EDA: distributions, missingness, per-participant patterns | — |
| `02_phase0_threshold_rule.ipynb` | Implement personal-baseline RMSSD threshold rule | Phase 0 |
| `03_phase1_within_person_ols.ipynb` | OLS: acoustic features → RMSSD per participant | Phase 1 |
| `04_phase2_bayesian_hierarchical.ipynb` | PyMC/bambi: cross-participant Bayesian model | Phase 2 |
| `05_phase3_contextual_bandit.ipynb` | vowpalwabbit contextual bandit prototype | Phase 3 |

Notebooks are not yet created. Add them here as you work through the ML phases.

---

## Key variables in `feature_dataset`

| Column | Type | Notes |
|---|---|---|
| `participant_id` | uuid | Join to `participants` table |
| `session_id` | uuid | Join to `sessions` table |
| `window_ts` | timestamptz | Start of 30-sec window — primary join key |
| `window_type` | text | `'pre'` / `'post'` / `'in_session'` |
| `rmssd` | float | ms — only valid for `'pre'` / `'post'` windows |
| `hf_power` | float | ms² — use for in-session analysis |
| `rsa_amplitude` | float | ms — best in-session vagal index |
| `tempo` | float | BPM |
| `bass_rms` | float | RMS energy 20–250 Hz |
| `am_rate` | float | Amplitude modulation rate (Hz) |
| `spectral_centroid` | float | Hz |
| `pss3` | text | PSS-3 score from session form |
| `energy` | text | Self-reported energy 0–10 |
| `sleep` | text | Sleep quality 1–5 |

---

## MLflow experiment tracking

```bash
mlflow ui  # opens at http://localhost:5000
```

Log runs:
```python
import mlflow
with mlflow.start_run():
    mlflow.log_param("model", "ols_within_person")
    mlflow.log_metric("pearson_r", 0.72)
    mlflow.sklearn.log_model(model, "hrv_state_predictor")
```
