# analysis/

Exploratory and hypothesis-testing scripts. These scripts run on local data files (not Supabase) and produce figures for inspection.

---

## Scripts

| Script | Purpose | Input | Output |
|---|---|---|---|
| `01_stage_hrv_analysis.py` | Stage-level HRV analysis. Tests H1 (arc) and H5 (activation → rebound). | R-R CSV + stages CSV | 3 figures per session in `outputs/figures/` |
| `02_audio_rr_feature_map.py` | Plots acoustic features alongside HRV on a shared time axis. | Audio file + R-R CSV | Feature map figure |

---

## How to add a new session to `01_stage_hrv_analysis.py`

Find the `SESSIONS` list near the top of the script and add an entry:

```python
{
    "id":       "Claudia_20251226",
    "rr_file":  "data/baseline + stress test.../26.12.2025 Claudia 12 stages.csv",
    "format":   "polar_ecg",        # or "polar_beat"
    "segments": {
        "baseline":  (0,   300),    # seconds from session start
        "stage_1":   (500, 800),
        # ... add all stages
    },
}
```

Then run:
```bash
python analysis/01_stage_hrv_analysis.py
```

---

## File formats (see `data/README.md` for full spec)

- `polar_ecg`: Polar H10 raw ECG. Columns: `time [ns], ecg, hr, rr [ms], marker`
- `polar_beat`: Polar Beat app CSV. Columns: `Phone timestamp, RR-interval [ms]`

---

## Demo mode

If a data file is not found, `01_stage_hrv_analysis.py` runs with synthetic data simulating the expected resilience arc. Use this to verify plot format before connecting real data.

---

## Output figures (gitignored)

Figures are saved to `outputs/figures/` and are gitignored (generated from participant data). Run the scripts locally to reproduce them.
