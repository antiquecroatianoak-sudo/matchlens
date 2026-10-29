"""Make the UI-sized projection; the complete research archive stays intact."""
import argparse
import json
from pathlib import Path

FIELDS=('protocol','calibration_candidates','audit_gates','eligible_fixtures',
        'unscored_fixtures','reference','candidate','selected_gate_audit',
        'independent_90_confirmed','promoted','limitations')


def summarize(source, destination):
    report=json.loads(Path(source).read_text())
    Path(destination).write_text(json.dumps({k:report[k] for k in FIELDS},indent=2)+'\n')


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('source');p.add_argument('destination')
    a=p.parse_args();summarize(a.source,a.destination)
