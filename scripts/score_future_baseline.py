"""Generate honest prematch probabilities using the existing historical Poisson baseline.

Research fallback while full factor-model prospective inference is not implemented.
"""
import json
from collections import defaultdict,Counter
import re
import unicodedata
from datetime import date,timedelta
from pathlib import Path
from analytics.backtest import load_matches,predict

# Provider competition IDs are not historical model league IDs.
LEAGUE_MAP={'bl1':'de.1'}  # bl2 is deliberately unsupported by this model.

OPENLIGA_TEAMS={
    "fc bayern münchen":"Bayern München",
    "bayer 04 leverkusen":"Bayer Leverkusen",
    "borussia dortmund":"Borussia Dortmund",
    "rb leipzig":"RB Leipzig",
    "vfb stuttgart":"VfB Stuttgart",
    "eintracht frankfurt":"Eintracht Frankfurt",
    "sc freiburg":"SC Freiburg",
    "tsg 1899 hoffenheim":"Hoffenheim",
    "tsg hoffenheim":"Hoffenheim",
    "vfl wolfsburg":"Wolfsburg",
    "1. fc union berlin":"Union Berlin",
    "1. fsv mainz 05":"Mainz 05",
    "borussia mönchengladbach":"Borussia Mönchengladbach",
    "fc augsburg":"FC Augsburg",
    "sv werder bremen":"Werder Bremen",
    "1. fc heidenheim 1846":"Heidenheim",
    "fc st. pauli":"St. Pauli",
    "1. fc köln":"1. FC Köln",
    "hamburger sv":"Hamburger SV",
}

def normalize_team(name,known):
    if name in known:return name
    alias=OPENLIGA_TEAMS.get(name.casefold(),name)
    if alias in known:return alias
    def key(s):
        s=unicodedata.normalize("NFKD",s.casefold())
        return re.sub(r"[^a-z0-9]","", "".join(ch for ch in s if not unicodedata.combining(ch)))
    matches=[t for t in known if key(t)==key(alias)]
    if len(matches)==1:
        return matches[0]
    if matches:
        return None
    # Match generic club prefixes only if the result is unambiguous.
    generic={"fc","sc","sv","vfl","vfb","tsg","fk","cf","ac","as","club"}
    def club_tokens(s):
        normalized=unicodedata.normalize("NFKD",s.casefold())
        normalized="".join(ch for ch in normalized if not unicodedata.combining(ch))
        return tuple(t for t in re.findall(r"[a-z0-9]+",normalized) if t not in generic)
    target=club_tokens(alias)
    matches=[t for t in known if target and club_tokens(t)==target]
    return matches[0] if len(matches)==1 else None

def last_two_completed_seasons(match_date):
    """Use only the last two fully completed July-June seasons before kickoff."""
    last_start = match_date.year - 1 if match_date.month >= 7 else match_date.year - 2
    return {f'{y}-{str((y + 1) % 100).zfill(2)}' for y in (last_start - 1, last_start)}

def main():
    fixture_file=Path('out/future-fixtures.json')
    payload=json.loads(fixture_file.read_text())
    history,_=load_matches('data/openfootball')
    by_league=defaultdict(list)
    for row in history:by_league[row['league']].append(row)
    result=[];skipped=[]
    for f in payload['fixtures']:
        match_date=date.fromisoformat(f['kickoff_utc'][:10])
        cutoff=(match_date-timedelta(days=2)).isoformat()
        historical_league=LEAGUE_MAP.get(f['league'],f['league'])
        if historical_league not in by_league:
            skipped.append({'id':f['id'],'reason':'no corresponding historical league for '+f['league']})
            continue
        eligible_seasons=last_two_completed_seasons(match_date)
        past=[r for r in by_league[historical_league] if r['season'] in eligible_seasons and r['date']<cutoff]
        known={t for r in past for t in (r['home'],r['away'])}
        home=normalize_team(f['home'],known)
        away=normalize_team(f['away'],known)
        match={'date':match_date.isoformat(),'home':home or f['home'],'away':away or f['away']}
        # Team-specific estimates need enough historical matches. For newly
        # promoted or unmatched teams, use an explicitly labelled league-only
        # prior, never fabricated team results or unsupported confidence.
        probs=predict(past,match,{'window':50,'half_life':15,'prior':8}) if home and away else None
        league_prior = probs is None
        if league_prior:
            probs=predict(past,match,None)
        if probs is None:
            skipped.append({'id':f['id'],'reason':'insufficient verified league history'})
            continue
        result.append({**f,'historical_home':home,'historical_away':away,'historical_league':historical_league,'prob':probs,'model':('historical_league_prior_v1' if league_prior else 'historical_poisson_fallback_v1'), 'team_history_covered':not league_prior,
                       'history_cutoff_exclusive':cutoff})
    out=Path('out/upcoming-probabilities.jsonl')
    out.write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in result))
    Path('out/upcoming-coverage.json').write_text(json.dumps({
        'source_fixtures':len(payload['fixtures']),'scored':len(result),'skipped':skipped,
        'warning':'Poisson fallback, NOT the previously evaluated factor model; no accuracy claim.'},indent=2))
    print('FUTURE PREMATCH SCORED',len(result),'OF',len(payload['fixtures']))
if __name__=='__main__':main()
