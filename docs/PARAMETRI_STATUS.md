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

## Stvarni povijesni uvoz i prvi kontrolni izračun — 2026-10-30
- Uvezeno 380 EPL rezultata 2023/24 i 380 EPL rezultata 2024/25 iz `openfootball/football.json`, uz izvorne blob SHA vrijednosti u metapodacima i 0 nedostajućih rezultata u ta dva snapshotova.
- Usporedni jednostavni Poissonov kontrolni izračun na 380 utakmica 2024/25 (trening isključivo prethodni rezultati s dvodnevnim odmakom, datum bez potvrđenog vremena početka): 1X2 155/380 = 40,79%, više/manje 2,5 215/380 = 56,58%, Brier 1X2 = 0,65493. Izračun je izveden u JavaScriptu po istoj matematičkoj logici kao Python modul; izvršavanje Python CI još nije potvrđeno.
- OVO NIJE dokaz povećanja točnosti: kontrolni model je jednostavniji od već postojećih MatchLens algoritama, bez vremena/terena/postava; sezona 2024/25 već je ranije pregledana. Potreban neovisni test novih faktora i usporedba na istim utakmicama.

## Odluka korisnika: zajednički test svih faktora i tržišta (2026-10-30)
- Testirati puni skup dostupnih, stvarno povijesnih, prije-utakmice poznatih faktora **zajedno**, a tek nakon toga raditi uklanjanje skupina koje ne poboljšavaju rezultate.
- Tržišta: 1, X, 2, više od 2,5, manje od 2,5, dvostruka šansa 1X i X2 **samo ako stvarna zabilježena kvota prelazi 2,00**.
- Dodan `analytics/full_market_evaluation.py` za zajedničko vrednovanje sedam tržišta s vremenski valjanim kvotama i provjerom potpunosti traženih faktora; testni slučajevi dodani. Nije trenirani model.
- Izvorni OpenFootball rezultati **nemaju povijesne kvote ni većinu traženih faktora**. Puni test trenutačno nema dovoljno verificiranih ulaza; ne imputirati izmišljene kvote, sastave ili vremenske prognoze.
- Mjeriti pogodak, Brier i rezultat po jedinici uloga, uz broj pokrivenih utakmica i usporedbu s prethodnim modelom na identičnom skupu.

## Prikupljanje dodatnih povijesnih rezultata — 2026-10-30
- Preuzeti iz OpenFootball (CC0) i spremljeni snapshotovi 2024/25: Bundesliga 306/306, La Liga 370/380 (10 bez valjanog FT), Serie A 370/380 (10 bez valjanog FT), Ligue 1 306/306. Izvorni SHA svake datoteke u manifestu.
- Novo dodano 1.352 valjana rezultata; ukupno s prethodnih 760 sada 2.112 rezultata. Izostavljenih 20 zapisa nisu tretirani kao 0:0.
- Ovo su **samo rezultati**. Povijesne kvote, izdane vremenske prognoze, potvrđene postave i ostali vanjski faktori nisu dostupni u OpenFootball izvoru; njihovo stvarno prikupljanje ostaje otvoreno, uz provjeru uvjeta uporabe i povijesnog vremena objave.
- Ne prikazivati nove zajedničke rezultate točnosti dok svi traženi ulazi i cijene nisu stvarno dostupni.

## Ispravak zahtjeva — sintetičke kvote 1X i X2 (2026-10-30)
- Korisnik je potvrdio: 1X i X2 su **sintetičke kvote** iz vlastitih vjerojatnosti modela, ne kvote kladionica. 1X = 1/(P1+PX), X2 = 1/(PX+P2); samo strogo > 2,00.
- `full_market_evaluation.py` izračunava te dvije cijene iz prognoze, ne traži povijesni bookmaker quote i ne prikazuje ROI/profit za sintetičke kvote.
- `coverage_audit.py` za stvarne kvote provjerava samo ostalih pet tržišta. Sintetičke kvote ne predstavljaju dokaz tržišne ponude ili zarade.
- Potrebno izvršiti CI i pravi zajednički test na potpunim, prije utakmice dostupnim faktorima.

## Povezivanje svih povijesnih faktora (2026-10-30)
- Dodan `analytics/factor_assembly.py`: zajednički ulaz za sve faktore; za svaki odabire samo zapis s dokazanim `source_id` i `available_at` (te `issued_at` gdje postoji) prije cutoffa. Nedostajuće podatke označava kao nedostajuće, ne izmišlja vrijednosti.
- Dodana tri testa za buduće podatke, odabir zadnjeg dopuštenog zapisa i zabranu prognoze nakon početka.
- Ovo je priprema za spajanje stvarnih vanjskih izvora; nije dokaz da su vrijeme, ozljede, postave, kvote ili ostali faktori već prikupljeni. Nema novog potvrđenog modelskog backtesta.

## Implementiran zajednički odabir kola (2026-10-30)
- `analytics/round_selector.py`: odabire jedan dopušteni tip po utakmici, potom gornjih 25% utakmica **unutar svakog kola**, strogo primjenjuje >1,30 za 1/X/2 i O/U 2,5 uz datiranu stvarnu kvotu te >2,00 za sintetičke 1X/X2.
- `backtest(rounds)` izračunava **jedinstvenu** točnost svih konačnih tipova; ne optimizira sedam odvojenih rezultata. Zaokruživanje 25%: polovice naviše, najmanje 1 za neprazno kolo; ako nema dopuštenih tipova, vraća manje.
- Dodano pet jediničnih testova. Njihovo izvršavanje u CI još nije potvrđeno. Trenutačno ne postoji potvrđen backtest kompletnog modela na svim stvarnim povijesnim faktorima.
- Važna metodološka napomena: najviša predviđena vjerojatnost među heterogenim tržištima favorizira široke ishode; potrebno kalibrirati i evaluirati selekciju na stvarnim povijesnim kolima.

## Obvezujuća odluka korisnika — 2026-10-30: nema ponavljanja parcijalnih testova
- **NE pokretati novi povijesni backtest** dok nisu povezani svi dogovoreni parametri i za njih pribavljeni stvarni povijesni podaci, dostupni prije svake prognoze.
- Prije toga raditi isključivo inventuru postojeće baze, oporavak ranije uvezenih liga, uvoz i vremensku validaciju nedostajućih parametara, implementaciju zajedničkog modela te provjere integriteta podataka i koda. Jedinični testovi koda nisu povijesni backtest.
- Konačni test je **jedan**, na svim dostupnim ligama (najmanje deset), s pet tipova (1, X, 2, over 2.5, under 2.5), bez kvota i bez 1X/X2, uz **globalni** odabir najboljih 25% iz cijele baze, ne po ligi.
- Prije testa objaviti pokrivenost svakog parametra i svake lige. Nedostajući povijesni ulazi nisu nula niti se smiju izmišljati; ako je obvezni faktor nepokriven, prvo riješiti izvor ili izričito prijaviti blokadu.
- Ranije dodana skripta za osnovni pet-tržišni test nije odobreni završni test i ne treba je pokretati kao zamjenu za puni test.
