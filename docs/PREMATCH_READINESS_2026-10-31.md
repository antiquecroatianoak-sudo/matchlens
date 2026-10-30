# MatchLens — pre-match readiness 2026-10-31

## Scope (approved)
Existing ten leagues only; markets 1/X/2 and over/under 2.5 regular-time goals. No new league, no automatic xG promotion. Preserve existing ranking UI and show Top 25% only among eligible, independently validated forecasts.

## Required launch gates (fail closed)
1. **Fixture feed**: fetch genuine upcoming fixtures from an authorized source, record source, competition, canonical home/away IDs, kickoff UTC, retrieval timestamp, unique match ID. Reject ambiguous, postponed, duplicate, already-started, or stale fixtures.
2. **Model artifact**: load a real trained, versioned and calibrated model, with exact training cutoff, validation ID, factor schema and checksums. Never substitute the manual Poisson scenario for verified predictions.
3. **As-of feature join**: each input must have an observed/available timestamp strictly before forecast cutoff; unavailable inputs remain missing, not zero. Never use future match results or xG from target match.
4. **Inference**: generate 1/X/2 and O/U 2.5 probabilities with defined settlement rules, finite values and sum-to-one consistency for each exclusive market; no fabricated odds. Odds are optional and must have their own timestamp and source.
5. **Freeze**: persist immutable prediction record before kickoff with modelVersion, validationId, validatedAt, generatedAt, kickoff, validUntil, market, selection, probability, status and source hashes; reject overwrites and late predictions.
6. **Dry run**: on real upcoming fixtures verify counts loaded/eligible/rejected, reasons for exclusion, probabilities, freeze records and UI appearance. Compare on untouched historical or prospective outcomes before calling the system validated.
7. **Release**: enable automatic live forecasts only after gates 1–6 pass. Otherwise show 'No verified forecast available' and preserve manual scenario labeling.

## Operator checklist
- [ ] Authorized live fixture feed connected and verified
- [ ] Trained calibrated model artifact available and verified
- [ ] Pre-kickoff factor availability verified
- [ ] Prediction/freeze write path verified
- [ ] Real-fixture dry run and audit log verified
- [ ] Production deployment confirmed

This document is an acceptance checklist, not evidence that integration or live prediction has been executed.
