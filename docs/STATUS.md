# MatchLens — stanje 28.10.2026.

## Potvrđeno
- Privatna Sites aplikacija: https://matchlens-luka.lushlily1.chatgpt.site. Javni zasebni GitHub: antiquecroatianoak-sudo/matchlens.
- Top 10, podprozor Top 50 i filter kvote >=2,00 objavljeni su ranijom verzijom (commit 9979181c1e2ab28af22bfc9402afb4358ff247e7). Više ponuda iste utakmice, dvije decimale, rang po vjerojatnosti. Liste bez lažnih podataka, model nije ovlašten izdavati buduće preporuke.
- Povijesni pilot implementiran i pokrenut: 20.517 odigranih utakmica iz 10 liga; 27 kombinacija prozora, vremenske težine i zaglađivanja. Ciljevi samo 1X2 i više/manje od 2,5 golova. Kartoni odgođeni.
- Završni test: dostupne utakmice 2024./25. i 2025./26.; 5.772 valjane prognoze. Učenje/izbor na starijim sezonama do 2022./23.; kalibracija 2023./24. Test ide kronološki uz odmak 2 dana. Provjereno da kasniji ili istodnevni rezultati ne mijenjaju ranije prognoze.
- Odabrano među 27: 50 utakmica, prepolovljavanje težine nakon 30 utakmica, prior 8. Kalibrirani pilot: 51,02% za najvjerojatniji 1X2, 55,20% za stranu više/manje 2,5, 57,67% za jednu najvjerojatniju ponudu među pet opcija. To nisu Top 10 rezultati, kvota-2+ rezultati ni dokaz zarade.
- Brier: referenca lige 0,23218; osnovni model 0,21994; kalibrirana verzija 0,22124. Kalibracija nije poboljšala osnovni model na testu. Model ostaje istraživački.
- Dohvati: OpenFootball football.json te izvorne TXT baze openfootball/europe i openfootball/belgium (CC0). Upstream je dodao 950 rezultata: 933 za 2023./24. i 17 belgijskih za 2025./26. Nije potvrđen drugi neovisni pružatelj. Manifest s SHA-256, izvori, izvještaj i prognoze nalaze se u data/.
- Šest Python testova uspješno, TypeScript provjera uspješna. Ranija provjera rangiranja: četiri testa. Browser preview je bio nedostupan (connection refused), vizualni QA nije potvrđen.

## Preostale prepreke
- Ne predstavljati pilot kao potpuno pokrivanje posljednjih dviju sezona: neki rezultati nedostaju, osobito Belgija/Turska/Grčka 2025./26., ponešto i drugdje. Dodatne faze i doigravanje nisu svugdje potpuno navedeni. Prikazati broj ocijenjenih i broj rezultata po sezoni/lizi.
- Turski/grčki izvorni TXT također je nepotpun za 2025./26.; ne smatrati promjenu formata neovisnom potvrdom. Tražiti dodatni dopušteni izvor za svih 10 liga, ne smanjivati opseg na 3 lige. Nema odobrenja za plaćene usluge.
- Nema povijesnih kvota s dokazanim vremenom dostupnosti, nema ROI niti testa kvota2+. Nema postava, ozljeda, taktike, vremenskih prognoza niti drugih kontekstualnih faktora. Ne tvrditi da su analizirani.
- Snapshot nema povijesne as-of oznake objave rezultata: pomična simulacija pretpostavlja dostupnost nakon dva dana, nije potpuna rekonstrukcija tadašnjeg izvora.
- Ova završna razdoblja sad su pregledana. Buduće podešavanje zahtijeva novo neovisno razdoblje za dokaz; ne ugađati model na zadnjim kolima i zatim tvrditi neovisan uspjeh.
- GitHub izdanje ranije nije imalo samostalni web runtime. Python analitika je samostalna (standardna biblioteka). Claude rad nije potvrđen, ne čekati za autorizirani samostalni nastavak.

## Sljedeći korak
Dopuniti izvorne rezultate i identitete za svih deset liga, odvojeno provjeriti službene završne rasporede/faze i posljednja kola. Nakon potpunijeg ulaza izraditi nove razvojne testove bez optimizacije na već pregledanom završnom testu. Dalje mjeriti doprinos faktora, kalibraciju i nesigurnost; visok postotak ne obećavati.

## Naknadni zahtjev — zamjene i Bugarska/Rumunjska
- Vlasnik je odobrio zamjene nepotpunih liga sljedećima po UEFA poretku, te posebno zatražio Bugarsku i Rumunjsku.
- Pregledan upstream europe tree: za BG i RO postoje 2023-24 i 2024-25, nema 2025-26 datoteka u pregledanom stablu. RSSSF ima sezonske preglede 2025/26, ali potpuna utakmična pokrivenost s datumima i prava za konkretan uvoz još nisu potvrđeni; nisu uvezeni.
- Norveška, Austrija i Škotska provjerene kao kandidati iz istog izvora; potpuna 2025/26 nije potvrđena. Ne zamijeniti nepotpun izvor drugim nepotpunim samo radi broja deset.
- Prvi izvještaj pilota uspješno objavljen: Sites commit 4c573386d8b4b16adc93bef84bd20ab5e93d72af; deployment appgdep_6ae25b4f02748191a69f9bea1967d807, succeeded. Naknadne upute za izbor zamjena još nisu implementirane u testirani skup.

## Važeća odluka vlasnika — bez Bugarske i Rumunjske
Korisnik je 28.10.2026. izričito odabrao nastavak bez Bugarske i Rumunjske. Obje izostaviti iz kandidata za zamjenu; ne čekati njihove podatke. Nastaviti redom po UEFA poretku i uključiti samo zamjenske lige s potvrđenim rezultatima po utakmicama, datumima i fazama za obje testne sezone. Prethodno navedena provjera BG/RO ostaje povijesni zapis, nije aktivna zadaća. Zamjenske lige još nisu potvrđene niti ubačene u već objavljeni pilot.

## Važeći nastavak — prošireni ciklus povijesnog učenja
- Vlasnik je nakon ranijih bilješki izričito odabrao ostanak na postojećih deset liga, bez zamjena. Nastaviti samo 1X2 i više/manje 2,5; prethodni plan zamjenskih liga nije aktivan.
- Provedeno 1.701 konfiguracija u analytics/expanded_search.py: dev prozori 2022/23 i 2023/24, učenje koeficijenata samo na prethodnim sezonama. Dodani domaći/gostujući učinak, snaga ranijih protivnika, forma, Elo i razmak ligaških utakmica uz napad/obranu. Nema taktičkih ni drugih vanjskih ulaza.
- Odabrano isključivo razvojnim Brierom: napad/obrana + Elo razlika; prozor 50, poluvrijeme težine 15, ridge 0,01, korekcija malih rezultata -0,1, temperatura 1. Pun model svih faktora bio je slabiji na razvojnim sezonama.
- Ponovna analiza istih 5.772 susreta iz 2024/25 i dostupne 2025/26: 1X2 52,10%; više/manje 2,5 56,64%; jedna najvjerojatnija ponuda 59,55%. Brier 0,21869; razvojno odabrana osnovna regresija na istim susretima 0,21977. Pojedinačni 1X2 pogodak osnovne regresije blago je viši (52,18%); ne tvrditi poboljšanje svih metrika.
- Ovo nije novi neovisan završni test: obje novije sezone već su viđene. Za novi dokaz potrebna je zaključana verzija i novi neviđeni ishodi. Ostaju djelomična pokrivenost, nedostatak postava/ozljeda/taktike/vremena/kvota i datumskih as-of oznaka.
- Arhivirani ciklus: data/experiments/20261028-expanded-v1/ (svaka postavka, zaključana konfiguracija prije audita, izvještaj, prognoze). Kompaktan UI app/expanded-summary.json. Skripta odbija prepisati završen eksperiment; za novi ciklus odabrati novu mapu. Stari pilot u data/reports/ ostaje sačuvan.
- Dodana usporedba skupina i izostavljanja, razvojni doprinos za 1X2 i golove, kalibracijske tablice, rezultati po sezonama/ligama i opisni tjedni bootstrap razlike Brier rezultata. To nije dokaz uzročnog utjecaja niti nesigurnost koja obuhvaća izbor među svim modelima.
- Jedanaest Python testova prošlo, uključujući vremensku izolaciju, granice treniranja, normalizaciju tržišta i neovisnost razvoja o naknadnoj promjeni audit ishoda. Preglednik za lokalni preview javio ERR_CONNECTION_REFUSED; vizualni QA nije potvrđen. TypeScript i produkcijsku izgradnju provjeriti prije objave.
- GitHub issue #1 i otvoreni PR-ovi pregledani: nema potvrde Claudeova preuzimanja ni otvorenih PR-ova. Samostalan rad nastavljen je bez čekanja.
- Završna provjera ovog ciklusa: TypeScript `tsc --noEmit` i produkcijski Sites build uspješni. Objavu potvrditi tek po odgovoru Sites alata.

## Potvrđena objava proširenog ciklusa
Sites verzija 5 uspješno je objavljena na https://matchlens-luka.lushlily1.chatgpt.site. Izvorni commit a39f0fd5cab6c425048a881f6d5005f8e430cec1; deployment appgdep_6ae25ed958dc81918af648b3d0c7d50d, status succeeded. GitHub istraživačka analitika i izvještaj spremljeni commitom 0d623027ed098ed445f58e0a665b74f317f8fcdf. Prijenos je ograničen na projektne datoteke i agregirane nalaze; ne sadrži platformski paket ni tajne. Buduće prognoze nisu aktivirane. Vizualni QA ostaje nepotvrđen zbog odbijene veze preview preglednika.

## Claude Code nastavak — 28.10.2026., oko 22:15 Europe/Zagreb
Sesija: https://claude.ai/code/session_01XjqfQVhHbKVrHjWEGhqkqh (ručno pokrenuta, ne preko `@claude`). Preuzimanje potvrđeno u issueu #1. Grana `claude/prospective-lock-ci`.

Potvrđeno (provjereno izvršavanjem):
- Repozitorij prije ovog rada nije imao GitHub Actions workflowe. Integracija na `@claude` nije postojala.
- Sirovi snapshotovi nisu bili u GitHubu, pa su 3 od 12 testova padala na čistom klonu. Ponovno su izgrađeni s OpenFootballa (CC0) i spremljeni u `data/openfootball/` i `data/upstream/`. Pohranjeni su kao JSON s indent=2, uz spajanje TXT dopuna.
  - 58/64 datoteka je bajt-identično manifestu.
  - 6 datoteka (2019-20 BE/FR/NL, 2024-25 ES/IT/TR) upstream je u međuvremenu promijenio, uz iste brojeve utakmica i rezultata.
  - Provjera: zaključani expanded-v1 ponovljen je točno iz ovih podataka (20.517 utakmica; audit Brier 0,21869063; isti koeficijenti; razvojni rezultat 0,21695284). Grid od 1.701 konfiguracije nije ponovno pokretan.
- `analytics/verify_snapshots.py` provjerava ili ponovno gradi snapshotove prema manifestu i prijavljuje razlike.
- 14 Python testova prolazi lokalno (Python 3.13, numpy 2.3.5, scipy 1.17.0). Novi testovi potvrđuju da buduće neodigrane utakmice ne ulaze u povijest.
- **Prospektivni test `data/experiments/20261028-prospective-v1/`:**
  - Zaključana konfiguracija expanded-v1; koeficijenti jednom naučeni na 18.905 utakmica s rezultatima prije 28.10.2026.
  - 67 prognoza zamrznuto prije početka utakmica od 29.10. do 4.11.2026. (7 liga).
  - SHA-256 dnevnika `eeaccee74f694b49bfc282e3ed84048a2abe65797741044770a773ce3d1731b8` objavljen je u issueu #1 (komentar 6480577279) kao vremenski žig poslužitelja.
  - Polje `source_lock` u lock datoteci ručno je skraćeno s apsolutne na relativnu putanju prije ikakvih ishoda. To je jedina naknadna izmjena.

Pripremljeno, nije testirano:
- `.github/workflows/claude.yml` (claude-code-action@v1). Koraci koje vlasnik mora napraviti osobno su u `docs/SURADNJA_GITHUB.md`: GitHub App, tajna `CLAUDE_CODE_OAUTH_TOKEN`, spajanje u `main`, probni komentar. Ne tvrditi da automatizacija radi dok run u kartici Actions ne uspije.
- `.github/workflows/tests.yml` za PR-ove: prvi run 40768475267 na commitu 094f98159bc1c8af114dc620b8c0cfb61f611a1e uspješan (success, 28.10.2026. 22:02 Europe/Zagreb), PR #2.

Otvoreno / prepreke:
- OpenFootball 2026./27. ima rezultate samo do 20.9.2026. (EN/IT/ES/DE/FR/PT/NL). Zato je svih 67 prognoza u skupini `stale` (39 dana). Potreban je svježiji dopušteni izvor rezultata. Football-Data.co.uk CSV ima svih 10 liga, ali licenca za javnu redistribuciju nije potvrđena: koristiti ga samo lokalno, bez spremanja sirovih podataka u javni repo.
- TR/GR/BE 2026./27.: TXT drugog formata (`Tim  2-2 (0-0)  Tim`) i sponzorski nazivi klubova (npr. „Atiker Konyaspor”). Treba parser i kanonsko mapiranje naziva prije uključivanja.
- Ocjenu raditi tek kad izvor objavi rezultate; tvrdnje tek nakon ≥200 ocijenjenih utakmica.

Sljedeći korak: svakih nekoliko dana pokrenuti `snapshot` i `predict --as-of <danas>` za nova kola (dodaje samo nove utakmice), a nakon objave rezultata `score`. Kriterij dovršenosti: ≥200 ocijenjenih prognoza i izvještaj odvojeno za `fresh` i `stale`.
