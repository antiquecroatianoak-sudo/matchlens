# Glavna strategija: odabrana četvrtina kola

Korisnik je 29.10.2026. izričito promijenio glavni način rada: preporuke se odnose na najviše25%utakmica svakog kola, odabranih prije početka. Sve utakmice i dalje služe učenju i kontroli kvalitete; puni skup nije glavni popis preporuka. Jedinica je liga+sezona+oznaka kola, ne dan. Budžet je floor(broj utakmica cijelog poznatog kola/4), uključujući utakmice bez ishoda i bez dovoljno prognoznih podataka. Od8biramo2, od10biramo2, od12biramo3; postotak nije uvijek točno25%. Ne popunjavati kvotu izmišljenim ili nedovoljno provjerenim prognozama.

## Stvarni povijesni test

analytics/round_quarter.py prvo zamrzava sve obilježje svakog susreta u kolu na povijesti strogo prije najranijeg datuma kola minus dva dana. Nedjeljna prognoza ne smije koristiti petkov rezultat iz istog kola. Napad/obrana/Elo/forma i razmak ligaških utakmica računaju se iz iste takve zamrznute povijesti. Datumi budućih susreta mogu biti poznati iz snapshot rasporeda; arhivirana stvarna dostupnost takvog rasporeda nije dokazana. Refiti koeficijenata nasljeđuju sezonsku/tromjesečnu politiku aktivnog osnovnog modela i ne smiju koristiti podatke nakon pre-round cutoffa.

Za svaki susret jedna najvjerojatnija ponuda iz pet izvornih tržišta. Devet pravila ranga: vjerojatnost + w×razlika dvije najveće vjerojatnosti unutar izabrane obitelji tržišta; w=0,-0,2,-0,1,0,05,0,1,0,2,0,3,0,5,1. Izbor po jednako ponderiranoj točnosti odabira dviju razvojnih sezona2022/23i2023/24. Razvoj je odabrao0,05; lock spremljen prije audita2024/25–2025/26. Sve razvojne konfiguracije sačuvane, nisu prepisivane. Audit je već viđen u drugim pokusima, a osnovne postavke ranije birane na obje razvojne sezone: ovo je istraživački retrospektivni poligon, ne novi neovisan dokaz.

| Usporedba | Odabrano | Ocijenjeno | Pogoci | Promašaji | Bez ishoda | Točnost |
|---|---:|---:|---:|---:|---:|---:|
| Sve usporedive zamrznute prognoze |6242|5771|3457|2314|471|59,90%|
| Četvrtina: osnovni rang po vjerojatnosti |1316|1219|902|317|97|74,00%|
| Četvrtina: razvojno odabrana dodatna težina0,05 |1316|1219|897|322|97|73,58%|

Dodatno podešavanje nije nadmašilo osnovni rang, pa aktivna politika ostajew=0. To je zadržavanje unaprijed definirane reference, ne promocija nekog naknadno izabranog audit pobjednika. Pet pogodaka razlike nije dokaz statističke značajnosti. Novi raspon i populacija ne uspoređuju se kao čisti lift s ranijih59,86%koji su imali prognozu prije svakog pojedinog susreta. Ovdje je puni usporedivi frozen skup59,90%;74,00%je odabrani lakši skup.

Izvorni audit ima6346utakmica. Dovoljno povijesti za6242prognoze;104bez dovoljno podloge u ovom strožem načinu. Odabrano1316/6346=20,74%izvornog skupa. Zaokruživanje i nepotpuni izvorni raspored znače manje od25%. Obuhvat među raspoloživim prognozama je21,08%. Oba imenika prikazana. Nepoznati ishodi nisu izbačeni prije odabira.1X/X2nisu u ovoj povijesnoj stopi jer nema stvarnih prethodnih kvota>=2,00; ne uključivati matematičku uniju bez korisnikova kvotnog uvjeta.

## Izvedba aplikacije

app/quarter-policy.json označava glavni način round-quarter-v1,ratio0,25,w0. Središnji registar osnovnog modela upućuje na tu politiku. app/prediction-ranking.ts ima čistu funkciju createRoundQuarter: cjeloviti provjereni raspored kola s objavom prije sadašnjeg trenutka, jedinstveni ID-evi i početci s vremenskim zonama, zamrzavanje strogo prije prvog početka, samo validirane prognoze aktivnog modela koje se poklapaju s terminima rasporeda. Po susretu bira jednu najbolju ponudu; ne više različitih susreta od budžeta. Kvotni uvjet dvostruke šanse vrijedi i ovdje.

API app/api/quarter-selection/route.ts čita isključivo vlasnikove interne round_schedule(predviđen verified izvorni raspored)i prediction zapise. Prije prvog početka pokušava izraditi snapshot; ključ je vlasnik+liga+sezona+kolo. D1 onConflictDoNothing i prethodna provjera sprječavaju prepisivanje pri ponovnom pozivu ili promjeni modela. PATCHveć odbija sve što nije ručni trial; DELETEsada odbija quarter_selection; javni POSTkinds ne prihvaća managed predikcije/rasporede/snapshote. Stara verzija modela ostaje dio već zaključanog kola; nova se koristi za sljedeće nezaključano kolo.

Oba glavna rangiranja čitaju samo zamrznute snapshotove. Nema fallbacka na100%ostale utakmice i nema nadopunjavanja nakon prvih rezultata. Istekle/počete prognoze prestaju se prikazivati, ali ostaju u revizijskom snapshotu; ne zamjenjuju se novima. Pri otvaranju aplikacije klijent poziva endpoint za pokušaj zamrzavanja i učitava odabir. Ne postoji uključeni pozadinski servis ili raspored kontinuiranog istraživanja.

Trenutačno nema aktivnog provjerenog izvora aktualnih rasporeda i živih prognoza. live_recommendations_enabledostajefalse; capture vraća awaiting_validated_predictions, glavni popis ostaje prazan bez takvih ulaza. Ovo nije dozvola izmišljanja sastava/kvota/rasporeda ili slanja ručnih zapisa kao modelskih potvrda. Povijesni poligon i njegovih74,00%su stvarno izračunati i prikazani u aplikaciji; još nema neovisno potvrđenih budućih74%ili90%.
