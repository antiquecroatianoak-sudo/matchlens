"""Audit 25% selection, group errors, and compare fixed prematch-only ranking rules.
Retrospective comparisons are exploratory; never optimize on the audit outcomes.
"""
import argparse,collections,json,math
from pathlib import Path
from scripts.top25_single_pick import select,MARKETS

def alternative(rows,rule):
    changed=[]
    for r in rows:
        p=r['prob']
        if rule=='outcomes_only':markets=MARKETS[:3]
        elif rule=='totals_only':markets=MARKETS[3:]
        else:markets=MARKETS
        market=max(markets,key=lambda m:p[m])
        confidence=p[market]
        if rule=='margin':
            # Compare within the same exclusive outcome family, not across 1X2 and totals.
            family=MARKETS[:3] if market in MARKETS[:3] else MARKETS[3:]
            margin=confidence-max(p[m] for m in family if m!=market)
            score=(confidence+0.10*margin)/1.10
        elif rule=='outcomes_only' or rule=='totals_only':score=confidence
        elif rule=='balanced':
            # Avoid treating raw probabilities from 3-way and 2-way markets as identical.
            home=max(MARKETS[:3],key=lambda m:p[m])
            total=max(MARKETS[3:],key=lambda m:p[m])
            market=home if p[home]-1/3 >= p[total]-1/2 else total
            score=p[market]-(1/3 if market in MARKETS[:3] else 1/2)+0.5
        else:score=confidence
        clone=dict(r,prob={m:(min(1.,max(0.,score)) if m==market else 0.) for m in MARKETS})
        clone['_market']=market
        changed.append(clone)
    return changed

def evaluate(rows,rule):
    if rule=='original':return select(rows)
    altered=alternative(rows,rule)
    report=select(altered)
    lookup={r['id']:r for r in rows}
    market_lookup={r['id']:r['_market'] for r in altered}
    for item in report['selected']:
        actual=lookup[item['id']]
        item['market']=market_lookup[item['id']]
        item['correct']=bool(actual['actual'][item['market']])
        item['probability']=actual['prob'][item['market']]
    hits=sum(int(x['correct']) for x in report['selected'])
    report['summary']['hits']=hits
    report['summary']['hit_rate']=hits/len(report['selected']) if report['selected'] else None
    return report

def breakdown(selected,key):
    groups=collections.defaultdict(list)
    for r in selected:groups[str(r[key])].append(r)
    return {k:{'selected':len(v),'hits':sum(bool(x['correct']) for x in v),
               'hit_rate':sum(bool(x['correct']) for x in v)/len(v)}
            for k,v in sorted(groups.items())}

def probability_audit(selected):
    groups=collections.defaultdict(list)
    for item in selected:
        bucket=min(9,int(item['probability']*10))
        groups[(item['market'],bucket)].append(item)
    return [{'market':market,'probability_bin':f'{bucket/10:.1f}-{(bucket+1)/10:.1f}',
             'count':len(items),'mean_predicted':sum(x['probability'] for x in items)/len(items),
             'actual_hit_rate':sum(x['correct'] for x in items)/len(items)}
            for (market,bucket),items in sorted(groups.items())]

def round_completeness(rows):
    groups=collections.defaultdict(list)
    for r in rows:groups[(r['league'],r['season'],str(r['round']))].append(r)
    by_league_season=collections.defaultdict(list)
    for (league,season,round_id),fixtures in groups.items():
        by_league_season[(league,season)].append((round_id,len(fixtures)))
    result=[]
    for (league,season),rounds in sorted(by_league_season.items()):
        sizes=sorted(n for _,n in rounds)
        # Mode is an observed typical round size, not an asserted official schedule.
        typical=collections.Counter(sizes).most_common(1)[0][0]
        unusual=[{'round':rid,'fixtures':n} for rid,n in rounds if n<typical]
        result.append({'league':league,'season':season,'typical_observed_round_size':typical,
            'round_count':len(rounds),'underfilled_round_count':len(unusual),
            'underfilled_examples':unusual[:10]})
    return result

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--input',required=True)
    ap.add_argument('--output',required=True)
    args=ap.parse_args()
    rows=[json.loads(line) for line in Path(args.input).read_text().splitlines() if line.strip()]
    original=evaluate(rows,'original')
    issues={
      'rounds_with_less_than_four_fixtures':sum(r['fixtures']<4 for r in original['rounds']),
      'rounds_with_zero_capacity':sum(r['limit']==0 for r in original['rounds']),
      'rounds_with_partial_data':sum(r['fixtures'] not in (8,9,10,12,16,18,20) for r in original['rounds']),
      'total_selection_capacity':sum(r['limit'] for r in original['rounds']),
      'capacity_unused':sum(r['limit']-r['selected'] for r in original['rounds']),
      'selection_share':len(original['selected'])/len(rows)
    }
    selected=original['selected']
    selected_ids=[r['id'] for r in selected]
    if len(selected_ids)!=len(set(selected_ids)):
        raise ValueError('Multiple selected tips for the same fixture')
    if any(r['market'] not in MARKETS for r in selected):
        raise ValueError('Unsupported single-pick market')
    if any(r['selected']>r['limit'] for r in original['rounds']):
        raise ValueError('Selection exceeded the per-round 25% cap')
    diagnostics={'fixtures':len(rows),'rounds':len(original['rounds']),'issues':issues,
       'baseline':original['summary'],'by_league':breakdown(selected,'league'),
       'by_season':breakdown(selected,'season'),'by_market':breakdown(selected,'market'),
       'probability_calibration':probability_audit(selected),
       'round_completeness':round_completeness(rows),
       'alternatives':{}}
    for rule in ('outcomes_only','totals_only','margin','balanced'):
        result=evaluate(rows,rule)
        diagnostics['alternatives'][rule]={'summary':result['summary'],
             'by_season':breakdown(result['selected'],'season')}
    baseline=diagnostics['baseline']
    # Require the same number of selections, a material aggregate gain and no
    # severe deterioration in the latest two seasons before recommending a rule.
    eligible=[]
    for rule,info in diagnostics['alternatives'].items():
        summary=info['summary']
        if summary['selected']!=baseline['selected']:continue
        if summary['hit_rate'] is None or summary['hit_rate']<baseline['hit_rate']+0.015:continue
        original_seasons=breakdown(selected,'season')
        latest=sorted(original_seasons)[-2:]
        if any(info['by_season'][season]['hit_rate']<original_seasons[season]['hit_rate']-0.03 for season in latest):continue
        eligible.append(rule)
    diagnostics['eligible_for_further_validation']=eligible
    diagnostics['recommendation']='Keep original until independent future-season confirmation; retrospective eligibility is not deployment approval.'
    diagnostics['warning']='All alternatives are exploratory on viewed data. No claim of out-of-sample improvement.'
    path=Path(args.output);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(diagnostics,indent=2)+'\n')
    print('SELECTION DIAGNOSTICS',json.dumps(diagnostics),flush=True)
if __name__=='__main__':main()
