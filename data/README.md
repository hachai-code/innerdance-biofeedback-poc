# data/

Participant health data — **not committed to git**. This README is the only file tracked.

---

## Why data is not in the repo

The CSV files contain individual health data (heart rate variability recordings). They are excluded by `.gitignore`. Request access from the research lead.

---

## Folder layout (local only)

```
data/
├── README.md                                  ← this file (committed)
├── 14.12.25, 12_50 Vlad-1.csv                ← Polar H10 ECG export, Vlad, partial session
└── baseline + stress test + 5 stages RR recordnings/
    ├── 10.12.25, 15_47-1 Lorenzo first 5 stages.csv
    ├── 13.12.25, 19_30 cezar 12 stages.csv
    ├── 14.12.25, 12_50 Vlad 12 stages.csv
    ├── 19.12.25, 19_17 Andrei last stages.csv
    ├── 26.12.2025, 18_29 Claudia 12 stages.csv
    ├── 26.12.25, 18_29 Giacomo 12 stages.csv
    ├── Timestamps Giacomo and Claudia session.docx
    └── Timestamps Vlad.docx
```

---

## Polar H10 file formats

### `polar_ecg` — Raw H10 ECG export
Columns: `time [ns], ecg, hr, rr [ms], marker`
- `time [ns]`: nanoseconds from session start
- `rr [ms]`: R-R interval in milliseconds. NaN on rows without an R-peak.
- `ecg`: raw ECG signal (not used in HRV analysis)

### `polar_beat` — Polar Beat app CSV export
Columns: `Phone timestamp, RR-interval [ms]`

---

## Stage timestamps format

Each session needs a stages CSV file:
```csv
stage,start_sec,label
baseline,0,Baseline (relaxed smalltalk)
stress,300,Stress induction (video + questions)
1,720,Stage 1 - Befriedigung
2,960,Stage 2 - Unzufriedenheit
3,1200,Stage 3 - Die Schwelle
4,1440,Stage 4 - Freisetzung
...
```
`start_sec` = seconds from session start.

Existing timestamp documents: see `.docx` files in `baseline + stress test.../` folder. Convert to CSV before running analysis.

---

## Self-report JSON schema (fixed — do not change mid-study)

```json
{
  "pre_stress": 0,
  "post_stress": 0,
  "pre_energy": 0,
  "post_energy": 0,
  "sleep_quality_last_night": 3,
  "notable_events": ""
}
```

---

## Session metadata JSON schema

```json
{
  "start_time_utc": "2025-12-14T12:50:00Z",
  "duration_min": 60,
  "sync_offset_sec": 0.0,
  "session_type": "innerdance",
  "audio_source": "spotify:playlist:xxx or filename.mp3",
  "polar_format": "polar_ecg"
}
```

---

## 3-clap sync protocol

When session audio and R-R data are both recorded:
1. Start Polar recording first.
2. Clap loudly 3 times before starting audio.
3. The clap appears as an R-R artefact spike AND as a transient in the audio waveform.
4. Compute `sync_offset_sec` from this shared event and store in `metadata.json`.

---

## Participants (Dec 2025 cohort)

| Participant ID | Date | Format | Notes |
|---|---|---|---|
| Vlad | 14.12.2025 | polar_ecg | Partial + full session. Timestamps in `.docx`. |
| Lorenzo | 10.12.2025 | polar_ecg | First 5 stages only |
| Cezar | 13.12.2025 | polar_ecg | 12 stages |
| Andrei | 19.12.2025 | polar_ecg | Last stages only |
| Claudia | 26.12.2025 | polar_ecg | 12 stages. Timestamps in `.docx`. |
| Giacomo | 26.12.2025 | polar_ecg | 12 stages. Timestamps in `.docx`. |
