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

## Dnevni filtri i novi razvojni ciklus

    python -m analytics.filter_audit --output data/experiments/novi-dnevni-filtri
    OPENBLAS_NUM_THREADS=1 python -m analytics.direct_model --output data/experiments/novi-izravni-model

Obje skripte odbijaju prepisati završen eksperiment. Dnevni filtri uključuju neocijenjene ponude u poredak, arhiviraju cijeli skup ponuda i izvještaj, te ne optimiziraju prag prema najvišem audit postotku. direct-v1 ima 12 konfiguracija, odvojeno učenje/tuning 2022/23 i kalibraciju 2023/24, pa opisni audit na već viđenim sezonama. Lošiji kandidati i temperature ostaju sačuvani. Ne mijenjaju ranije zaključani model niti predstavljaju novi neovisni dokaz.


## Zasebno učenje po tržištu — 29.10.2026.

    OPENBLAS_NUM_THREADS=1 python -m analytics.market_specialists --output data/experiments/novi-market-specialists --ui app/specialists-summary.json

Novi izlaz mora biti nepostojeća mapa. Uspoređuje 12 kandidata kalendarske težine primjera i sezonskog/tromjesečnog refita. Izbor 1X2 i golova je zaseban, samo prema razvoju; zaključavanje se zapisuje prije opisnog audita. Nisu dodani vanjski faktori. U javnoj arhivi prognoze mogu biti pohranjene kao specialists-predictions.jsonl.gz (gzip bez vremenske oznake); skripta izvorno piše JSONL.

Prospektivna provjera sada odbija promijenjeni hash koda i as_of različit od stvarnog UTC datuma. Pri ocjenjivanju generated_at mora prethoditi i izvornom i stvarnom datumu utakmice; bez potvrđene vremenske zone početka koristi se konzervativni datum. Nevaljani zapisi isključeni su s razlogom, ne izbrisani. Stari lockovi ostaju nepromijenjeni i za novo generiranje trebaju novi eksperiment.


## Novi faktori i nelinearne ablacije

    python -m pip install -r analytics/requirements-research.txt
    OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 python -m analytics.factor_search --output data/experiments/novi-factor-search --ui app/factor-summary.json

Skripta zahtijeva novu izlaznu mapu. Koristi scikit-learn 1.8.0, isključuje slučajnu validacijsku podjelu/early stopping, podešava 2022/23 i kalibrira zasebno 2023/24. Svih 14 kandidata i temperature arhiviraju se. Pohranjeni hash koda i izvora, lock prije audita i pojedinačne prognoze. Javni arhiv može sadržavati gzip JSONL prognoza. Slabiji novi kandidat se ne promovira.

## Povijest osoba i filtri novijeg modela

`person_matchups.py` priprema kandidatna obilježja trenera i igrača kroz promjene klubova iz provjerenih JSONL činjenica. Podatkovni ugovor i status su u `docs/POVIJEST_TRENERA_I_IGRACA.md`. Ne preuzima podatke, ne spaja osobe po imenu i ne pretvara nedostatak podataka u modelski bonus. Trenutačni nogometni skup nema stvarne osobne zapise; novi testovi su sintetičke provjere koda.

    python -m analytics.specialist_filter_audit --output data/experiments/NOVI_CIKLUS

Zadana pravila filtara primjenjuju se na ranije odabrani market-specialists-v1. Novu mapu ne prepisuje; puni skup uključuje i ponude bez poznatog ishoda. Kompaktan UI omogućuje poštenu usporedbu s ranijim Poisson + Elo izračunom. Nema novih kvota ni preporuka.
