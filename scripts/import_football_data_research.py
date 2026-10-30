"""Download and reconcile public Football-Data.co.uk league-season CSVs.
Supplementary research only: no post-match fields enter prematch features.
"""
import csv,io,json,urllib.request
from pathlib import Path
from collections import Counter
from analytics.backtest import load_matches

LEAGUES={'en.1':'E0','de.1':'D1','it.1':'I1','es.1':'SP1','fr.1':'F1',
         'nl.1':'N1','pt.1':'P1','be.1':'B1','tr.1':'T1','gr.1':'G1'}
YEARS=range(2017,2026)
BASE='https://www.football-data.co.uk/mmz4281'
def main():
    dest=Path('out/external-source-audit');dest.mkdir(parents=True,exist_ok=True)
    canonical,_=load_matches('data/openfootball')
    report=[];total=0
    for year in YEARS:
        season=f'{year}-{(year+1)%100:02d}'
        for league,division in LEAGUES.items():
            url=f'{BASE}/{year%100:02d}{(year+1)%100:02d}/{division}.csv'
            item={'source':'football-data.co.uk','league':league,'season':season,'url':url}
            try:
                request=urllib.request.Request(url,headers={'User-Agent':'MatchLensResearch/1.0'})
                with urllib.request.urlopen(request,timeout=12) as response:
                    raw=response.read(5_000_000)
                content=raw.decode('utf-8-sig',errors='replace')
                rows=list(csv.DictReader(io.StringIO(content)))
                rows=[r for r in rows if r.get('HomeTeam') and r.get('AwayTeam') and r.get('FTHG') not in (None,'') and r.get('FTAG') not in (None,'')]
                if not rows:raise ValueError('No completed match rows')
                item.update(status='available',completed_matches=len(rows),
                    available_columns=sorted(set(rows[0]).intersection({'Date','Time','HomeTeam','AwayTeam','FTHG','FTAG','HS','AS','HST','AST','B365H','B365D','B365A','B365>2.5','B365<2.5'})),
                    canonical_completed_matches=sum(r['league']==league and r['season']==season for r in canonical))
                # Save the original source snapshot separately; no unverified join by team spelling.
                (dest/f'{season}.{league}.csv').write_bytes(raw)
                total+=len(rows)
            except Exception as exc:item.update(status='unavailable',reason=str(exc)[:150])
            report.append(item)
            print(json.dumps(item),flush=True)
    summary={'source':'football-data.co.uk','mode':'supplementary_research_only',
       'downloaded_league_seasons':sum(r['status']=='available' for r in report),
       'completed_external_rows':total,'canonical_matches':len(canonical),
       'note':'Do not merge by row order or use post-match statistics as prematch features.',
       'coverage':report}
    (dest/'manifest.json').write_text(json.dumps(summary,indent=2))
    print('EXTERNAL SOURCE AUDIT',json.dumps({k:v for k,v in summary.items() if k!='coverage'}),flush=True)
    if not summary['downloaded_league_seasons']:raise SystemExit('No external football source downloaded')
if __name__=='__main__':main()
