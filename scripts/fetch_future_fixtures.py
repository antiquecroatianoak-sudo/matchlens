"""Fetch upcoming OpenFootball fixtures, without fabricating model probabilities."""
import json,urllib.request
from datetime import datetime,timezone,timedelta
from pathlib import Path

LEAGUES=("en.1","it.1","es.1","de.1","fr.1","pt.1","be.1","nl.1","tr.1","gr.1")
BASE="https://raw.githubusercontent.com/openfootball/football.json/master"
def fetch(now=None,days=14):
    now=now or datetime.now(timezone.utc)
    years=range(now.year-1,now.year+2)
    fixtures=[];errors=[]
    for year in years:
        season=f"{year}-{(year+1)%100:02d}"
        for league in LEAGUES:
            url=f"{BASE}/{season}/{league}.json"
            try:
                with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'MatchLens/1.0'}),timeout=12) as response:
                    data=json.load(response)
            except Exception as e:
                errors.append({'league':league,'season':season,'error':str(e)[:100]})
                continue
            for m in data.get('matches',[]):
                date=m.get('date')
                if not date:continue
                try:
                    kickoff=datetime.fromisoformat(date.replace('Z','+00:00'))
                    if kickoff.tzinfo is None:kickoff=kickoff.replace(tzinfo=timezone.utc)
                except ValueError:continue
                if not now<kickoff<=now+timedelta(days=days):continue
                home=m.get('team1') or m.get('home')
                away=m.get('team2') or m.get('away')
                if not isinstance(home,str) or not isinstance(away,str):continue
                if m.get('score') is not None or m.get('ft') is not None:continue
                fixtures.append({'id':f"{season}:{league}:{date}:{home}:{away}",
                                 'league':league,'season':season,'round':str(m.get('round','unknown')),
                                 'kickoff_utc':kickoff.isoformat(),'home':home,'away':away,
                                 'source':url})
    return {'fetched_at_utc':now.isoformat(),'fixtures':fixtures,'source_errors':errors,
            'probabilities_available':False,
            'status':'fixtures_only_no_predictions_until_prematch_model_feed'}

def main():
    result=fetch()
    out=Path('out/future-fixtures.json')
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n')
    print('UPCOMING FIXTURES',len(result['fixtures']),'SOURCE ERRORS',len(result['source_errors']))
    print('NO PREDICTIONS: model probability feed not connected')
if __name__=='__main__':main()
