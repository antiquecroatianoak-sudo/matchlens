"""Import the observed OpenFootball v-style Football.TXT subset, failing on unknown played-game syntax."""
import json,re
from datetime import date
from pathlib import Path
MONTHS={m:i+1 for i,m in enumerate(['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'])}
SOURCES=[('belgium','2023-24/be1.txt','2023-24','be.1'),('belgium','2025-26/be1.txt','2025-26','be.1'),('europe','turkey/2023-24_tr1.txt','2023-24','tr.1'),('europe','turkey/2025-26_tr1.txt','2025-26','tr.1'),('europe','greece/2023-24_gr1.txt','2023-24','gr.1'),('europe','greece/2025-26_gr1.txt','2025-26','gr.1')]
def parse(text,season):
 rows=[];current=None;round_='';year=int(season[:4]);seen=set()
 for line in text.splitlines():
  if line.startswith('▪'):round_=line[1:].strip();continue
  day=re.match(r'^\s*(?:Mon|Tue|Wed|Thu|Fri|Sat|Sun)\s+([A-Za-z]{3})\s+(\d{1,2})(?:\s+(\d{4}))?\s*$',line)
  if day:
   mon=MONTHS[day[1]];y=int(day[3]) if day[3] else year+(mon<7);current=date(y,mon,int(day[2])).isoformat();continue
  game=re.match(r'^\s*(?:(\d{1,2}:\d{2})\s+)?(.+?)\s+v\s+(.+?)\s+(\d+)-(\d+)(?:\s|$)',line)
  if game:
   if current is None:raise ValueError('Missing date before game')
   row=dict(round=round_,date=current,team1=game[2].strip(),team2=game[3].strip(),score={'ft':[int(game[4]),int(game[5])]})
   if game[1]:row['time']=game[1]
   key=(current,row['team1'],row['team2'])
   if key in seen:raise ValueError('Duplicate upstream match')
   seen.add(key);rows.append(row)
  elif re.search(r'\sv\s.*\d+-\d+',line):raise ValueError('Unsupported score syntax: '+line)
 return rows

def run():
 audit=[]
 for repo,path,season,league in SOURCES:
  raw=Path('data/upstream')/repo/path;parsed=parse(raw.read_text(),season);dest=Path('data/openfootball')/(season+'-'+league+'.json')
  old=json.loads(dest.read_text()) if dest.exists() else {'name':league+' '+season,'matches':[]}
  def key(m):return (m['date'],m['team1'],m['team2'])
  lookup={key(m):m for m in old['matches']};added=0
  for m in parsed:
   previous=lookup.get(key(m));score=previous.get('score') if previous else None;old_ft=score.get('ft') if isinstance(score,dict) else score
   if old_ft and old_ft!=m['score']['ft']:raise ValueError('Conflicting result '+str(key(m)))
   if not old_ft:added+=1;lookup[key(m)]=m
  old['matches']=list(lookup.values());old['supplemental_source']=f'https://github.com/openfootball/{repo}/blob/master/{path}';dest.write_text(json.dumps(old,ensure_ascii=False,indent=2)+'\n')
  audit.append(dict(source=old['supplemental_source'],parsed=len(parsed),new_results=added,season=season,league=league))
 Path('data/upstream/audit.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2)+'\n');print(json.dumps(audit))
if __name__=='__main__':run()
