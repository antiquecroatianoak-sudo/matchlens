# Povijesni pilot

Samostalna Python 3 analitika, bez vanjskih paketa. Iz korijena:

    python analytics/import_upstream.py
    python -m unittest discover -s tests -p 'test_backtest.py' -v
    python analytics/backtest.py
    python analytics/summarize.py

Izvorni snapshotovi i porijeklo su u data/openfootball i data/upstream; izvještaj i nepromijenjene prognoze u data/reports. GitHub preslika sadrži odabrani projektni kod i manifest, bez platformskog hosting paketa. Skupove preuzimati s adresa u manifestu, koristiti cache i hash; dopune trebaju izvorne TXT datoteke prema analytics/import_upstream.py.

Rezultati su retrospektivni pilot. Ne koristiti kao potvrđene prognoze uživo. Ne mijenjati parametre prema završnom testu. Nedostajući rezultati ostaju nedostajući, nikada 0:0. Četiri plus dva testova provjeravaju vremensku izolaciju, konzistentne vjerojatnosti, neovisnost kalibracije od test-ishoda i uvoz eksplicitnog 0:0 naspram odgođene utakmice.

## Prošireno podešavanje (offline)

Dodatne ovisnosti su u `analytics/requirements.txt`. Instalirati ih u odvojeno Python okruženje. Iz korijena projekta:

    python -m pip install -r analytics/requirements.txt
    python -m unittest discover -s tests -p 'test*py' -v
    python -m analytics.expanded_search --output data/experiments/novi-ciklus

Završeni izlaz se ne prepisuje: svaki ciklus ima svoju mapu. Arhivirani prvi prošireni ciklus: `data/experiments/20261028-expanded-v1/`. Izvorni pilot ostaje u `data/reports/`. Algoritam zapisuje svaku od 1.701 konfiguracije, zaključani odabir prije audita, pokazatelje, koeficijente, važnost skupina, vremenske granice te pojedinačne prognoze. `app/expanded-summary.json` je kompaktan prikaz zadnjeg ciklusa, ne spremnik neovisnih dokaza.

Razvojni prozori su 2022/23 i 2023/24, uz treniranje samo na ranijim sezonama. Naknadno pregledane 2024/25 i 2025/26 su opisna ponovna analiza. Objavljivanje novih stvarnih preporuka nije uključeno. Uspoređeni osnovni regresijski model također se odabire isključivo u razvojnim prozorima; usporedba se radi na istim utakmicama.

GitHub izdanje treba kanonske JSON snapshotove na putanjama iz izvornog manifesta; ne preuzimati bez provjere hashova i istih upstream dopuna. Sam izvorni manifest nije zamjena za cijeli podatkovni skup. Izvorni platformski runtime nije dio prijenosa analitike.

## Snapshotovi i prospektivni test

`data/openfootball/` i `data/upstream/` sadrže CC0 snapshotove korištene u expanded-v1. Provjera prema manifestu:

    python analytics/verify_snapshots.py                 # provjera spremljenih datoteka
    python analytics/verify_snapshots.py --rebuild DIR   # svježi download u praznu mapu i usporedba

Prospektivni test (`analytics/prospective.py`, svi zapisi samo se dodaju):

    python -m analytics.prospective snapshot
    python -m analytics.prospective predict --experiment data/experiments/20261028-prospective-v1 --snapshot data/prospective/snapshots/<STAMP> --as-of YYYY-MM-DD
    python -m analytics.prospective score   --experiment data/experiments/20261028-prospective-v1 --snapshot data/prospective/snapshots/<STAMP>

`lock` se pokreće samo jednom po eksperimentu. Promjena modela ili pravila zahtijeva novu mapu. Nakon svakog `predict` objaviti `log_sha256` u issueu radi vremenskog žiga.
