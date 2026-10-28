"""Rebuild OpenFootball snapshots from the source manifest and compare SHA-256.

Snapshots were stored as canonical JSON (indent=2, trailing newline); transformed
files additionally merge the upstream TXT results via analytics/import_upstream.py.
Upstream repositories change over time, so a mismatch is reported, never hidden.
Default mode only verifies the committed files; --rebuild DIR downloads into DIR.
"""
import argparse, hashlib, json, os, shutil, sys, urllib.error, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def raw_url(url):
    return url.replace('https://github.com/', 'https://raw.githubusercontent.com/').replace('/blob/', '/')


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def verify(folder, manifest):
    rows = []
    for f in manifest['source_files']:
        path = Path(folder) / f['file']
        actual = sha(path) if path.exists() else None
        rows.append(dict(file=f['file'], expected=f['sha256'], actual=actual, match=actual == f['sha256'], transformed=f['transformed']))
    return rows


def rebuild(target, manifest):
    target = Path(target)
    (target / 'data/openfootball').mkdir(parents=True, exist_ok=True)
    for f in manifest['source_files']:
        try:
            data = json.loads(urllib.request.urlopen(raw_url(f['url'])).read())
        except urllib.error.HTTPError as e:
            if e.code != 404 or not f['transformed']:
                raise
            continue  # import_upstream starts an empty file when the JSON base does not exist
        (target / 'data/openfootball' / f['file']).write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')
    for f in manifest['source_files']:
        if f['supplemental_source']:
            rel = raw_url(f['supplemental_source']).split('/openfootball/', 1)[1].replace('/master/', '/', 1)
            dest = target / 'data/upstream' / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(urllib.request.urlopen(raw_url(f['supplemental_source'])).read())
    cwd = os.getcwd()
    try:
        os.chdir(target)
        sys.path.insert(0, str(ROOT))
        from analytics.import_upstream import run
        run()
    finally:
        os.chdir(cwd)
    return target / 'data/openfootball'


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--manifest', default=str(ROOT / 'data/source-manifest.json'))
    p.add_argument('--data', default=str(ROOT / 'data/openfootball'))
    p.add_argument('--rebuild', help='empty directory for a fresh download and comparison')
    p.add_argument('--strict', action='store_true', help='exit 1 on any mismatch')
    a = p.parse_args()
    manifest = json.loads(Path(a.manifest).read_text())
    folder = rebuild(a.rebuild, manifest) if a.rebuild else a.data
    rows = verify(folder, manifest)
    bad = [r for r in rows if not r['match']]
    print(json.dumps(dict(files=len(rows), matching=len(rows) - len(bad), mismatched=[(r['file'], r['actual']) for r in bad]), ensure_ascii=False, indent=1))
    if a.strict and bad:
        sys.exit(1)


if __name__ == '__main__':
    main()
