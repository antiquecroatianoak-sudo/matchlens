"""Build leakage-safe factor-search feature vectors for future fixtures.

This module prepares the same 84-dimensional design as the historical learner.
It does not train or publish an unvalidated model.
"""
from datetime import date, timedelta
import numpy as np
from analytics.expanded_search import features
from analytics.factor_search import build_design
from scripts.score_future_baseline import last_two_completed_seasons


def prepare_future_design(historical_rows, fixtures):
    """Return (accepted, skipped), preserving input fixture order.

    Fixtures use canonical historical league/team names and YYYY-MM-DD dates.
    All model inputs come from the two most recently completed seasons.
    """
    accepted, skipped = [], []
    for fixture in fixtures:
        day = date.fromisoformat(fixture['date'])
        cutoff = (day - timedelta(days=2)).isoformat()
        seasons = last_two_completed_seasons(day)
        past = [r for r in historical_rows if r['season'] in seasons and r['date'] < cutoff
                and r['league'] == fixture['league']]
        known = {name for r in past for name in (r['home'], r['away'])}
        if fixture['home'] not in known or fixture['away'] not in known:
            skipped.append({'id': fixture['id'], 'reason': 'unmapped or insufficient team history'})
            continue
        pending = {**fixture, 'season': f"{day.year if day.month >= 7 else day.year - 1}-{str((day.year + 1 if day.month >= 7 else day.year) % 100).zfill(2)}",
                   'pending': True}
        records = features(past + [pending], 50, 15)
        targets = [r for r in records if r['match']['id'] == fixture['id']]
        if len(targets) != 1:
            skipped.append({'id': fixture['id'], 'reason': 'insufficient two-season feature coverage'})
            continue
        vector = build_design(past + [pending], targets)
        if vector.shape != (1, 84) or not np.isfinite(vector).all():
            skipped.append({'id': fixture['id'], 'reason': 'invalid advanced feature vector'})
            continue
        accepted.append({'fixture': fixture, 'features': vector[0].tolist(),
                         'history_cutoff_exclusive': cutoff,
                         'history_seasons': sorted(seasons),
                         'model_status': 'features_only_not_scored'})
    return accepted, skipped
