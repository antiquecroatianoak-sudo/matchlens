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
