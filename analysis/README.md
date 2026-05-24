# analysis/

Exploratory and hypothesis-testing scripts. These scripts run on local data files (not Supabase) and produce figures and the primary HTML report.

---

## Scripts

| Script | Purpose | Input | Output |
|---|---|---|---|
| `01_stage_hrv_analysis.py` | Stage-level HRV analysis. Tests H1 (arc) and H5 (activation → rebound). | R-R CSV + stages CSV | 3 figures per session in `outputs/figures/` |
| `02_audio_rr_feature_map.py` | Plots acoustic features alongside HRV on a shared time axis. | Audio file + R-R CSV | Feature map figure |
| `03_qualitative_model_report.py` | **Primary report generator.** Builds the full HTML report with acoustic features, per-stage HRV, participant profiles, hypotheses, and critical review. | R-R CSVs + audio files | `outputs/innerdance_model_report_v2.html` |

---

## How to generate the HTML report

This produces the primary output: `outputs/innerdance_model_report_v2.html`.

### Minimum requirements (sample data only — P1)

With only the sample file committed to the repo:

```bash
pip install -r requirements.txt
python analysis/03_qualitative_model_report.py
```

This will:
- Extract acoustic features from all available tracks in `sound/12 stages tracks/`
- Load `data/sample/P1_2025-12-14_session01.csv` for P1 HRV analysis
- Show `(data not available)` for P2–P6 (their files are not committed — health data, gitignored)
- Produce a valid HTML report at `outputs/innerdance_model_report_v2.html`

### Full dataset (all 6 participants)

Place the participant R-R CSV files in `data/` following the path pattern in the `PARTICIPANTS` dict at the top of `03_qualitative_model_report.py`. Then re-run the script. The script skips any file it cannot find and reports a warning rather than crashing.

### What the report contains

- Participant profiles (age, fitness, smoker/mindfulness flags)
- Acoustic feature extraction for each innerdance stage (6 features)
- Per-stage HRV metrics for timed participants (RMSSD, SD1/SD2, DFA α1, mean HR)
- Whole-session RMSSD curves for all 6 participants
- Qualitative model table: acoustic category × HRV response
- 12 research hypotheses (3 tiers)
- Critical review of data limitations
- **AI-generated disclaimer banner** — the report marks itself as unreviewed

The report is self-contained (all JS/CSS embedded) and can be opened in any browser.

---

## How to add a new session to `01_stage_hrv_analysis.py`

Find the `SESSIONS` list near the top of the script and add an entry:

```python
{
    "id":       "Claudia_20251226",
    "rr_file":  "data/baseline + stress test.../26.12.2025 Claudia 12 stages.csv",
    "format":   "polar_beat",        # or "polar_ecg"
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

Both formats use the same `col_time` / `col_rr` aliasing in the `PARTICIPANTS` dict.

---

## Output figures (gitignored)

Figures from `01_stage_hrv_analysis.py` and `02_audio_rr_feature_map.py` are saved to `outputs/figures/` and gitignored (generated from participant data). Run the scripts locally to reproduce them.

The HTML report (`outputs/innerdance_model_report_v2.html`) **is tracked** in git — it is the primary project output.
