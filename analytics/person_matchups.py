"""As-of, cross-club coach and direct player-pair history.
Source facts must use canonical IDs and verified availability timestamps.
No inferred duels from shared lineups, no effect inferred from a club transfer.
"""
import argparse,json,math
from collections import defaultdict
from datetime import datetime,timezone
from pathlib import Path

SCHEMA='person-matchups-v1'

def instant(value):
    if not isinstance(value,str):raise ValueError('ISO timestamp required')
    d=datetime.fromisoformat(value.replace('Z','+00:00'))
    if d.tzinfo is None:raise ValueError('Timezone required')
    return d.astimezone(timezone.utc)

def number(value,low,high):
    if isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value) or not low<=value<=high:raise ValueError('Invalid numeric value')
    return float(value)

def identifier(row,key):
    if not isinstance(row.get(key),str) or not row[key].strip():raise ValueError('Canonical identity required: '+key)
    return row[key]

def validate(row,kind):
    for key in ('record_id','match_id','team_id','opponent_id','source_id'):identifier(row,key)
    if row['team_id']==row['opponent_id']:raise ValueError('Same team on both sides')
    occurred=instant(row['occurred_at']);available=instant(row['available_at'])
    if available<occurred:raise ValueError('Outcome known before occurrence')
    if kind=='coach':
        identifier(row,'coach_id');number(row['points'],0,3)
        if row['points'] not in (0,1,3):raise ValueError('Invalid match points')
        number(row['expected_points'],0,3)
        # Expected value must itself have been frozen before the historic game.
        if instant(row['baseline_generated_at'])>=occurred:raise ValueError('Leaked historical strength baseline')
        identifier(row,'baseline_version')
    elif kind=='duel':
        for key in ('attacker_id','defender_id','event_type','attacker_role','defender_role','pair_evidence'):identifier(row,key)
        if row['attacker_id']==row['defender_id']:raise ValueError('Self duel')
        if row['pair_evidence']!='explicit_link':raise ValueError('Only explicit direct opponent evidence accepted')
        number(row['success'],0,1)
        if row['success'] not in (0,1):raise ValueError('Binary duel outcome required')
    else:raise ValueError('Unknown fact kind')
    return dict(row)

def prepare(rows,kind):
    # Duplicate identities cannot count as independent observations.
    seen=set();out=[]
    for raw in rows:
        row=validate(raw,kind)
        key=(row['match_id'],row['coach_id'] if kind=='coach' else row['record_id'])
        if key in seen:raise ValueError('Duplicate source record')
        seen.add(key);out.append(row)
    return out

def eligible(rows,as_of,target_match):
    cutoff=instant(as_of)
    return [r for r in rows if r['match_id']!=target_match and instant(r['occurred_at'])<cutoff and instant(r['available_at'])<=cutoff]

def weight(row,as_of,half_life_days):
    return 2**(-(instant(as_of)-instant(row['occurred_at'])).total_seconds()/(86400*half_life_days))

def estimate(rows,as_of,residual,current_team,prior,min_matches):
    if not rows:return dict(value=None,observations=0,matches=0,cross_club_matches=0,effective_weight=0.,supported=False)
    # Equal total influence per fixture; many logged events in one game cannot dominate.
    by_match=defaultdict(list)
    for row in rows:by_match[row['match_id']].append(row)
    total=0.;weighted=0.
    for group in by_match.values():
        w=weight(group[0],as_of,365);total+=w;weighted+=w*sum(residual(r) for r in group)/len(group)
    return dict(value=weighted/(total+prior),observations=len(rows),matches=len(by_match),cross_club_matches=len({r['match_id'] for r in rows if r['team_id']!=current_team}),effective_weight=total,supported=len(by_match)>=min_matches,shrinkage_prior_matches=prior)

class PersonHistory:
    def __init__(self,coaches=(),duels=()):
        self.coaches=prepare(coaches,'coach');self.duels=prepare(duels,'duel')

    def coach(self,coach_id,current_team,opponent_id,as_of,target_match,prior=8.,min_matches=5):
        past=eligible(self.coaches,as_of,target_match)
        rows=[r for r in past if r['coach_id']==coach_id and r['opponent_id']==opponent_id]
        # Residual is relative to the old club's pre-game strength expectation.
        return estimate(rows,as_of,lambda r:(r['points']-r['expected_points'])/3,current_team,prior,min_matches)

    def pair(self,attacker_id,defender_id,current_team,as_of,target_match,event_type,attacker_role,defender_role,prior=8.,min_matches=5):
        past=[r for r in eligible(self.duels,as_of,target_match) if r['event_type']==event_type and r['attacker_role']==attacker_role and r['defender_role']==defender_role]
        pair=[r for r in past if r['attacker_id']==attacker_id and r['defender_id']==defender_id]
        # Pair-specific effect relative to each person's performance against OTHER opponents.
        a=[r for r in past if r['attacker_id']==attacker_id and r['defender_id']!=defender_id]
        d=[r for r in past if r['defender_id']==defender_id and r['attacker_id']!=attacker_id]
        def rate(rows):
            groups=defaultdict(list)
            for r in rows:groups[r['match_id']].append(r)
            ws=[weight(g[0],as_of,365) for g in groups.values()]
            rates=[sum(r['success'] for r in g)/len(g) for g in groups.values()]
            return (sum(w*v for w,v in zip(ws,rates))+5*.5)/(sum(ws)+5)
        baseline=(rate(a)+rate(d))/2
        result=estimate(pair,as_of,lambda r:r['success']-baseline,current_team,prior,min_matches)
        result['opponent_adjusted_baseline']=baseline
        result['comparison_observations']=dict(attacker=len(a),defender=len(d))
        result['comparison_matches']=dict(attacker=len({r['match_id'] for r in a}),defender=len({r['match_id'] for r in d}))
        result['supported']=result['supported'] and len(a)>=10 and len(d)>=10 and min(result['comparison_matches'].values())>=5
        return result

    def target(self,target):
        cutoff=instant(target['as_of'])
        for key in ('match_id','team_id','opponent_id'):identifier(target,key)
        if target.get('coach_id') and instant(target['coach_known_at'])>cutoff:raise ValueError('Future coach appointment information')
        if target.get('expected_pairs') and instant(target['lineup_known_at'])>cutoff:raise ValueError('Future lineup information')
        coach=self.coach(target['coach_id'],target['team_id'],target['opponent_id'],target['as_of'],target['match_id']) if target.get('coach_id') else dict(value=None,supported=False,matches=0)
        pairs=[];seen=set()
        for p in target.get('expected_pairs',[]):
            key=tuple(p[k] for k in ('attacker_id','defender_id','event_type','attacker_role','defender_role'))
            if key in seen:raise ValueError('Duplicate expected pair')
            seen.add(key);exposure=number(p['expected_overlap_minutes'],0,90)/90
            # Explicit joint participation probability supplied before kickoff; do not multiply independent marginals.
            exposure*=number(p['joint_participation_probability'],0,1)
            r=self.pair(p['attacker_id'],p['defender_id'],target['team_id'],target['as_of'],target['match_id'],p['event_type'],p['attacker_role'],p['defender_role'])
            pairs.append(dict(pair=p,estimate=r,exposure=exposure))
        supported=[r for r in pairs if r['estimate']['supported'] and r['exposure']>0]
        total=sum(r['exposure'] for r in supported)
        by_type=defaultdict(list)
        for r in supported:by_type[r['pair']['event_type']].append(r)
        effects={k:sum(r['exposure']*r['estimate']['value'] for r in group)/sum(r['exposure'] for r in group) for k,group in by_type.items()}
        combined=next(iter(effects.values())) if len(effects)==1 else None
        return dict(schema=SCHEMA,match_id=target['match_id'],as_of=target['as_of'],coach=coach,pairs=pairs,
                    player_pair_effect=combined,player_pair_effect_by_type=effects,
                    model_columns=dict(coach_opponent_residual=coach.get('value') if coach.get('supported') else None,coach_history_matches=coach.get('matches',0),player_pair_residual=combined,player_pair_residual_by_type=effects,player_pair_coverage=len(supported)/len(pairs) if pairs else None),
                    supported_pair_count=len(supported),expected_pair_count=len(pairs),model_ready=coach.get('supported',False) or bool(supported),
                    note='Candidate features only. Learned weights and historical ablation still required; never a manual probability bonus.')

def load_jsonl(path):
    return [json.loads(s) for s in Path(path).read_text().splitlines() if s.strip()]

def build(coaches,duels,targets,output):
    out=Path(output);out.mkdir(parents=True,exist_ok=False);history=PersonHistory(load_jsonl(coaches),load_jsonl(duels));results=[history.target(t) for t in load_jsonl(targets)]
    (out/'person-features.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in results))
    return results

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--coaches',required=True);p.add_argument('--duels',required=True);p.add_argument('--targets',required=True);p.add_argument('--output',required=True);a=p.parse_args();build(a.coaches,a.duels,a.targets,a.output)
