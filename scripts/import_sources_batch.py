"""One-command multi-source ingestion audit. Research datasets remain quarantined."""
import concurrent.futures,json,subprocess,sys,urllib.request
from pathlib import Path

CATALOGS={
 'statsbomb-open-data':'https://raw.githubusercontent.com/statsbomb/open-data/master/data/competitions.json',
 'openfootball-europe':'https://raw.githubusercontent.com/openfootball/europe/master/README.md',
}
def catalog(name,url):
    result={'source':name,'url':url,'mode':'metadata_only'}
    try:
        req=urllib.request.Request(url,headers={'User-Agent':'MatchLensResearch/1.0'})
        with urllib.request.urlopen(req,timeout=20) as response:raw=response.read(3_000_000)
        if name=='statsbomb-open-data':
            entries=json.loads(raw)
            if not isinstance(entries,list):raise ValueError('Unexpected competitions catalog')
            result.update(status='available',entries=len(entries),competitions=sorted({str(x.get('competition_name')) for x in entries})[:100])
        else:result.update(status='available',bytes=len(raw))
    except Exception as exc:result.update(status='unavailable',reason=str(exc)[:180])
    return result

def main():
    out=Path('out/external-source-audit');out.mkdir(parents=True,exist_ok=True)
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        jobs={pool.submit(catalog,name,url):name for name,url in CATALOGS.items()}
        jobs[pool.submit(lambda:subprocess.run([sys.executable,'-m','scripts.import_football_data_research'],capture_output=True,text=True,timeout=1500))]='football-data.co.uk'
        results=[]
        for future in concurrent.futures.as_completed(jobs):
            name=jobs[future]
            try:
                response=future.result()
                if name=='football-data.co.uk':
                    manifest=out/'manifest.json'
                    response={'source':name,'status':'available' if response.returncode==0 else 'failed',
                              'returncode':response.returncode,
                              'summary':json.loads(manifest.read_text()) if manifest.exists() else None,
                              'stderr_tail':response.stderr[-1200:]}
                    if response['summary']:response['summary'].pop('coverage',None)
                results.append(response)
            except Exception as exc:results.append({'source':name,'status':'failed','reason':str(exc)[:200]})
    results.append({'source':'openfootball/football.json','status':'existing_canonical',
                    'note':'Restored in prior workflow step; not downloaded twice'})
    results.append({'source':'soccerdata','status':'adapter_only',
                    'note':'Library is not a standalone licensed dataset; provider access requires individual approval'})
    summary={'mode':'batch_ingestion_research_only','sources':sorted(results,key=lambda r:r['source']),
             'warning':'Only canonical OpenFootball data currently enter model training. Other feeds are quarantined pending licensed, leakage-safe fixture reconciliation.'}
    (out/'batch-sources.json').write_text(json.dumps(summary,indent=2))
    print('BATCH SOURCES',json.dumps(summary),flush=True)
    if not any(r['status']=='available' for r in results):raise SystemExit('No supplemental source available')
if __name__=='__main__':main()
