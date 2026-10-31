"""Evaluate locked 84-feature model on real upcoming fixtures without publishing picks.

Uses the two most recently completed seasons; writes a separate challenger artifact.
"""
import json
from collections import defaultdict
from datetime import date
from pathlib import Path
from analytics.backtest import load_matches
from analytics.prospective_advanced import score_advanced
from scripts.score_future_baseline import LEAGUE_MAP, normalize_team, last_two_completed_seasons

LOCK = 'data/experiments/20261029-factor-search-v1/factor-lock.json'


def main():
    source = json.loads(Path('out/future-fixtures.json').read_text())
    history, _ = load_matches('data/openfootball')
    by_league = defaultdict(list)
    for row in history:
        by_league[row['league']].append(row)
    accepted, skipped = [], []
    for f in source['fixtures']:
        league = LEAGUE_MAP.get(f['league'], f['league'])
        day = date.fromisoformat(f['kickoff_utc'][:10])
        eligible = [r for r in by_league[league]
                    if r['season'] in last_two_completed_seasons(day)]
        known = {t for r in eligible for t in (r['home'], r['away'])}
        home = normalize_team(f['home'], known)
        away = normalize_team(f['away'], known)
        if not home or not away:
            skipped.append({'id': f['id'], 'reason': 'unmapped historical team'})
            continue
        canonical = {'id': f['id'], 'date': day.isoformat(), 'league': league,
                     'home': home, 'away': away}
        try:
            scores, failures = score_advanced(eligible, [canonical], LOCK)
        except (ValueError, RuntimeError, KeyError) as exc:
            skipped.append({'id': f['id'], 'reason': type(exc).__name__ + ': ' + str(exc)[:160]})
            continue
        skipped.extend(failures)
        for scored in scores:
            accepted.append({**f, 'prob': scored['prob'], 'model': scored['model'],
                             'history_cutoff_exclusive': scored['history_cutoff_exclusive'],
                             'history_seasons': scored['history_seasons'],
                             'historical_home': home, 'historical_away': away,
                             'status': 'challenger_research_only'})
    Path('out/upcoming-advanced-probabilities.jsonl').write_text(
        ''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in accepted))
    Path('out/upcoming-advanced-coverage.json').write_text(
        json.dumps({'fixtures': len(source['fixtures']), 'scored': len(accepted),
                    'skipped': skipped, 'status': 'research_only_not_published'}, indent=2))
    print('ADVANCED CHALLENGER', len(accepted), 'OF', len(source['fixtures']))


if __name__ == '__main__':
    main()
