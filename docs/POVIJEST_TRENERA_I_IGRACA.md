# Povijest trenera i igrača kroz klubove

## Zahtjev vlasnika, 29.10.2026.
Za budući susret pratiti trenera protiv istog protivničkog kluba i dok je vodio druge klubove. Pratiti izravne učinke napadača protiv određenih protivničkih igrača i nakon transfera. To je hipoteza za provjeru, ne pravilo da se isti učinak mora ponoviti.

## Implementirano
`analytics/person_matchups.py` računa vremenski ograničene kandidate obilježja iz dviju vrsta provjerenih činjenica. Kanonski identitet osobe ne sadrži trenutačni klub. Preslikavanja imena, identifikatora pružatelja i promjena klubova moraju biti potvrđena; nema automatskog spajanja samo po prezimenu. `record_id` je kanonski događaj, a `match_id` kanonski susret; duplikati istog događaja iz više portala ne predstavljaju novu potvrdu.

Za trenera se od stvarnih bodova oduzima očekivanje snage njegova tadašnjeg kluba, zamrznuto prije stare utakmice. Rezultat se dijeli s 3. Povijest protiv istog protivnika zadržava se nakon promjene kluba; odvojeno se broje susreti iz drugih klubova. To je prediktivni rezidual, ne dokaz uzročnog učinka trenera. Stari i novi taktika, liga, kadar i uloga ostaju zasebni kontekstualni faktori.

Za igrača se koriste samo zabilježeni izravni događaji s potvrđenim protivnikom. Sama istodobna prisutnost na terenu nije duel. Driblinzi, zračni dueli i drugi događaji ne smiju se nekritički zbrajati. Povijest se uspoređuje unutar vrste događaja i uloga napadača/branitelja, uz opću uspješnost napadača protiv drugih braniča i braniča protiv drugih napadača. Broj golova u utakmici nije sam po sebi dokaz da je jedan branič zaustavio napadača.

Svaka utakmica ima ograničen ukupni utjecaj, neovisno o broju događaja. Starost prepolovljuje težinu nakon 365 dana; zaglađivanje ima prior osam utakmica. To su početne istraživačke postavke, ne optimizirani parametri. Za oznaku dovoljne podloge traži se barem pet različitih utakmica; kod igrača i barem deset događaja usporedne povijesti za obje osobe. Na stvarnim podacima usporediti alternative tih postavki i uključiti nesigurnost. Dovoljan uzorak nije jamstvo prenosivosti učinka.

Očekivani parovi prije susreta imaju zajedničku vjerojatnost nastupa i očekivane minute preklapanja. Ne pretpostavljati neovisnost nastupa dvaju igrača. Nepoznate postave nisu potvrđene postave. Čuvati vrijeme informacije o treneru i postavi; kasnija potvrda ne ulazi u raniju prognozu.

## Podatkovni ugovor (JSONL)
Obje vrste: `record_id`, `match_id`, `source_id`, `team_id`, `opponent_id`, `occurred_at`, `available_at`. Vremena su ISO-8601 s vremenskom zonom; dostupnost rezultata ne može prethoditi događaju.

Trener: `coach_id`, `points` (0/1/3), `expected_points` (0–3), `baseline_generated_at`, `baseline_version`. Očekivanje mora biti izračunano prije stare utakmice, bez njezina rezultata.

Izravni duel: `attacker_id`, `defender_id`, `event_type`, `attacker_role`, `defender_role`, `success` (0/1), `pair_evidence: explicit_link`. Potrebna je provjera izvornih povezanih događaja; ne popunjavati branitelja prema blizini ili sastavu bez odgovarajućih podataka.

Cilj: `match_id`, `team_id`, `opponent_id`, `as_of`, opcionalni `coach_id` i pripadajući `coach_known_at`. Za parove: `lineup_known_at` i `expected_pairs`, svaki s identitetima, vrstom događaja, ulogama, `joint_participation_probability` i `expected_overlap_minutes`.

Pokretanje iz korijena:

    python -m analytics.person_matchups --coaches PROVJERENI_TRENERI.jsonl --duels PROVJERENI_DUELI.jsonl --targets CILJEVI.jsonl --output NOVI_EKSPERIMENT

Skripta odbija prepisati postojeću mapu. Sve izvore prije obrade treba provjeriti za dopuštenu uporabu i porijeklo. Ugovor nije dozvola za prikupljanje tuđih podataka.

## Što još nije uključeno u trening
Postojeći OpenFootball skup ima rezultate, ali ne i potvrđene kanonske trenere, sastave ili izravne parove događaja. U ovom ciklusu nije uvezen nijedan stvarni zapis trenera ili duela. Testovi koriste jasno sintetičke anonimne zapise isključivo za provjeru koda; ne daju postotak nogometnih pogodaka.

Prije novog postotka točnosti trebaju: izvor i prava uporabe, identiteti i vremenske oznake, audit pokrivenosti, spajanje obilježja s utakmicama, razvojna usporedba osnovno / +trener / +igrač / oboje i uklanjanje skupina na istim susretima. Za usporedbu poduzorka prikazati i osnovni model na tom istom poduzorku. Težine i parametre birati u ranijim segmentima; kasnije već pregledane sezone ostaju opisna ponovna analiza. Nedostatak podatka ostaje `null`, ne nulti ili pozitivan doprinos.
