# Jedini glavni test: sve dopuštene ponude na četvrtini kola

Korisnik je pojasnio da ga zanima isključivo zajednička strategija: za svaku utakmicu usporediti 1/X/2, više/manje2,5 gola i dopuštene1X/X2; zatim izabrati najviše četvrtinu utakmica svakog kola prema najvećoj modelskoj vjerojatnosti.1X/X2prolaze samo uz sintetičku cijenu>=2 iz stvarnih osnovnih kvota iste kladionice. Nema zasebnog odabira samo dvostruke šanse, forsiranja da se takva ponuda mora pojaviti ili fiksnog postotka tržišta.

## Novi zajednički pilot

OpenFootball2026/27 ima rasporede/rezultate za sedam postojećih liga:EN,IT,ES,DE,FR,PT,NL. PreostaleBE,TR,GRnisu trajno izbačene; u tom izvoru nedostaju odgovarajuće nove datoteke. TipsAuditCSVima stvarne Pinnacle1X2cijene; pribavljeni su datirani arhivski checkpointovi od7.8.do25.9.2026. Umjesto nepovezanog kvotnog filtra, po utakmici povezujemo izvor, datum i normalizirana imena oba kluba, bez fuzzy pogađanja. Duplicirani/nejasni parovi ne prolaze.

Za vremensku podlogu uzimamo posljednji checkpoint prije konzervativne granice prvog početka kola. Lokalni početci iz izvora tretiraju se kaoUTC+3, što za sedam liga daje namjerno raniju UTCdonju granicu; nedostajuće vrijeme znači ponoć. Prognoze rezultata koriste samo povijest prije najranijeg datuma kola minus dva dana. Koeficijenti osnovnog modela i ritam refita ostaju isti; nema podešavanja prema pilot ishodima.

Cijene iz CSV-a povezujemo samo kada je provider record_hash jednak onome u ranijem checkpointu, snapshot je prije prve utakmice, a zapis tada nije bio završen. Prema dokumentaciji pružatelja hash pokriva i osnovne pin_open cijene. Stariji JSONne izlaže sva tri inputa, pa se oslanjamo na tu izjavu, bez neovisnog kriptografskog ponavljanja. Vrijeme generiranja arhive nije neovisno verificirano vrijeme prve objave. Raspored je također naknadni snapshot. To su izričite pretpostavke pilota, a ne tvrdnja potpuno rekonstruirane tada dostupne baze.

## Rezultat iste strategije na istim kolima

| Pokus | Odabrano/ocijenjeno | Pogoci | Promašaji | Točnost |
|---|---:|---:|---:|---:|
| Referenca: pet izvornih ponuda, četvrtina kola |80|64|16|80,00%|
| Zajednički izbor: pet+1X/X2uz>=2, četvrtina kola |80|64|16|80,00%|

40kola,376izvornih utakmica,326s dovoljno prognozne povijesti. Budžet računa svih376utakmica, uključujući50bez dovoljno podloge. Floor(N/4)daje80odabranih,21,28%izvornog skupa; nula odabranih bez ishoda u ovom završenom razdoblju. Povezano99pre-roundkvotnih snapshot zapisa;39dvostrukih šansi prošlo je cijenu>=2. Model nijednu nije procijenio boljom od ponuda koje je već odabrao, pa je odabrano0dvostrukih šansi i0kola s promijenjenim izborom. Nema povećanja točnosti od njihova dodavanja u ovom pilotu.

Izabrane ponude:37domaćin,16gost,19više2,5 i8manje2,5. Remi i dvostruke šanse bili su dopušteni, ali nisu morali biti odabrani. Tuđe modelske vjerojatnosti nisu korištene. Na izbor ponude i susreta ne utječe ishod. Eventualna nesuglasnost izvora ishoda samo se zapisuje u kvalitetu; ne uklanja naknadno kvotne kandidate.

80utakmica je premalo za raniji minimum200, a vremensko/izvorno razdoblje nije isto kao stari test74%. Ne predstavljati80%kao rast74→80na istom uzorku, kao nezavisni budući dokaz ili cilj90%postignut. Aktivni osnovni model nije zamijenjen; evaluira se ista zajednička politika koju korisnik traži. Izolirani kvotni benchmark32,62%nije glavni prikaz niti rezultat algoritma; arhiva ostaje samo za reviziju.

## Provjere i arhive

analytics/joint_quarter.py, glavni rezultat data/experiments/20261029-joint-seven-quarter-pilot-v2/. V1sačuvan s vlastitim code-snapshot.py i hashom; V2uklanja mogućnost da naknadno neslaganje ishoda utječe na dostupnost kvote (na stvarnim redcima nema takvih konflikata pa su brojevi isti). Snapshotovi, izvorne datoteke i pojedinačni rezultati ostaju u privatnom projektnom izvoru; javno su kod, zbirni nalazi i manifesti.

Glavni panel aplikacije je zajednički test. Stariji74%je referentni pokus pod detaljima, kalkulator je pomoćni ulaz, a zasebni1X/X2postoci nisu prikaz glavne strategije. Budući freeze APIuzima ponude svih triju podržanih markettipova prije deduplikacije; kartoni ili drugi goal lineovi ne smiju istisnuti valjanu ponudu. Liveprognoze ostaju isključene dok nema odgovarajućeg provjerenog aktualnog feeda.

Izvori:OpenFootball football.json, javna domena/CC0, https://github.com/openfootball/football.json . TipsAudit,CCBY4.0, https://github.com/tipsaudit/track-record-public ; atribucija https://tipsaudit.com . Normalizacija i izračun sintetičkih kvota su naše transformacije.
