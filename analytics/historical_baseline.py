"""Leakage-safe walk-forward baseline for dated historical football results.

Input: list of dicts with match_id, kickoff (ISO 8601 UTC/offset), home, away,
home_goals, away_goals. Missing results are excluded from training/scoring.
No external dataset is bundled or inferred. Prediction uses only prior matches.
"""
from datetime import datetime, timezone
import math

def utc(value):
    d = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if d.tzinfo is None:
        raise ValueError("Timezone required")
    return d.astimezone(timezone.utc)

def poisson(lam, n):
    return math.exp(-lam) * lam ** n / math.factorial(n)

def probabilities(home_rate, away_rate):
    p = [0., 0., 0., 0.]
    total = 0.
    for h in range(15):
        for a in range(15):
            mass = poisson(home_rate, h) * poisson(away_rate, a)
            total += mass
            p[0 if h > a else 1 if h == a else 2] += mass
            if h + a > 2:
                p[3] += mass
    return [v / total for v in p]

def walk_forward(matches, min_history=10, delay_days=2):
    if min_history < 1 or delay_days < 0:
        raise ValueError("Invalid history settings")
    rows = sorted(matches, key=lambda r: (utc(r["kickoff"]), r["match_id"]))
    if len({r["match_id"] for r in rows}) != len(rows):
        raise ValueError("Duplicate match ID")
    out = []
    for current in rows:
        t = utc(current["kickoff"])
        prior = [r for r in rows if utc(r["kickoff"]).timestamp() <= t.timestamp() - delay_days * 86400
                 and r.get("home_goals") is not None and r.get("away_goals") is not None]
        if len(prior) < min_history:
            continue
        # Smoothed league-level attack rates; a deliberately simple control baseline.
        n = len(prior)
        home_rate = (sum(r["home_goals"] for r in prior) + 10 * 1.4) / (n + 10)
        away_rate = (sum(r["away_goals"] for r in prior) + 10 * 1.1) / (n + 10)
        probs = probabilities(home_rate, away_rate)
        if current.get("home_goals") is None or current.get("away_goals") is None:
            outcome = None
        else:
            h, a = current["home_goals"], current["away_goals"]
            outcome = 0 if h > a else 1 if h == a else 2
        out.append(dict(match_id=current["match_id"], kickoff=current["kickoff"],
                        probabilities_1x2=probs[:3], probability_over25=probs[3],
                        outcome=outcome, training_matches=n))
    scored = [r for r in out if r["outcome"] is not None]
    brier = (sum(sum((p - (i == r["outcome"])) ** 2 for i, p in enumerate(r["probabilities_1x2"])) for r in scored) / len(scored)) if scored else None
    accuracy = (sum(max(range(3), key=lambda i: r["probabilities_1x2"][i]) == r["outcome"] for r in scored) / len(scored)) if scored else None
    return dict(predictions=out, scored=len(scored), accuracy_1x2=accuracy, brier_1x2=brier)
