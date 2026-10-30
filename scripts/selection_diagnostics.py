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
            score=confidence+0.10*margin
        elif rule=='outcomes_only' or rule=='totals_only':score=confidence
        elif rule=='balanced':
            # Avoid treating raw probabilities from 3-way and 2-way markets as identical.
            home=max(MARKETS[:3],key=lambda m:p[m])
            total=max(MARKETS[3:],key=lambda m:p[m])
            market=home if p[home]-1/3 >= p[total]-1/2 else total
            score=p[market]-(1/3 if market in MARKETS[:3] else 1/2)
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
    diagnostics={'fixtures':len(rows),'rounds':len(original['rounds']),'issues':issues,
       'baseline':original['summary'],'by_league':breakdown(selected,'league'),
       'by_season':breakdown(selected,'season'),'by_market':breakdown(selected,'market'),
       'alternatives':{}}
    for rule in ('outcomes_only','totals_only','margin','balanced'):
        result=evaluate(rows,rule)
        diagnostics['alternatives'][rule]={'summary':result['summary'],
             'by_season':breakdown(result['selected'],'season')}
    diagnostics['warning']='All alternatives are exploratory on viewed data. No claim of out-of-sample improvement.'
    path=Path(args.output);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(diagnostics,indent=2)+'\n')
    print('SELECTION DIAGNOSTICS',json.dumps(diagnostics),flush=True)
if __name__=='__main__':main()
