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

ALIASES = {'man united':'manchester united','man city':'manchester city',
 'wolves':'wolverhampton wanderers','spurs':'tottenham hotspur',
 'newcastle':'newcastle united','west ham':'west ham united',
 'brighton':'brighton and hove albion','leicester':'leicester city',
 'inter':'internazionale','ac milan':'milan','juventus':'juventus',
 'psg':'paris saint germain','paris sg':'paris saint germain',
 'bayern munich':'bayern munchen','bayern munchen':'bayern munchen',
 'gladbach':'borussia monchengladbach','m gladbach':'borussia monchengladbach',
 'atletico madrid':'atletico de madrid','ath madrid':'atletico de madrid',
 'ath bilbao':'athletic club','athletic bilbao':'athletic club',
 'real sociedad':'real sociedad','sporting lisbon':'sporting cp',
 'porto':'fc porto','benfica':'sl benfica'}
def canonical_team(name):
    key=normalize(name)
    return ALIASES.get(key,key)

def main():
    root=Path('out/external-source-audit')
    root.mkdir(parents=True,exist_ok=True)
    canonical,_=load_matches('data/openfootball')
    by_league=defaultdict(list)
    for row in canonical:by_league[(row['league'],row['season'])].append(row)
    report=[];linked=[];unresolved=Counter()
    for file in sorted(root.glob('*.csv')):
        try:
            season,league=file.name.removesuffix('.csv').split('.',1)
        except ValueError:continue
        candidates=by_league[(league,season)]
        # A normalized exact name is permitted only when unambiguous in that league-season.
        aliases=defaultdict(set)
        for r in candidates:
            for name in (r['home'],r['away']):aliases[canonical_team(name)].add(name)
        counts=Counter()
        with file.open(encoding='utf-8-sig',errors='replace',newline='') as f:
            for row in csv.DictReader(f):
                if not row.get('HomeTeam') or not row.get('AwayTeam'):continue
                counts['external_rows']+=1
                h=aliases.get(canonical_team(row['HomeTeam']),set())
                a=aliases.get(canonical_team(row['AwayTeam']),set())
                if len(h)!=1 or len(a)!=1:
                    counts['unresolved_team_alias']+=1
                    if len(h)!=1:unresolved[(league,'home',row['HomeTeam'])]+=1
                    if len(a)!=1:unresolved[(league,'away',row['AwayTeam'])]+=1
                    continue
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
             'by_file':report,'unresolved_teams':[{'league':league,'side':side,'name':name,'count':count} for (league,side,name),count in unresolved.most_common(100)],'warning':'Postmatch statistics are NOT pre-match features; odds require timestamp validation.'}
    (root/'fixture-links.jsonl').write_text(''.join(json.dumps(x)+'\n' for x in linked))
    (root/'reconciliation.json').write_text(json.dumps(summary,indent=2))
    totals=dict(sum((Counter({k:v for k,v in row.items() if k!='file'}) for row in report),Counter()))
    print('SOURCE RECONCILIATION',json.dumps({**{k:v for k,v in summary.items() if k!='by_file'},'totals':totals,'sample_files':report[:3],'top_unresolved_teams':summary['unresolved_teams'][:20]}),flush=True)
    if list(root.glob('*.csv')) and not linked:
        raise SystemExit('External CSV files exist but no fixtures reconciled; inspect alias/date diagnostics')
if __name__=='__main__':main()
