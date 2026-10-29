"""Shared active historical model and comparable replacement decision.

The registry controls actual offline inference. Activation is not a claim of
independently validated live recommendations or an unattended training service.
"""
import argparse
import json
from pathlib import Path
import numpy as np
from analytics.expanded_search import features,actual_array,metrics,stripped
from analytics.market_specialists import chronological_predictions,combine
from analytics.filter_audit import all_fixtures

REGISTRY=Path(__file__).resolve().parents[1]/'app/active-strategy.json'


def load_active(path=REGISTRY):
    strategy=json.loads(Path(path).read_text())
    if strategy['status']!='active_research':
        raise ValueError('No active research model')
    lock=json.loads((REGISTRY.parents[1]/strategy['source_lock']).read_text())
    if strategy['seed_configs']!=lock['seed_configs'] or strategy['policies']!={f:v['policy'] for f,v in lock['chosen'].items()}:
        raise ValueError('Active registry differs from its archived model lock')
    return strategy


def predict_active(rows,season,strategy=None):
    strategy=load_active() if strategy is None else strategy
    families={};cache={};ids=None;targets=None;traces={}
    for family,cfg in strategy['seed_configs'].items():
        key=(cfg['window'],cfg['half_life'])
        if key not in cache:cache[key]=features(rows,*key)
        p,rec,trace=chronological_predictions(cache[key],season,cfg,strategy['policies'][family])
        current=[r['match']['id'] for r in rec]
        if ids is not None and ids!=current:raise ValueError('Different active model fixture pools')
        ids=current;targets=rec;families[family]=p;traces[family]=trace
    return targets,combine(families['outcome'],families['goals']),traces


def replacement_decision(champion,challenger,evidence):
    """No replacement for a tiny or easier sample, or already-used audit."""
    if evidence.get('kind')!='unused_chronological_validation' or evidence.get('used_for_tuning',True):
        return dict(replace=False,reason='requires_unused_validation')
    if evidence.get('season') in champion['previously_viewed_audit_seasons']:
        return dict(replace=False,reason='previously_viewed_audit')
    if evidence.get('coverage_policy')!=champion['coverage_policy']:
        return dict(replace=False,reason='different_coverage_policy')
    current=evidence.get('champion',[]);candidate=evidence.get('challenger',[])
    def keyed(rows):
        ids=[r['id'] for r in rows]
        if len(ids)!=len(set(ids)):raise ValueError('Duplicate validation fixture')
        if any(type(r['hit']) is not bool for r in rows):raise ValueError('Expected scored boolean hits')
        return {r['id']:r['hit'] for r in rows}
    left,right=keyed(current),keyed(candidate)
    if set(left)!=set(right):return dict(replace=False,reason='different_fixtures')
    if len(left)<champion['replacement_policy']['minimum_distinct_fixtures']:
        return dict(replace=False,reason='insufficient_sample')
    difference=sum(right.values())-sum(left.values())
    return dict(replace=difference>0,reason='higher_validation_accuracy' if difference>0 else 'not_more_accurate',
                current_id=champion['id'],candidate_id=challenger['id'],matches=len(left),
                additional_hits=difference,champion_accuracy=sum(left.values())/len(left),
                challenger_accuracy=sum(right.values())/len(right))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--data',default='data/openfootball');p.add_argument('--season',required=True)
    args=p.parse_args();strategy=load_active();rows,_=all_fixtures(args.data)
    records,prob,trace=predict_active(rows,args.season,strategy)
    known=np.array([not r['match'].get('pending') for r in records]);scored=[r for r in records if not r['match'].get('pending')]
    print(json.dumps(dict(active_strategy=strategy['id'],eligible_fixtures=len(records),
                         unscored=int((~known).sum()),historical=stripped(metrics(prob[known],actual_array(scored))),
                         live_recommendations_enabled=strategy['live_recommendations_enabled'],trace=trace),indent=2))
