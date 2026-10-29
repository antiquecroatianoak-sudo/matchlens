# MatchLens — plan izrade i zadatak za Claude

## Granica projekta
Ovo je nova samostalna nogometna aplikacija. Izmjene dopuštene samo u ovom projektu. Ne koristiti repozitorije, baze, podatke, API ključeve, postavke, automatizacije ili kanale EUnekretnina, Košarice, građevinskih i drugih aplikacija. Za predaju koristiti isključivo zaseban nogometni repozitorij i zasebnu Claude sesiju. Ovaj dokument nije dokaz predaje ni pokretanja Claudea.

## Cilj
Učiti iz velike povijesne baze koliko protivnikov stil odgovara momčadi. Cilj nije nužno pobjednik: usporediti golove, hendikepe, oba daju gol, poluvrijeme/kraj i kartone te se specijalizirati samo gdje postoji stabilan dokaz. Odvojeno prikazivati stopu pogodaka, kalibraciju i rezultat pri stvarnim kvotama. Bez jamstva pogodaka ili zarade; dopušten zaključak je nema preporuke.

## Faze i uvjeti završetka
1. **Temelj i sučelje (v0.1):** privatni responzivni pregled, utakmice, katalog izvora, trajne bilješke, specifikacija faktora, JSON uvoz/izvoz i dnevnik ručnih procjena. Jasno odvojiti matematički scenarij od treniranog modela. Provjeriti spremanje, izmjenu ishoda, brisanje i izolaciju korisnika. Trenutno napravljeno u ovom projektu; nema automatskih podataka ni treniranog modela.
2. **Pregled i pristup izvorima:** katalog službenih stranica liga i saveza, klubova, SofaScorea i sličnih servisa, događajnih/prostornih podataka, vremena, medija i povijesnih kvota. Za svaki zapis dokumentirati ligu, sezonu, polja, licencu, uvjete pristupa, dostupnost API-ja, svježinu i povijesnu dubinu. Ne tvrditi da izvor radi dok pristup i dohvat nisu provjereni. Pilot odabrati prema stvarnoj pokrivenosti; all-liga katalog širiti postupno.
3. **Podatkovni cjevovod:** kanonski identiteti liga, sezona, klubova, utakmica, stadiona, igrača i trenera. Deduplikacija, verzije, izvor, vrijeme objave/dohvata i vrijeme dostupnosti prije prognoze. Odvojene sirove i obrađene tablice. Praćenje kvalitete i nedostajućih vrijednosti; nepoznato nije nula. Povijesne prognoze vremena čuvati kao prognoze izdane prije utakmice, stvarno vrijeme kao odvojeno opažanje.
4. **Osnovni model:** vremenski promjenjiva napadačka i obrambena snaga, snaga lige, domaći teren, postave i izostanci, kvaliteta zamjena, odmor, putovanje i promjene trenera. Definirati točan trenutak prognoze; ranija verzija sa scenarijima postave, kasnija s potvrđenim sastavom.
5. **Taktička međudjelovanja:** formacije po fazama, uloge, presing × izlazak iz presinga, visoka linija × dubina, tranzicija × zaštita nakon gubitka, niski blok × kreacija, bokovi, prekidi i kvaliteta prilika. Profil ažurirati kroz vrijeme. Segmentirati povijest prema minuti, rezultatu, kartonima, zamjenama i promjenama taktike. Događaji, 360 snimke i kontinuirani tracking nisu zamjenjivi. Doprinos dodatnih faktora ocjenjivati ablacijama; prediktivni doprinos nije dokaz čistog uzročnog učinka.
6. **Ostali faktori:** kvaliteta i učinci pojedinaca prilagođeni minutaži, ulozi i protivniku; profil trenera kroz klubove, taktika protiv jačih/slabijih, prilagodljivost, rotacije i uigravanje; prioritet lige/kupa/Europe procjenjivati po susretu. Temperatura, oborine, vjetar, vlaga; podloga, dimenzije, natopljenost, snijeg i oštećenja zasebno. Medijske informacije o odnosima suigrača, treneru i zajedništvu s pouzdanošću; preuzeta vijest nije neovisna potvrda. Za kartone uključiti suca i disciplinu.
7. **Tržišta i provjera:** čuvati kladionicu, točnu ponudu, granicu, kvotu, vrijeme, pravila obračuna, produžetke/povrate/djelomične ishode. Predviđanja zamrznuti prije početka uz zaseban revizijski zapis. Učiti na prošlosti; izabrati model/tržište na kasnijem validacijskom razdoblju; završni test na još novijem, neupotrijebljenom razdoblju. Kontrolirati pretjerano ispitivanje mnogih tržišta i korelirane oklade. Mjeriti log loss/Brier, kalibraciju, stopu pogodaka, pokrivenost, rezultat uz jednake uloge, nesigurnost i stabilnost kroz sezone. Usporediti osnovni model, postave i uloge, taktiku i dodatni kontekst; usporediti i tržišnu referencu uz maržu. Kod povrata i djelomičnih ishoda koristiti točan obračun.
8. **Prognoze u sučelju:** osnovna prognoza, taktička promjena i konačne vjerojatnosti; dostupnost podataka, glavni razlozi, vremenska oznaka i nesigurnost. Automatizaciju osvježavanja uključiti tek uz izričit zahtjev i provjerene izvore. Nikada ne prikazivati izmišljene susrete, kvote ili točnost kao stvarne.

## Trenutni tehnički temelj
Vinext/React na Sites, samostalni D1, korisnički odvojeni zapisi, privatno objavljivanje. Dnevnik v0.1 je ručni istraživački alat, ne nepromjenjivi dokaz prognoze prije utakmice. Poissonov laboratorij prima ručno zadane intenzitete i ne koristi povijesne faktore. Nema preuzetih podataka ni API tajni drugih aplikacija.

## Upute za predaju
Predati ovaj plan i kod tek na potvrđeni zasebni nogometni GitHub/Claude kanal. Ne koristiti postojeće komentare ili sesije drugih aplikacija. Najprije tražiti tehnički pregled podataka i vremenskog testiranja, zatim implementaciju po fazama s pregledom koda. Objavljen komentar nije potvrda da je Claude pokrenuo rad; zabilježiti link predaje i njegov odgovor zasebno.

## Vizualna tema — 28.10.2026.
Korisnik je odobrio tamnu plavo-crnu temu prema referentnoj slici: blagi zakrivljeni plavi valovi na podlozi te okviri s naglašenom plavom koja postupno pada prema crnoj. Tema je u app/theme.css, uključena nakon osnovnih stilova. Zadržati čitljivost na mobilnom uređaju.

## Rangiranje prognoza — dogovor 28.10.2026.
Početna stranica prikazuje Top 10 po kalibriranoj procijenjenoj vjerojatnosti, sve vrste kladioničkih ponuda zajedno. Zasebna ikona otvara podprozor s do 50. Dopušteno je više različitih ponuda iste utakmice. Vjerojatnost prikazati s dvije decimale. Dodatni podprozor „Koeficijent 2,00+” prvo filtrira sve prihvatljive prognoze s dostupnom kvotom >= 2,00, zatim rangira po vjerojatnosti i prikazuje do 50; ne filtrirati samo prethodni Top 50. Kvota nije vjerojatnost. Ne ograničavati vrste ponuda na 1X2. Točna granica i pravila obračuna dio su identiteta ponude.

Implementirano: sva tri prikaza, sortiranje, uklanjanje duplikata iste ponude, isključivanje proteklih/isteklih/neprovjerenih prognoza i ručnih procjena. Bez izmišljenih prognoza za popunjavanje liste. Još nije implementirano: treniranje/kalibracija modela i automatska izrada prognoza. Podatkovni ugovor `prediction` zahtijeva broj `prob` (0–100), `matchId`, `market`, `selection`, `modelVersion`, `validationId`, `validatedAt`, `generatedAt`, `kickoff`, `validUntil`, `calibrated: true`, `status: verified`; `odds` je zasebna brojčana kvota. Oznake potvrde smije izdavati tek provjereni modelski cjevovod, ne ručni dnevnik.

## Aktivni opseg modela — 28.10.2026.
Korisnik je odabrao prvih deset liga prema aktualnom UEFA petogodišnjem poretku: Engleska, Italija, Španjolska, Njemačka, Francuska, Portugal, Belgija, Nizozemska, Turska i Grčka. Završni povijesni test ograničiti na dvije posljednje završene sezone, 2024./25. i 2025./26. Starije sezone služe učenju i izboru parametara. Početne ponude su isključivo 1, X, 2 i više/manje od 2,5 gola u regularnom vremenu; kartoni i ostala tržišta odgođeni su. To ima prednost nad ranijim širim pilotom.

Traži se velik broj pomičnih vremenskih testova. Prva mreža: 27 kombinacija prozora 10/20/50 utakmica, poluvremena težine 5/10/30 utakmica i zaglađivanja 4/8/16. Parametri birani na 2022./23., zasebna kalibracija na 2023./24., zaključani završni test na 2024./25. i 2025./26. Računati prognozu prije otkrivanja ishoda i po datumima, uz konzervativno izostavljanje posljednja dva dana rezultata. Ponavljanje testova nije jamstvo vrlo visoke točnosti. Za buduće promjene modela ova dva završna razdoblja više nisu potpuno neviđeni dokaz; potreban novi neovisni test.

Podaci OpenFootball / CC0: izvorni JSON snapshotovi s hashom i porijeklom. Dio liga/sezona je nepotpun; nedostajuće rezultate ne pretvarati u 0:0. Format score:[0,0] u izvoru je izričit rezultat, odsutni score nije rezultat. Izvor nema arhivirane povijesne oznake prve objave, pa rezultat predstavlja retrospektivnu simulaciju dostupnosti uz pretpostavku, ne potpuno rekonstruiranu tadašnju bazu. Nisu uključeni postave, taktika, ozljede, kvote ni drugi faktori; oni i dalje zahtijevaju nove izvore i mjerenje doprinosa.

## Naknadni odabir zamjenskih liga
Vlasnik je odobrio da se nepotpune lige privremeno stave na stranu i zamijene sljedećima po UEFA poretku uz potvrđenu pokrivenost obiju sezona. Izričito provjeriti Bugarsku i Rumunjsku kao moguće zamjene. Ne predstavljati ih kao već testirane dok rezultati po datumima i fazama nisu uvezeni. Dosadašnji javni pilot ostaje označen izvornim skupom liga i ne smije se tiho preimenovati.

## Važeća odluka vlasnika — bez Bugarske i Rumunjske
Korisnik je 28.10.2026. izričito odabrao nastavak bez Bugarske i Rumunjske. Obje izostaviti iz kandidata za zamjenu; ne čekati njihove podatke. Nastaviti redom po UEFA poretku i uključiti samo zamjenske lige s potvrđenim rezultatima po utakmicama, datumima i fazama za obje testne sezone. Prethodno navedena provjera BG/RO ostaje povijesni zapis, nije aktivna zadaća. Zamjenske lige još nisu potvrđene niti ubačene u već objavljeni pilot.

## Važeći nastavak — zadržati postojeće lige i širiti povijesno učenje
Posljednja izričita odluka vlasnika ima prednost nad gornjim planom zamjena: nastaviti s postojećih deset liga, bez traženja zamjena, bez Bugarske i Rumunjske. Aktivni cilj ostaje 1X2 i više/manje 2,5 gola; točan broj golova nije zasebno ugovoren cilj modela.

Vlasnik traži ponovljeno testiranje različitih faktora i njihovih težina. Svaki novi razvojni ciklus mora imati novu mapu eksperimenta, zapis isprobanih postavki, vremenske granice, zaključanu odabranu konfiguraciju, prognoze i rezultate. Isti završeni eksperiment ne prepisivati. Ponovno izvođenje istih postavki na istim podacima služi ponovljivosti, ne poboljšava samo po sebi model.

Implementiran prošireni ciklus: Poissonova regresija s naučenim težinama, sedam skupina obilježja, prozori 10/20/50, poluvrijeme težine 5/15/30, tri jačine regularizacije, tri korekcije malih rezultata i tri postavke kalibracijske temperature — ukupno 1.701 kombinacija. Obilježja su izvedena samo iz ranije dostupnih rezultata: napad/obrana, domaći/gostujući učinak, snaga prethodnih protivnika, novija forma, Elo razlika i razmak zabilježenih ligaških utakmica. Posljednji faktor nije cjeloviti odmor bez kupova/Europe.

Model za razvojnu sezonu uči se na prethodnim sezonama; izbor se radi na 2022./23. i 2023./24., s jednakom težinom tih sezona po obiteljskom Brieru. Sezone 2024./25. i 2025./26. ostaju ponovna opisna analiza jer su već viđene u starom pilotu. Nikakvo novo podešavanje ne čini ih ponovno neovisnim testom. Za novi dokaz treba unaprijed zaključana verzija i stvarno neviđeno razdoblje.

Doprinos mjeriti usporedbom skupina i izostavljanjem skupine uz ponovno učenje. Ne nametati unaprijed da svi faktori moraju poboljšati predviđanje. Sve izvorno dogovorene postave, ozljede, treneri, taktička međudjelovanja, kvaliteta prilika, vrijeme/teren i mediji ostaju u dugoročnom planu; ne izmišljati ih iz konačnih rezultata. Dodavati ih tek s provjerenim vremenski označenim ulazom i novom razvojnom usporedbom.

## Nastavak razvoja i objava — filtri i novi algoritmi
Vlasnik je odobrio daljnji razvoj i javnu objavu MatchLens projektnog koda te ažuriranje privatne aplikacije nakon provjera. Ne čekati automatizaciju komunikacije za analitički rad.

Posebno ocijeniti stvarne dnevne Top 10/50 među svim podržanim ponudama, uz dopuštene višestruke ponude istog susreta. Jedinica dana je izvorni kalendarski datum jer nemamo potpune vremenske zone/vremena početka; izjednačene vjerojatnosti razrješava stabilni identifikator ponude. Prikazati pragove 60/65/70/75/80/85/90/95%, broj odabranih, ocijenjenih i neocijenjenih, pogodaka i promašaja te obuhvat jedinstvenih utakmica. Nepoznati ishodi moraju ostati u skupu za rangiranje; ne birati samo utakmice za koje je kasnije pronađen rezultat. Ne prikazivati uspješnost jedne najbolje ponude kao uspješnost Top 10 ili Top 50.

Takvi pragovi trenutačno su opisna istraživačka usporedba na već pregledanim sezonama, ne odabrana operativna strategija. Ne uzeti najbolji naknadno viđeni prag i proglasiti ga neovisnim dokazom. Prikazati i slabije pragove i Top50. Povijesni raspored je naknadni snapshot, pa ni ovaj dnevni poredak nije potpuno rekonstruiran tada poznati raspored. Kvota 2,00+ ostaje neprovjerljiva bez stvarnih vremenski označenih kvota.

Novi zasebni razvojni ciklus direct-v1 uspoređuje izravnu multinomnu klasifikaciju 1X2 i binarnu klasifikaciju više/manje 2,5 s postojećim Poisson + Elo modelom. Dodaje rezultate izvedene samo iz ranije povijesti: prosjek i promjenjivost ukupnih golova, učestalost clean-sheet/bez postignutog gola/remija, noviji trend, zaglađenu povijest međusobnih susreta i nelinearne odnose snage. To nisu taktički, kadrovski ni vremenski ulazi. Dvanaest konfiguracija birati na 2022/23, šest temperatura kalibracije na zasebnoj 2023/24; audit 2024/25 i 2025/26 ostaje opisna ponovna analiza. Novi slabiji model ne zamjenjuje postojeći. Arhivirati pokušaje i rezultate bez prepisivanja expanded-v1 i prospektivnog zaključavanja.


## Prioritet 29.10.2026. — prvo algoritam, zatim aktualne prognoze
Vlasnik je pojasnio da trenutačni prikaz rezultata i aktualnih prognoza nije prioritet. Povijesne utakmice služe ponavljanom učenju faktora i težina; aktualni ulazi slijede nakon pouzdane provjere algoritma. Visoku buduću točnost nije dopušteno obećati niti zaključiti samo iz podešavanja na već poznatim sezonama.

Novi market-specialists-v1 zasebno bira konfiguraciju za 1X2 i golove, polazeći od arhiviranih razvojnih rezultata. Uspoređuje jednaku težinu primjera i kalendarsko prepolovljavanje 730/365 dana te sezonsko/tromjesečno ponovno učenje. Svaki refit koristi rezultate strogo prije početka bloka minus dva dana. Svih 12 kandidata i tragovi treniranja ostaju arhivirani; audit je ponovno opisno pregledavanje 2024/25 i 2025/26. Nema automatskih preporuka.


## Proširenje izvora — 29.10.2026.
Korisnik izričito traži dodati Transfermarkt i po potrebi proširiti izvore točnih informacija i statistike. Implementiran ugrađeni katalog sa statusom stvarne integracije, pokrivenošću, namjenom, uvjetima, vremenskim ograničenjima i izvornim poveznicama. Transfermarkt je referenca koja zahtijeva posebno dopuštenje: točka 11.1 zabranjuje automatizirano kopiranje i uporabu za razvoj AI/ML. Ne tretirati korisnikovo imenovanje izvora kao dopuštenje pružatelja podataka.

U katalogu i StatsBomb Open Data, football-data.org, Football-Data.co.uk, Open-Meteo Previous/Single Runs, službena UEFA statistika i postojeći OpenFootball. Nijedan novi zapis sam ne aktivira uvoz ili trening. Za ozljede, trenere i postave dodatno tražiti datirane službene objave klubova/liga, ali ne tvrditi potpunu pokrivenost bez provjere. Svaki novi faktor treba izvor, vrijeme objave/dohvata, identitete, dostupnost prije ciljanog susreta i usporedbu doprinosa. Bez plaćenih usluga.
