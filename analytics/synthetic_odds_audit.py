"""Real-price arithmetic/coverage benchmark. NOT MatchLens predictive accuracy.

No round IDs, no captured-at timestamps, no matching 2024-26 cohort. It cannot
evaluate the active 25%-before-round strategy. Missing results remain unknown.
"""
import argparse,csv,hashlib,json
from pathlib import Path
from analytics.synthetic_odds import terms
from analytics.filter_audit import all_fixtures,summary

SCOPE={('England','Premier League'):'en.1',('Italy','Serie A'):'it.1',('Spain','La Liga'):'es.1',
       ('Germany','Bundesliga'):'de.1',('France','Ligue 1'):'fr.1',('Portugal','Primeira Liga'):'pt.1',
       ('Belgium','Jupiler Pro League'):'be.1',('Netherlands','Eredivisie'):'nl.1',
       ('Turkey','Süper Lig'):'tr.1',('Greece','Greek Super League'):'gr.1'}


def build(rows):
    offers=[];valid_matches=0;seen=set();invalid=0
    for r in rows:
        key=(r['country'],r['league'])
        if key not in SCOPE:continue
        if r['id'] in seen:raise ValueError('Duplicate source match row')
        seen.add(r['id']);prices={}
        try:
            for label,field in [('1','home'),('X','draw'),('2','away')]:prices[label]=float(r['pin_open_'+field])
            for selection in ('1X','X2'):terms(selection,prices)
        except (ValueError,TypeError):invalid+=1;continue
        valid_matches+=1
        for selection in ('1X','X2'):
            t=terms(selection,prices)
            if t['odds']<2:continue
            actual=None if r['void_reason'] or r['result'] not in ('1','X','2') else int(r['result'] in selection)
            offers.append(dict(id='tipsaudit:'+r['id']+'|'+selection,match_id='tipsaudit:'+r['id'],
                date=r['kickoff_utc'][:10],market=selection,league=SCOPE[key],prob=0.,odds=t['odds'],
                actual=actual,odds_basis='synthetic_1x2',availability_before_round=None))
    return offers,valid_matches,invalid,len(seen)


def run(raw,output,ui):
    out=Path(output);out.mkdir(parents=True,exist_ok=False)
    rows=list(csv.DictReader(Path(raw).open()));pool,valid,invalid,scope_rows=build(rows)
    past,_=all_fixtures('data/openfootball');dates={r['date'] for r in past if r['season'] in ('2024-25','2025-26')}
    # Dates do not overlap: no fuzzy team join or invented old prices.
    overlapping_dates=sum(r['kickoff_utc'][:10] in dates for r in rows if (r['country'],r['league']) in SCOPE)
    protocol=dict(name='synthetic-odds-coverage-v1',scope='Existing ten top leagues only',
                  assumption='Synthetic odds treated as exact test payoff; same-book prices; zero fees.',
                  formula='1 / (1/a + 1/b)',minimum_odds=2.,
                  source_sha256=hashlib.sha256(Path(raw).read_bytes()).hexdigest(),
                  code_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                  benchmark='Every qualifying 1X/X2 offer; NO MatchLens selection, NO 25% round policy.',
                  model_accuracy=None,quarter_policy_accuracy=None)
    (out/'lock.json').write_text(json.dumps(protocol,indent=2)+'\n')
    def describe(selected):
        known=[r for r in selected if r['actual'] is not None]
        return dict(selected=len(selected),scored=len(known),unscored=len(selected)-len(known),
                    hits=sum(r['actual'] for r in known),misses=sum(1-r['actual'] for r in known),
                    hit_rate=sum(r['actual'] for r in known)/len(known) if known else None)
    report=dict(protocol=protocol,source_rows=len(rows),scope_rows=scope_rows,valid_price_matches=valid,invalid_price_matches=invalid,
                date_min=min(r['kickoff_utc'][:10] for r in rows),date_max=max(r['kickoff_utc'][:10] for r in rows),
                overlapping_dates_with_existing_audit=overlapping_dates,
                price_filter_benchmark=describe(pool),by_selection={s:describe([r for r in pool if r['market']==s]) for s in ('1X','X2')},
                model_accuracy_status='Not measurable from this file: no MatchLens forecast join or verified pre-round price times.',
                promoted=False,limitations=['Different 2026 source-selected population; not the old 2024/26 audit.',
                    'CSV has no round IDs or quote-availability timestamps; some prices entered after match according to source.',
                    'Raw qualifying-offer hit rate is not the app algorithm hit rate or a 25% strategy.',
                    'No closing prices, best-soft cross-book prices or foreign model probabilities used.'])
    (out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    (out/'offers.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in pool));Path(ui).write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))
    return report


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--raw',default='data/odds/tipsaudit-predictions-all.csv');p.add_argument('--output',required=True);p.add_argument('--ui',default='app/synthetic-odds-summary.json');a=p.parse_args();run(a.raw,a.output,a.ui)
