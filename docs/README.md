# docs/

All research documentation, design artefacts, and iteration records.

## Start here

- [RESEARCH_JOURNAL.md](../RESEARCH_JOURNAL.md) — consolidated research journal covering all iterations and current results. Read this first for context.
- [architecture.md](architecture.md) — V1 implementation architecture (Supabase + React + Metabase) and conceptual architecture. Contains Mermaid diagrams and database schema.
- [architecture_decision_records.md](architecture_decision_records.md) — ADRs for platform selection (Supabase) and acoustic feature extraction package stack.
- [data_collection_protocol.md](data_collection_protocol.md) — Single reference for what to record, when, in what format, and why. Use this for all future data collection rounds.
- [analysis_skills.md](analysis_skills.md) — Compressed technical reference: HRV pipeline code, acoustic feature extraction code, key findings, and critical constraints. Start here when extending the analysis.

## Research iterations

The `research/` subdirectory contains the full output of each design iteration. They are preserved in order and should not be edited retroactively.

| File | Summary | Status |
|---|---|---|
| [step1_metrics_hypothesis.md](research/step1_metrics_hypothesis.md) | First draft: RMSSD + PSS-3 + rule-based ML | Superseded by v2 |
| [step2_metrics_hypothesis_v2.md](research/step2_metrics_hypothesis_v2.md) | Literature review, metric tiers, ML approaches A–E | **Current reference** |
| [step3_sequence_models.md](research/step3_sequence_models.md) | Sequence model approaches: TRF → ARMAX → ESN → TCN → LSTM | Technical reference |
| [step4_pragmatic_approach.md](research/step4_pragmatic_approach.md) | Two-stream pivot (observe + validate). H1–H5. | Design pivot |
| [step5_refined_approach.md](research/step5_refined_approach.md) | Resilience reframe, self-administered protocol, comparison conditions | **Final protocol design** |
