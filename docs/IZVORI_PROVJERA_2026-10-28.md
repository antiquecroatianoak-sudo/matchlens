# MatchLens — provjera izvora 28.10.2026.

## Status i preporuka
Ovo je provjera dokumentacije i probnog dohvata, ne dokaz integracije u web-aplikaciju. Nisu aktivirane plaćene usluge. Preporučeni prvi povijesni pilot: Football-Data.co.uk rezultati i odgovarajuće kvote. StatsBomb koristiti kao zaseban taktički istraživački uzorak, bez pretpostavke iste pokrivenosti. Vrijeme dodati uz provjeru tada dostupne prognoze.

## Football-Data.co.uk — uspješan probni dohvat
- Katalog: https://www.football-data.co.uk/downloadm.php
- Objašnjenja: https://www.football-data.co.uk/notes.txt
- Test: https://www.football-data.co.uk/mmz4281/2425/E0.csv — HTTP 200; 197110 bajtova; 380 redaka utakmica Premier League 2024/25.
- Pronađeni stupci: datum, vrijeme, klubovi, rezultat cijele utakmice/poluvremena, sudac, udarci, udarci u okvir, prekršaji, korneri, žuti/crveni kartoni; kvote 1X2, više/manje 2.5 i azijski hendikep, uključujući zasebne završne kvote.
- Katalog nudi sezonske arhive od 1993/94; dostupnost statistike i kvota nije jednaka za sve lige/sezone. Besplatni download ne znači neograničenu licencu redistribucije: prava za javno ponovno objavljivanje podataka nisu ovim pregledom potvrđena. Ne stavljati sirove arhive u javni repo.
- Notes navodi prikupljanje nezavršnih kvota petkom za vikend i utorkom za sredinu tjedna; precizna vremenska oznaka svake kvote nije potvrđena. Završnu kvotu ne koristiti kao ranije poznati ulaz. Ne tvrditi precizno ostvariv povijesni povrat ako vrijeme dostupnosti nije potvrđeno.
- Notes upozorava na različito računanje žutih kartona kod drugog žutog po natjecanjima. Za kartonsko tržište uskladiti statistiku s pravilima konkretne ponude.
- Podaci o utakmici (udarci, kartoni itd.) dostupni nakon susreta ne smiju postati ulazi za predviđanje istog susreta; dopušteni su kao povijest prethodnih susreta.
- Vremenska zona polja Time i stabilan izvorni ID nisu potvrđeni ovim pregledom; ne izmišljati UTC ni ID. Prije adaptera definirati i provjeriti mapiranje.

## StatsBomb / Hudl Open Data — uspješan katalog
- https://github.com/hudl/open-data
- https://github.com/hudl/open-data/blob/master/README.md
- Test: https://raw.githubusercontent.com/hudl/open-data/master/data/competitions.json — HTTP 200; 34887 bajtova; 80 zapisa kombinacija natjecanja/sezone (nije 80 liga).
- Katalog sadrži Bundesligu 2023/24 (competition_id 9, season_id 281) i 2015/16 (9,27). To ne dokazuje potpunu sezonu; broj susreta i događajne datoteke tek treba provjeriti.
- README opisuje JSON utakmica, događaja i postava, uz 360 samo za odabrane susrete. Nije stalni puni feed svih liga; 360 nije kontinuirani tracking.
- README traži navođenje StatsBomba i logotipa za objavljene analize. Puni LICENSE.pdf još nije pročitan i komercijalna uporaba nije odobrena ovim pregledom. Ne pretpostaviti da je riječ o MIT/CC0 licenci.
- Kasnije objavljen/revidiran povijesni skup nije dokaz da je baš ta verzija bila dostupna prije utakmice; razlikovati retrospektivno istraživanje od stroge simulacije tada dostupnih podataka.

## Open-Meteo — uspješan arhivski probni dohvat
- https://open-meteo.com/en/docs/historical-weather-api
- https://open-meteo.com/en/docs/historical-forecast-api
- https://open-meteo.com/en/docs/previous-runs-api
- https://open-meteo.com/en/terms
- Test archive-api za koordinatu 51.555,-0.108, datum 2024-08-17: HTTP 200; 1266 bajtova; 24 satna zapisa temperature, relativne vlage, oborina i brzine vjetra. Ovo je probna koordinata, ne potvrđeno povezivanje stadiona.
- Arhivska reanaliza opisuje prošle uvjete; nije tada izdana prognoza ni izravno mjerenje na travnjaku. Nije dokaz stanja terena.
- Za povijesnu prediktivnu provjeru istražiti Previous Runs ili Single Runs s unaprijed odabranim horizontom i vremenom stvarne dostupnosti modela. Spojeni Historical Forecast niz nije sam po sebi prognoza izdana dan ranije.
- Besplatni API uvjeti: nekomercijalno korištenje; manje od 10000 poziva/dan, 5000/sat i 600/min. Podaci pod CC BY 4.0; navesti izvor. Komercijalni status korisnikove namjene treba razjasniti prije produkcijske uporabe. Nije aktivirana pretplata.
- Serijsko/batch preuzimanje i predmemorija mogu smanjiti broj poziva. Bez ukupnog limita utakmica u našoj bazi, uz poštovanje ograničenja izvora.

## Football-Data.org — dokumentacija provjerena, API nije testiran
- https://www.football-data.org/coverage
- https://www.football-data.org/pricing
- Besplatni plan navodi 12 natjecanja, raspored, tablice i odgođene rezultate te 10 poziva/min.
- Dublja povijest i postave/događaji prikazani su u zasebnim plaćenim paketima. Ne pretpostaviti da besplatni plan pokriva sve faktore ili svu povijest.
- Nema potvrđenog tokena ni probnog API dohvata. Kandidat za raspored/identitete, ne aktivni konektor.

## SofaScore — ne planirati neodobren masovni uvoz
- https://sofascore.helpscoutdocs.com/article/129-does-sofascore-offer-sports-data-api?lng=en
- https://www.sofascore.com/de/terms-and-conditions
- Službeni FAQ navodi da podatke ne dijele kroz API zbog ugovora s dobavljačima. Uvjeti ograničavaju scraping i izvlačenje baze bez izričitog pristanka, osim zakonom dopuštenog.
- Nije testirano neslužbeno interno sučelje niti zaobilažena ograničenja. Uvoz nije odobren niti integriran. Za masovnu uporabu potreban dopušten kanal.

## Još treba provjeriti
1. Stvarni uzorak utakmica, postava i događaja StatsBomba te potpuna licenca.
2. Pokrivenost više liga/sezona Football-Data.co.uk, prazne vrijednosti, dosljednost vremena i uvjeti uporabe.
3. Arhivska prognoza Open-Metea izdana prije konkretne utakmice; dostupnost svih potrebnih varijabli i povijesti.
4. Službeni izvori liga/klubova za ozljede, suspenzije, trenere, stadione i podlogu.
5. Medijski izvori, RSS/licencirani pristup, datum prve objave, deduplikacija prenesenih vijesti i pouzdanost tvrdnji. Ne izjednačavati medijski sentiment s potvrđenim stanjem svlačionice.
6. Povijesne kvote za kartone, oba daju gol i poluvrijeme/kraj nisu potvrđene navedenim probnim CSV-om.

## Sljedeća implementacija
Prvo adapter jednog provjerenog CSV skupa uz očuvanje izvornih polja i oznaka nedostajućih podataka. Zatim ponovljivi privatni uvoz i izvještaj pokrivenosti. Tek nakon toga vremenski model i pomična provjera prema glavnom planu. Nijedan današnji probni dohvat nije integracija u web-bazu.
