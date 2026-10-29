"""User-approved synthetic double chance, from real same-book 1X2 prices."""
import math


def terms(selection,prices):
    legs={'1X':('1','X'),'X2':('X','2')}
    if selection not in legs:raise ValueError('Only 1X/X2 supported')
    pair=legs[selection];values=[]
    for leg in pair:
        value=prices.get(leg)
        if isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value) or value<=1:
            raise ValueError('Real numeric component odds >1 required')
        values.append(float(value))
    total=sum(1/v for v in values);odds=1/total
    return dict(selection=selection,odds=odds,stake_fractions={leg:(1/value)/total for leg,value in zip(pair,values)},
                odds_basis='synthetic_1x2',components={leg:prices[leg] for leg in pair},fees_assumed=0.)


def quote(snapshot,selection):
    """A complete same-book timestamped snapshot, not reciprocal model p."""
    from analytics.double_chance import timestamp,MARKET
    if not all(isinstance(snapshot.get(k),str) and snapshot[k].strip() for k in ('match_id','source','bookmaker','timestamp','snapshot_id')):
        raise ValueError('Identified same-book snapshot required')
    if timestamp(snapshot['timestamp']) is None:raise ValueError('Timezone required')
    t=terms(selection,snapshot['odds'])
    return dict(match_id=snapshot['match_id'],market=MARKET,selection=selection,odds=t['odds'],
                source=snapshot['source']+' / '+snapshot['bookmaker'],timestamp=snapshot['timestamp'],
                oddsBasis='synthetic_1x2',underlyingOdds=t['components'],underlyingSnapshotId=snapshot['snapshot_id'],
                underlyingBookmaker=snapshot['bookmaker'],stakeFractions=t['stake_fractions'])


def validate_quote(q):
    if q.get('oddsBasis')!='synthetic_1x2':return True
    try:
        t=terms(q['selection'],q['underlyingOdds'])
        return (bool(q.get('underlyingSnapshotId')) and bool(q.get('underlyingBookmaker'))
                and math.isclose(t['odds'],q['odds'],rel_tol=1e-10,abs_tol=1e-10))
    except (ValueError,TypeError,KeyError):return False
