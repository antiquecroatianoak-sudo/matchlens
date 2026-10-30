# MatchLens — trajna evidencija parametara
Ažurirano: 2026-10-30. Izvor istine za napredak: ovaj dokument u GitHubu. Status 'kod pripremljen' NE znači da parametar utječe na trenirane prognoze.

| Parametar | Status | Izvor / nedostatak | Sljedeći korak |
|---|---|---|---|
| Napad, obrana, domaći/gosti, Elo, snaga protivnika | U povijesnom modelu | Rezultati OpenFootball | Kontrolna usporedba |
| Forma, golovi, remiji, trendovi, H2H | U povijesnom modelu | Rezultati OpenFootball | Ablacije i kalibracija |
| Odmor, putovanja, kupovi i Europa | Djelomično | Samo razmak ligaških susreta | Uvoz cjelovitog rasporeda |
| Treneri kroz klubove | Kod pripremljen, bez ulaza u trenirani model | Nedostaju vremenski označeni zapisi | Uvoz i ablacijski test |
| Igrači, uloge i izravni dueli | Kod pripremljen, bez ulaza u trenirani model | Nedostaju dokazani događaji | Uvoz i ablacijski test |
| Postave, ozljede, suspenzije, zamjene | Adapter potvrđenih postava dodan; ostalo čeka podatke | Povijesne datirane objave i kanonski ID-jevi | Provjeriti izvore i uvoz, potom testirati model |
| Formacije, presing, tranzicija, prekidi, xG | Čeka podatke | Licencirani događajni/taktički izvori | Provjera pokrivenosti |
| Vremenska prognoza prije susreta | Ugovor obilježja dodan; bez uvoza | Arhivirane prognoze s vremenom izdavanja | Priključiti provjeren izvor |
| Stanje terena, podloga, dimenzije | Ugovor obilježja dodan; bez uvoza | Datirana izvješća o stanju terena | Priključiti provjeren izvor |
| Motivacija, atmosfera i odnosi | Čeka podatke | Provjerene neovisne datirane objave | Procjena kvalitete |
| Povijesne kvote | Čeka podatke | Kvote i vrijeme objave | Uvoz i tržišni benchmark |
| Sudac i disciplina | Odgođeno | Povijesne delegacije i kartoni | Nakon aktivnih tržišta |

## Pravila ažuriranja
- Za svaki novi parametar zabilježiti: naziv, izvor, licencu, vrijeme nastanka, vrijeme dostupnosti, pokrivenost po ligi/sezoni, test i rezultat.
- Nepoznato nije nula; nedostajući ulaz ne smije stvoriti lažnu prognozu.
- Prognoza smije koristiti samo podatke dostupne prije zadanog trenutka prognoziranja.
- Novi model usporediti s baznim na istim utakmicama; Brier, log loss, kalibracija, pogodci, pokrivenost.
- 2024/25 i 2025/26 već su korištene u razvoju i ne mogu se ponovno predstavljati kao neviđeni završni test.
- Svaki završeni eksperiment ima nepromjenjiv ID, postavke i izvještaj; bez prepisivanja prethodnih rezultata.

## Provjera 2026-10-30
- Dodani adapteri za vremenske prognoze, stanje terena i potvrđene postave; samo validacija zapisa, bez stvarnog API uvoza.
- Dodano deset jediničnih testnih slučajeva i GitHub Actions workflow `factor-tests.yml`.
- Za commit `50835761d96f3e920f599627f1d315c4030a8f24` upit za workflow runs vratio je prazan popis; nema potvrde prolaska testova.
- Blokada: provjeriti uvjete korištenja i dobiti stvarne arhivirane podatke s dokazom vremena dostupnosti; bez toga nije moguće pošteno izmjeriti učinak ovih faktora na prognozu.
