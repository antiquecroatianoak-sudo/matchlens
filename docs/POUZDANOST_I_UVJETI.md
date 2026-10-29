# Korekcija vjerojatnosti i dodatni uvjeti — 29.10.2026.

Vlasnik traži nastavak podešavanja parametara i dodavanje uvjeta s ciljem >90%. Novi zasebni ciklus `confidence-search-v1` čuva 14 razvojnih usporedbi korekcije (12 naučenih i dvije reference bez korekcije), 28 unaprijed zadanih pravila odabira, lock prije audita, tragove učenja i prognoze. Ne prepisuje ranije cikluse i ne aktivira preporuke.

Osnovni model: zaključani market-specialists-v1, deset postojećih liga, 1X2 i više/manje 2,5 gola. Svaki tržišni model refita se svojim ranije odabranim ritmom i uz dva dana embarga. Nema novih vanjskih činjenica, postava, vremenskih ili taktičkih ulaza u ovom ciklusu.

Korekcija: skala log-vjerojatnosti, pristranost klasa i opcionalno zaglađeni ligaški pomaci; kazna prema identitetu 0,01/0,1/1. Za lokalni pomak najmanje200 ranijih kalibracijskih susreta, inače zajednički pomak. Za nepoznatu ligu samo zajednički dio. 7varijanti po obitelji tržišta. Korektor se uči samo na prognozama/ishodima2022/23; bira po log lossu2023/24 i nakon toga ostaje zamrznut. Obje obitelji izabrale su identitet, bez nove korekcije.

Važna granica: osnovne konfiguracije i ritam refita ranije su birani na obje razvojne sezone. Novi vremenski odmak korektora ne čini te sezone ponovno neovisnim razvojem; cijeli pokus je istraživački. Ni audit2024/25–2025/26 nije neviđen: ranije je višekratno pregledan. Nema povijesnih oznaka prve objave rezultata; embargo je pretpostavka.

Novi filteri prvo biraju jednu najvjerojatniju ponudu po utakmici, bez gledanja ishoda. Pragovi0/60/70/80/85/90/95%; četiri profila: svi, slaganje osnovnog/korigiranog izbora, povijest i povijest+slaganje. Povijest traži >=20 ranijih rezultata obje momčadi i <=21dan od posljednjeg zabilježenog ligaškog rezultata. To nije potpuni odmor niti potpuni broj nastupa; kupovi/Europa i praznine nisu obuhvaćeni. Nepoznati ishodi ostaju u odabiru, ne postaju0:0 i ne nestaju iz obuhvata. Isti dan isključuje se uz prethodna dva dana. Postojeći dnevni Top10/50 zadržava dopuštenje više ponuda istog susreta; ova dodatna analiza ne mijenja taj ugovor.

Prije audita, na razvoju, strateški kriterij: >=200različitih ocijenjenih susreta i jednostrana donja Wilsonova granica >90%, Bonferroni prilagođena za28razvojnih pravila. Među onima koji prolaze bira se najveći obuhvat; ako nijedan, nema odabranog pravila. **Nijedan nije prošao**, najveća prilagođena donja razvojna granica među svim pravilima bila je74,49%. Wilson pretpostavka ne rješava vremensku/momčadsku ovisnost; ovo je samo opisni screening, nikakav neovisan dokaz. Konzervativna korekcija28pravila ne pokriva sve ranije cikluse istraživanja.

## Nalaz

Na istih5772ocijenjenih audit susreta reference i novog kandidata identične su vjerojatnosti: 59,86%najvjerojatnija ponuda, Brier0,21852459. Nema poboljšanja.

| Uvjet, jedna ponuda po susretu | Pogoci | Promašaji | Bez ishoda | Točnost | Obuhvat6243prihvatljiva susreta |
|---|---:|---:|---:|---:|---:|
| Bez dodatnog uvjeta, prag80% |199|34|17|85,41%|4,00%|
| Povijest, prag80% |180|32|2|84,91%|3,43%|
| Bez dodatnog uvjeta, prag90% |14|5|1|73,68%|0,32%|

Viši prag procijenjene vjerojatnosti nije automatski veća izmjerena točnost. Novi uvjet povijesti nije bolji na80%. Budući da je korekcija identitet, slaganje je tautološki isto i ne stvara dodatni dokaz; tih14pravila nisu14neovisnih potvrda. UI prikazuje oba korisna profila, objašnjava duplikate i čuva sve28redaka u JSON-u. Stari prag85,83%bio je među svim ponudama, dok je ovdje samo jedna po utakmici: različiti imenici, ne novi lift ili pad modela.

Šest novih testova: normalizacija i nepoznata liga, izbor samo prema razvojnom gubitku, očuvanje nepoznatih ishoda i neovisnost odabira o njima, embargo/pending povijest, nedovoljan uzorak/interval za90%, jedna ponuda po susretu. Ukupno61Python test prošao; TypeScript prošao. Produkcijsku objavu i build potvrditi nakon uspješnog odgovora. Vizualna provjera ostaje ograničena ranije nedostupnim preview preglednikom.

Sljedeći opravdani razvoj: provjereni višesezonski vanjski ulazi i nezavisno buduće razdoblje s unaprijed zamrznutim modelom. Ne nastavljati istu28pragovnu pretragu samo radi povoljnog broja.
