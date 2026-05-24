# data/

Participant health data — **not committed to git**. This README is the only file tracked.

---

## Why data is not in the repo

The CSV files contain individual health data (heart rate variability recordings). They are excluded by `.gitignore`. Request access from the research lead.

---

## Folder layout

```
data/
├── README.md                                  ← this file (committed)
├── sample/                                    ← pipeline test files (committed)
│   ├── README.md
│   ├── P1_2025-12-14_session01.csv            ← P1 full session (Polar H10 ECG)
│   └── P1_2025-12-14_timestamps.json          ← P1 stage timestamps + HRV results
└── baseline + stress test + 5 stages RR recordnings/   ← local only, gitignored
    ├── P2_2025-12-26_session01.csv            (renamed from Claudia original)
    ├── P3_2025-12-26_session01.csv            (renamed from Giacomo original)
    ├── P4_2025-12-13_session01.csv            (renamed from Cezar original)
    ├── P5_2025-12-10_session01.csv            (renamed from Lorenzo original)
    ├── P6_2025-12-19_session01.csv            (renamed from Andrei original)
    ├── Timestamps P2 and P3 session.docx
    └── Timestamps P1.docx
```

Note: the original filenames in the local data folder have not been renamed on disk — the table above shows the target pseudonymised naming convention to use when re-organising.

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
| P1 | 14.12.2025 | polar_ecg | Full 12-stage session. Timestamps in `sample/P1_2025-12-14_timestamps.json`. |
| P2 | 26.12.2025 | polar_ecg | 12 stages. Timestamps available (converted from `.docx`). |
| P3 | 26.12.2025 | polar_ecg | 12 stages. Timestamps available (converted from `.docx`). |
| P4 | 13.12.2025 | polar_ecg | 12 stages — no stage timestamps. |
| P5 | 10.12.2025 | polar_ecg | First 5 stages only. |
| P6 | 19.12.2025 | polar_ecg | Last stages only (recording started late). |
