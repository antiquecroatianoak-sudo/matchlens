"""Conservative cross-source fixture reconciliation report, without leakage.

Only unique team/date matches are accepted; ambiguous fixtures remain quarantined.
The audit is not a model input and never changes canonical results.
"""
import csv,json,re,unicodedata
from collections import defaultdict,Counter
from datetime import datetime,timedelta
from pathlib import Path
from analytics.backtest import load_matches

def normalize(value):
    value=unicodedata.normalize('NFKD',value.casefold())
    value=''.join(c for c in value if not unicodedata.combining(c))
    return ' '.join(re.findall(r'[a-z0-9]+',value))

def main():
    root=Path('out/external-source-audit')
    root.mkdir(parents=True,exist_ok=True)
    canonical,_=load_matches('data/openfootball')
    by_league=defaultdict(list)
    for row in canonical:by_league[(row['league'],row['season'])].append(row)
    report=[];linked=[]
    for file in sorted(root.glob('*.csv')):
        try:
            season,league,_=file.name.split('.')
        except ValueError:continue
        candidates=by_league[(league,season)]
        # A normalized exact name is permitted only when unambiguous in that league-season.
        aliases=defaultdict(set)
        for r in candidates:
            for name in (r['home'],r['away']):aliases[normalize(name)].add(name)
        counts=Counter()
        with file.open(encoding='utf-8-sig',errors='replace',newline='') as f:
            for row in csv.DictReader(f):
                if not row.get('HomeTeam') or not row.get('AwayTeam'):continue
                counts['external_rows']+=1
                h=aliases.get(normalize(row['HomeTeam']),set())
                a=aliases.get(normalize(row['AwayTeam']),set())
                if len(h)!=1 or len(a)!=1:
                    counts['unresolved_team_alias']+=1;continue
                try:
                    d=datetime.strptime(row['Date'],'%d/%m/%Y').date()
                except (ValueError,KeyError):
                    try:d=datetime.strptime(row['Date'],'%d/%m/%y').date()
                    except (ValueError,KeyError):counts['invalid_date']+=1;continue
                # Allow a one-day timezone/date discrepancy, but never multiple candidates.
                matches=[r for r in candidates if r['home'] in h and r['away'] in a and abs((datetime.fromisoformat(r['date']).date()-d).days)<=1]
                if len(matches)!=1:counts['ambiguous_or_missing_fixture']+=1;continue
                match=matches[0]
                if row.get('FTHG') not in ('',None) and row.get('FTAG') not in ('',None):
                    try:valid=int(row['FTHG'])==match['hg'] and int(row['FTAG'])==match['ag']
                    except ValueError:valid=False
                    if not valid:counts['score_conflict']+=1;continue
                counts['matched']+=1
                linked.append({'canonical_id':match['id'],'source':'football-data.co.uk',
                               'source_date':row['Date'],'source_home':row['HomeTeam'],'source_away':row['AwayTeam'],
                               'available_fields':[k for k in ('HS','AS','HST','AST','B365H','B365D','B365A') if row.get(k) not in ('',None)]})
        report.append({'file':file.name,**dict(counts)})
    duplicates=Counter(x['canonical_id'] for x in linked)
    linked=[x for x in linked if duplicates[x['canonical_id']]==1]
    summary={'mode':'research_only_no_model_training','matched_unique':len(linked),
             'quarantined_duplicate_links':sum(v for v in duplicates.values() if v>1),
             'by_file':report,'warning':'Postmatch statistics are NOT pre-match features; odds require timestamp validation.'}
    (root/'fixture-links.jsonl').write_text(''.join(json.dumps(x)+'\n' for x in linked))
    (root/'reconciliation.json').write_text(json.dumps(summary,indent=2))
    print('SOURCE RECONCILIATION',json.dumps({k:v for k,v in summary.items() if k!='by_file'}),flush=True)
if __name__=='__main__':main()
