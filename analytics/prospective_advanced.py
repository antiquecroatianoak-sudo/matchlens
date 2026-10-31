"""Fit the locked factor-search learner using only the last two completed seasons.

No forecasts are published by this module until independently evaluated.
"""
from datetime import date, timedelta
import numpy as np
from analytics.expanded_search import features, actual_array
from analytics.factor_search import build_design, learner, probabilities
from analytics.prospective_model_lock import read_factor_lock
from analytics.prospective_factors import prepare_future_design
from scripts.score_future_baseline import last_two_completed_seasons


def score_advanced(historical_rows, fixtures, lock_path):
    """Return scored fixtures and explicit skips; never use target-match results."""
    lock = read_factor_lock(lock_path)
    scored, skipped = [], []
    for fixture in fixtures:
        day = date.fromisoformat(fixture['date'])
        cutoff = (day - timedelta(days=2)).isoformat()
        seasons = last_two_completed_seasons(day)
        past = [r for r in historical_rows
                if r['league'] == fixture['league'] and r['season'] in seasons
                and r['date'] < cutoff and not r.get('pending')]
        future, failures = prepare_future_design(past, [fixture])
        if failures:
            skipped.extend(failures)
            continue
        records = features(past, 50, 15)
        if len(records) < 160:
            skipped.append({'id': fixture['id'], 'reason': 'insufficient historical training samples'})
            continue
        x = build_design(past, records)
        y = actual_array(records)
        if x.shape != (len(records), 84) or not np.isfinite(x).all():
            skipped.append({'id': fixture['id'], 'reason': 'invalid training features'})
            continue
        target = np.asarray(future[0]['features'], dtype=float).reshape(1, 84)
        raw = {}
        for family in ('outcome', 'goals'):
            cfg = lock[family]['config']
            cols = lock[family]['columns']
            labels = y[:, :3].argmax(axis=1) if family == 'outcome' else y[:, 3].astype(int)
            if len(np.unique(labels)) != (3 if family == 'outcome' else 2):
                raise ValueError('Training labels do not cover all required classes')
            model = learner(cfg).fit(x[:, cols], labels)
            p = model.predict_proba(target[:, cols])
            raw[family] = p if family == 'outcome' else p[:, list(model.classes_).index(1)]
        p = probabilities(raw['outcome'], raw['goals'],
                          lock['outcome']['temperature'], lock['goals']['temperature'])[0]
        if not np.isfinite(p).all() or abs(float(p[:3].sum()) - 1) > 1e-6:
            raise ValueError('Invalid advanced probabilities')
        scored.append({**fixture, 'prob': dict(zip(('home', 'draw', 'away', 'over2.5', 'under2.5'),
                                                   map(float, p))),
                       'model': 'factor_search_v1_two_completed_seasons',
                       'history_cutoff_exclusive': cutoff,
                       'history_seasons': sorted(seasons)})
    return scored, skipped
