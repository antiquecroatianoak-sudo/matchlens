# Vanjski faktori — operativna odluka 30.10.2026.

Ovaj PR dodaje **provjeru, karantenski JSONL adapter i mjerenje pokrivenosti**, ali još ne uključuje vanjske podatke u trenirani ili produkcijski model.

## Redoslijed dopuštenih pilota

1. **OpenFootball (CC0):** postojeća baza rezultata; zadržati kao kontrolni model i spriječiti dvostruki uvoz.
2. **Hudl StatsBomb Open Data:** istraživački pilot događaja, xG i sastava, uz atribuciju i provjeru prava za namjeravanu upotrebu. Potvrđeni uzorak Bundeslige 2023/24 ima samo 34 utakmice. Za predviđanje susreta N smiju se koristiti samo događaji iz **ranijih** susreta; sastav ili xG susreta N nije ulaz za predviđanje N.
3. **Open-Meteo arhivirane prognoze:** kandidat za vrijeme samo ako su stadion, vrijeme početka i točan run izdavanja potvrđeni prije predviđanja.
4. **Treneri i ozljede:** prvo pribaviti dopuštene, datirane objave s pouzdanim identitetima i dokazom dostupnosti prije predviđanja. Bez toga ih ne uključivati.

**Ne uključivati automatski** Transfermarkt ili Football-Data.co.uk u treniranje: postoje dokumentirana ograničenja uvjeta uporabe u `docs/PROVJERA_STVARNIH_IZVORA_2026-10-30.md`. Imenovanje izvora nije licenca.

## Obvezan dokaz prije aktivacije

- Izričito odobren izvor u `approved_sources`, izvorni identifikator, identitet utakmice i provjerena licenca.
- `observed_at <= available_at < prediction_at`, svi s vremenskom zonom; nikad naknadno poznat ishod.
- Kanonsko uparivanje utakmica, izvještaj o duplikatima, nedostajućim vrijednostima i pokrivenosti svih kandidata, uključujući utakmice bez zapisa.
- Ablacija na istim susretima: osnovni model nasuprot modelu s faktorom; izbor parametara samo na ranijem razdoblju.
- Odabir 25 % prema unaprijed zadanom pravilu, jedan odabrani market po utakmici gdje je to dogovoreno; prijaviti broj kandidata, odabranih i pogodaka, kalibraciju i razliku prema osnovi.
- Završna validacija na zaista novom razdoblju; već analizirane 2024/25 i 2025/26 nisu novi neovisni dokaz.
- **Bez automatizirane promocije** novog faktora dok se ne potvrdi poboljšanje i prava na uporabu.

## Primjer ulaznog JSONL zapisa (ilustracija, nije stvarno preuzet podatak)

```json
{"match_id":"canonical-id","factor":"prior_matches_rolling_xg","value":1.4,"source":"approved-provider","observed_at":"2026-10-20T20:00:00Z","available_at":"2026-10-21T09:00:00Z","prediction_at":"2026-10-24T12:00:00Z"}
```

`analytics.factor_snapshot_import.read_factor_jsonl` i `analytics.factor_coverage.coverage_report` rade isključivo s već pribavljenim lokalnim datotekama i ne preuzimaju podatke niti tvrde da je primjer stvaran. Sljedeći implementacijski zadatak: licencirani izvorni adapter s uparivanjem ID-jeva i povijesnim snapshotovima, zatim ablacija.
