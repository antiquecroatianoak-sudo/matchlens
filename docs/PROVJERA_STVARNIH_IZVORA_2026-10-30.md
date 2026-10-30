# Provjera izvora za realne MatchLens testove (30.10.2026.)

## Izvori s različitim statusom

| Izvor | Podaci | Status i granice |
|---|---|---|
| Postojeći OpenFootball | Rezultati i raspored | Primarni postojeći ulaz; provjeriti točnost i datum dostupnosti prije povijesnog testa |
| Hudl StatsBomb Open Data | Događaji, xG, udarci, dodavanja, pritisci | **Djelomični uzorak**: potvrđene 34 utakmice Bundeslige 2023/24; istraživački uvoz, nije puna liga; uvjeti i atribucija |
| Open-Meteo Previous Runs | Povijesno izdane vremenske prognoze | Kandidat za realan vremenski faktor; većina modela od siječnja 2024.; tražiti koordinate stadiona, vrijeme početka i provjeru dostupnosti prognoze prije početka |
| Open-Meteo Single Runs | Pojedinačne prognoze s datumom inicijalizacije | Kandidat; ECMWF od ožujka 2024., ostali modeli od travnja 2026.; uzeti u obzir kašnjenje objave modela |
| Football-Data.co.uk | Rezultati, osnovna statistika, otvarajuće i završne kvote | **BLOKIRANO za automatizirani AI/ML uvoz** bez dopuštenja: stranica izričito ograničava upotrebu na privatne osobe, ne komercijalne ili proizvode za treniranje AI s botovima/scraperima |
| Transfermarkt | Transferi, ozljede, sastavi | **BLOKIRANO** za automatizirani ML uvoz bez dopuštenja, prema prethodno provjerenim uvjetima |
| Wyscout i komercijalni izvori | Napredni podaci o igračima | Čeka prava pristupa / ugovor; nije popunjeno |

## Kontrolni uvjeti prije uključivanja izvora u test

1. Jasna dozvola za konkretan način uporabe.
2. Točan identitet natjecanja, sezone, utakmice, kluba i igrača.
3. Datum objave/dostupnosti prije utakmice; post-match xG koristiti **samo za sljedeće utakmice**.
4. Izvještaj o pokrivenosti, dupliciranju i nedostajućim vrijednostima.
5. Novi faktor uključiti tek nakon vremenski ispravnog ablation testa protiv osnovnog modela.
6. Odvojiti stvarne kvote od modelskih/sintetičkih kvota; bez dopuštenih stvarnih kvota ne tvrditi ROI.
7. Ne popunjavati nepoznate podatke nulom.

Reference:
- https://football-data.co.uk/data
- https://open-meteo.com/en/docs/previous-runs-api
- https://open-meteo.com/en/docs/single-runs-api
- https://github.com/hudl/open-data
