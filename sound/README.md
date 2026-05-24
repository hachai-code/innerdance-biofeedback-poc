# sound/

Sample audio tracks for the innerdance pipeline. These files are the acoustic input to the feature extraction scripts.

> **Git LFS note:** These files are tracked directly for the POC (total ~115 MB). For a larger dataset, migrate to Git LFS: `git lfs track "*.mp3"`.

---

## Folder layout

```
sound/
└── 12 stages tracks/
    ├── 03.01.mp3                              ← Stage 3 — The Threshold (P1 only)
    ├── 1.- Safety/                            ← Stage 1 track missing (licensing)
    ├── 2.- Dissatisfaction/
    ├── 3.-4.- Purgation release/              ← Stage 4 — SNS activation peak
    ├── 5.- Disintegration/
    ├── 6.-7.- Awakening/
    ├── 9.- Strength-Failure/
    ├── 10.- Dark night of the soul/           ← Stage 10 — PNS rebound peak
    └── 11.-12.- Reintegration/
```

The `1.- Safety/` folder is present but its track is excluded from the repo. The script handles a missing file by skipping that stage's acoustic analysis.

---

## Stage → track mapping

| Stage | Track file | Brainwave | Innerdance role |
|---|---|---|---|
| 1 — Safety | *(missing)* | Delta | Grounding, surrender |
| 2 — Dissatisfaction | `2.- Dissatisfaction/Dissatisfaction 1.mp3` | Theta | Left-brain loosens |
| 3 — The Threshold | `03.01.mp3` (root) | θ→α/β | Boundary crossing |
| 4 — Purgation-Release | `3.-4.- Purgation release/Purgation-release 1.mp3` | α/β | **SNS activation peak** |
| 5 — Disintegration | `5.- Disintegration/Disintegration 1.mp3` | Delta | Identity dissolves |
| 6+7 — Awakening | `6.-7.- Awakening/Awakening-illumination 1.mp3` | θ/α | PNS recovery begins |
| 8+9 — Strength-Failure | `9.- Strength-Failure/Strength-failure 1.mp3` | α/Mu | Ego-death threshold |
| 10 — Dark Night | `10.- Dark night of the soul/dark night of soul 1.mp3` | Delta | **PNS rebound peak** |
| 11+12 — Unity | `11.-12.- Reintegration/Unity-Oneness-Reintegration 1.mp3` | θ/α | Re-integration |

The Stage 4 → Stage 10 arc (SNS peak → PNS rebound) is the primary pattern the analysis detects.
