# Kanonska pravila izbora i testiranja — potvrda 30.10.2026.

Ovaj zapis dopunjuje docs/PLAN_IZRADE.md i ima prednost nad starijim pravilima koja se sukobljavaju s ovim odlukama.

- Analizirati **sve utakmice kola**; odabrati najviše **25% utakmica kola**, najviše **jedan tip po utakmici**.
- Kandidati: **1, X, 2, više 2,5, manje 2,5, 1X, X2**. Za 1/X/2 i više/manje 2,5 potrebna je stvarna vremenski označena kvota **strogo >1,30**. Za 1X/X2 koristiti sintetičku kvotu **1/(P1+PX)** odnosno **1/(PX+P2)** i prag **strogo >2,00**. Sintetičku kvotu ne predstavljati kao stvarnu ponuđenu kvotu niti kao ostvarivi povrat.
- Za povijesnu usporedbu izračunati jedinstvenu ukupnu stopu pogodaka svih konačno izabranih tipova, uz pokrivenost, broj kola, broj utakmica, promašaje, Brier/kalibraciju gdje je primjenjivo i nesigurnost.
- Razdvojiti učenje, odabir parametara, kalibraciju i zaista novo neviđeno testno razdoblje. 2024/25 i 2025/26 već su pregledani te nisu novi neovisni test.
- Četrnaest skupina parametara treba dovršiti iz provjerenih izvora s vremenskim oznakama; nepoznato je NULL, ne nula. Uključiti rezultate i formu, napad/obranu, domaći teren, snagu protivnika, golove/xG, sastave/izostanke, individualnu kvalitetu, trenere kroz klubove, individualne duele kroz klubove, taktičke odnose, odmor/raspored, vrijeme/teren, motivaciju i datirane medijske informacije. Ovaj popis je cilj pokrivenosti, ne tvrdnja da su podaci već dostupni.
- Svaki faktor usporediti na istim vremenskim segmentima i izostavljanjem skupina; zadržati samo potvrđeni doprinos na razvoju. Ne optimizirati završni test unatrag.
- Prvo povijesni model i provjera, zatim aktualne preporuke. Ne objavljivati neprovjerene prognoze.
- StatsBomb pilot od 34 utakmice ostaje **izolirani nepotpuni istraživački skup** i nije zamjena za postojeću veću povijesnu bazu.
- Bez Bugarske i Rumunjske; zadržati postojeći skup liga. Poštovati ograničenja izvora i ne koristiti Transfermarkt za automatski ML uvoz bez dopuštenja.

Prije sljedećeg izvođenja usporediti postojeće analitičke skripte i izvještaje, ne prepisivati ranije eksperimente. Produkcijski upis tek uz stvarnu provjeru identiteta, deduplikacije, licence i vremenske dostupnosti.
