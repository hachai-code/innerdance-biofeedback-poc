# data/sample/

Pipeline sample files — committed to git for end-to-end testing.

These are pseudonymised versions of real participant data used to verify the full pipeline (upload → processing → report generation) without requiring the full participant dataset.

---

## Files

| File | Participant | Date | Format | Notes |
|---|---|---|---|---|
| `P1_2025-12-14_session01.csv` | P1 (pseudonymised) | 14 Dec 2025 | `polar_ecg` | Full 12-stage session with pre-session baseline |

---

## Format

`polar_ecg` — raw Polar H10 ECG export:
```
time [ns], ecg, hr, rr [ms], marker
```
- `time [ns]`: nanoseconds from session start
- `rr [ms]`: R-R interval in ms (NaN on rows without an R-peak)

---

## Pipeline test coverage

Running `analysis/03_qualitative_model_report.py` with only this file should produce:
- Acoustic feature extraction for all available stages
- P1 HRV curves (RMSSD rolling window, SD2, DFA α1)
- A valid HTML report at `outputs/innerdance_model_report_v2.html`

Other participants will show as `(data not available in this environment)` — this is expected.
