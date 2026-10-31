"""Strictly validate archived factor-search selection before prospective inference."""
import json
from pathlib import Path
from analytics.factor_search import GROUPS

class ModelLockError(ValueError):
    pass

def read_factor_lock(path):
    data=json.loads(Path(path).read_text())
    if data.get('protocol') != 'factor-search-v1' or data.get('features') != 84:
        raise ModelLockError('Unexpected factor-model lock')
    chosen=data.get('chosen',{})
    temperatures=data.get('temperatures',{})
    selected={}
    for family in ('outcome','goals'):
        entry=chosen.get(family)
        if not isinstance(entry,dict) or not isinstance(entry.get('config'),dict):
            raise ModelLockError('Missing locked selection: '+family)
        cfg=entry['config']
        if cfg.get('group') not in GROUPS or cfg.get('leaves') not in (5,7,11,15,23) or cfg.get('l2') not in (1.,2.,5.,10.,20.):
            raise ModelLockError('Invalid locked configuration: '+family)
        temp=temperatures.get(family)
        if temp not in (.75,.85,1.,1.15,1.3,1.5):
            raise ModelLockError('Missing calibrated temperature: '+family)
        selected[family]={'config':cfg,'columns':GROUPS[cfg['group']],'temperature':temp}
    return selected
