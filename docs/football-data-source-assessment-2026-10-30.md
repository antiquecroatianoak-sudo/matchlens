# MatchLens: public football data source assessment (2026-10-30)

Purpose: increase trustworthy pre-match feature coverage, especially goal-market calibration, without leakage or duplicate fixtures.

| Source | Data | Decision |
|---|---|---|
| openfootball/football.json | League fixtures/results, CC0 | ALREADY USED: scripts/restore_openfootball_history.py; do not import duplicate matches |
| openfootball/europe | More European schedules/results, CC0 | Candidate for missing rounds and reconciliation; first compare IDs and season/league coverage |
| football-data.co.uk | Results, match statistics, odds CSV | High-priority pilot; verify terms, timestamps and historical pre-match availability before importing features |
| statsbomb/open-data | Event/shot/lineup JSON, custom attribution terms | Research pilot for xG/event model; limited competition coverage; do not infer historical prematch features from match events of the target game |
| probberechts/soccerdata | Multi-provider Python retrieval library | Tool, NOT a data licence; assess provider terms and scraping constraints individually |
| Club Elo | Historical club strength ratings | Candidate; use rating snapshot strictly before kickoff; verify API usage rights |
| Wyscout Pappalardo | Historical events, CC BY 4.0 | Research-only supplementary validation for event features; limited seasons |
| Understat / FBref | xG and other statistics | Assess provider terms; no automated scraping without appropriate permission |

## Required ingestion checks

1. Record source, provider licence/terms, acquisition timestamp, original fixture identifier and match kickoff time.
2. Canonicalize league/season/team IDs and reconcile home/away/date; quarantine conflicting fixtures instead of silently overwriting.
3. Report coverage per league, season and round; distinguish genuine playoff rounds from missing matches.
4. For every feature, enforce `feature_timestamp < fixture_kickoff`. Match-level xG, shots and closing odds are not automatically available pre-match.
5. Build rolling team xG and goal-rate features using **prior** matches only; compare goal-market calibration by probability bucket.
6. Use time-separated development and untouched future holdout. Never select a source or ranking rule based solely on the holdout's outcome.
7. Preserve at most floor(fixtures_in_round / 4) selections, one market per fixture, and log both accuracy and number selected.

## Suggested order

1. Audit existing OpenFootball coverage and short playoff rounds.
2. Prototype football-data.co.uk importer in a quarantined research dataset; validate timestamp and terms.
3. Evaluate rolling prior-match goal features and reliability calibration on development seasons.
4. Add StatsBomb event features only where matched prior-match coverage exists; compare against a strong no-event baseline.
5. Promote a change only after robust prospective/time-separated evaluation; retain old selector as fallback.

Sources:
- https://github.com/openfootball/europe
- https://www.football-data.co.uk/data.php
- https://github.com/statsbomb/open-data
- https://github.com/probberechts/soccerdata
- https://github.com/withqwerty/open-football
