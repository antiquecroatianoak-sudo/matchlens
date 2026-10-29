"""Quote-gated 1X / X2 adapters; never infer odds from model probabilities.

Keeps old five-market audit archives unchanged. No verified quote means no offer.
"""
from datetime import datetime
import math

MARKET='Dvostruka šansa'


def timestamp(value):
    try:
        d=datetime.fromisoformat(value.replace('Z','+00:00'))
        return d.timestamp() if d.tzinfo else None
    except (ValueError,TypeError,AttributeError):return None


def probabilities(outcome):
    p=[float(v) for v in outcome]
    if len(p)!=3 or any(not math.isfinite(v) or not 0<=v<=1 for v in p) or not math.isclose(sum(p),1,abs_tol=1e-6):
        raise ValueError('Expected normalized home/draw/away probabilities')
    return {'1X':min(1.,p[0]+p[1]),'X2':min(1.,p[1]+p[2])}


def offers(match_id,outcome,quotes,generated_at,kickoff):
    """Quote fields must identify this exact match, market and selection.

    Input source verification is the responsibility of the future source adapter.
    This function does not confer verified/live status or fabricate validation.
    """
    generated=timestamp(generated_at);start=timestamp(kickoff)
    if generated is None or start is None or generated>=start:
        raise ValueError('Generation must have a timezone and precede kickoff')
    pp=probabilities(outcome);valid={}
    for q in quotes:
        selection=q.get('selection');odds=q.get('odds');quoted=timestamp(q.get('timestamp'))
        if q.get('match_id')!=match_id or q.get('market')!=MARKET or selection not in pp:continue
        if isinstance(odds,bool) or not isinstance(odds,(int,float)) or not math.isfinite(odds) or odds<=1:continue
        if not isinstance(q.get('source'),str) or not q['source'].strip() or quoted is None or quoted>generated:continue
        key=(selection,q['source'])
        if key in valid and valid[key][0]>=quoted:continue
        valid[key]=(quoted,dict(matchId=match_id,market=MARKET,selection=selection,prob=100*pp[selection],
            odds=odds,oddsMatchId=match_id,oddsMarket=MARKET,oddsSelection=selection,
            oddsTimestamp=q['timestamp'],oddsSource=q['source'],generatedAt=generated_at,kickoff=kickoff))
    result=[]
    for selection in ('1X','X2'):
        candidates=[v for (s,source),v in valid.items() if s==selection and v[1]['odds']>=2]
        if candidates:result.append(max(candidates,key=lambda v:(v[1]['odds'],v[0],v[1]['oddsSource']))[1])
    return result


def settle(selection,home_goals,away_goals):
    if selection not in ('1X','X2'):raise ValueError('Unsupported double chance')
    if home_goals is None or away_goals is None:return None
    if any(isinstance(v,bool) or not isinstance(v,int) or v<0 for v in (home_goals,away_goals)):
        raise ValueError('Expected known regular-time goals')
    return int(home_goals>=away_goals if selection=='1X' else away_goals>=home_goals)
