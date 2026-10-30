"""Generate honest prematch probabilities using the existing historical Poisson baseline.

Research fallback while full factor-model prospective inference is not implemented.
"""
import json
from collections import defaultdict
from datetime import date,timedelta
from pathlib import Path
from analytics.backtest import load_matches,predict

def main():
    fixture_file=Path('out/future-fixtures.json')
    payload=json.loads(fixture_file.read_text())
    history,_=load_matches('data/openfootball')
    by_league=defaultdict(list)
    for row in history:by_league[row['league']].append(row)
    result=[];skipped=[]
    for f in payload['fixtures']:
        match_date=date.fromisoformat(f['kickoff_utc'][:10])
        cutoff=(match_date-timedelta(days=2)).isoformat()
        past=[r for r in by_league[f['league']] if r['date']<cutoff]
        match={'date':match_date.isoformat(),'home':f['home'],'away':f['away']}
        # The historical predictor uses only supplied past results.
        probs=predict(past,match,{'window':50,'half_life':15,'prior':8})
        if probs is None:
            skipped.append({'id':f['id'],'reason':'insufficient historical team or league coverage'})
            continue
        result.append({**f,'prob':probs,'model':'historical_poisson_fallback_v1',
                       'history_cutoff_exclusive':cutoff})
    out=Path('out/upcoming-probabilities.jsonl')
    out.write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in result))
    Path('out/upcoming-coverage.json').write_text(json.dumps({
        'source_fixtures':len(payload['fixtures']),'scored':len(result),'skipped':skipped,
        'warning':'Poisson fallback, NOT the previously evaluated factor model; no accuracy claim.'},indent=2))
    print('FUTURE PREMATCH SCORED',len(result),'OF',len(payload['fixtures']))
if __name__=='__main__':main()
