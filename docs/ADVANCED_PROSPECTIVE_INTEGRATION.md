# Advanced model prospective integration — implementation gate

## Objective
Replace the Poisson-only prospective fallback with the best *previously selected* historical factor model, without changing the existing frozen prediction records or claiming that all 84 features improve accuracy.

## Owner's data window decision (31 October 2026)
Production predictions must use the **last two fully completed football seasons** from the existing database, not five years of matches. For October 2026 fixtures this means **2024/25 and 2025/26**. Historical five-year experiments are separate research evidence, not the production prediction input. Preserve the two-day embargo within those seasons and do not silently expand the window when coverage is insufficient. The Poisson prospective scorer has been restricted accordingly; the 84-feature model must obey the same window when integrated.

## Required implementation
1. Read archived factor-search-v1 experiment outputs and identify the locked winning feature group, model configuration and calibration for each supported market. Do not pick a winner using the already-viewed 2024/25–2025/26 audit.
2. Refactor historical feature generation into a shared as-of-date interface used identically by chronological backtests and future fixture inference. Every feature must be derived only from matches known before kickoff with the two-day result embargo. Preserve the same feature order, encodings, team aliases and league IDs.
3. Load/retrain the selected model on eligible historical observations strictly before the inference cutoff; do not refit using the target fixture, later results, or post-match data. If feature parity, coverage, calibration or model identity cannot be established, explicitly skip the fixture or use a clearly labeled Poisson fallback.
4. Maintain the existing snapshot schema and Supabase OIDC sync. Mark model_version with the actual model used; keep probability normalization, immutable snapshots, complete-round Top25 certification, and idempotent inserts.
5. Add tests for feature parity, temporal leakage, missing/unmapped teams, calibrated 1X2 probabilities, fallback identification, duplicate snapshots and complete-round Top25 behavior. Compare advanced model against the Poisson baseline on a *new* untouched temporal evaluation or prospective fixtures; do not advertise previously viewed audit accuracy as live performance.
6. Run CI, inspect real scored fixture coverage, then enable advanced inference in the scheduled workflow only after checks pass. No unverified predictions or odds.

## Current known gap
`scripts/score_future_baseline.py` uses `analytics.backtest.predict` with Poisson parameters, while `analytics/factor_search.py` states it performs historical ablations only. A green historical CI run does not establish future feature parity.

## Acceptance
For each real future prediction: record source, kickoff, prediction timestamp, selected model version, probabilities, cutoff, coverage/fallback reason, and persistence outcome. Compare baseline and advanced outputs without overwriting existing frozen snapshots.
