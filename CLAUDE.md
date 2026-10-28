# MatchLens — samostalni projekt

## Opseg i izolacija
Raditi isključivo u `antiquecroatianoak-sudo/matchlens`. Ne otvarati niti mijenjati kod, baze, ključeve, automatizacije ili Claude sesije drugih aplikacija. Vlasnik je 28.10.2026. izričito odobrio javni GitHub repozitorij. Ne objavljivati tajne niti osobne podatke. Ne mijenjati privatnost objavljene aplikacije.

## Obvezno početno čitanje
Pročitati `docs/PLAN_IZRADE.md`, `app/workspace.tsx`, `app/api/records/route.ts`, `db/schema.ts` i postojeću konfiguraciju. Provjeriti postojeće stanje prije implementacije; objavljeno sučelje nije dovršeni model.

## Prva isporuka
1. Provjeriti postojeće spremanje, uređivanje ishoda, brisanje, JSON uvoz/izvoz i izolaciju podataka korisnika. Zabilježiti što je stvarno provjereno i eventualne prepreke.
2. Izraditi katalog izvora po ligi i sezoni: službene lige/savezi, klubovi, statistika pojedinaca, događaji/prostorni podaci, vrijeme, mediji i kvote. Provjeriti pristup, pokrivenost i uvjete; ne prikazivati zamišljeni priključak kao aktivan.
3. Implementirati jedan provjereni povijesni uvoz s kanonskim identitetima, deduplikacijom, porijeklom podataka, vremenskim oznakama, ponovljivim uvozom i izvještajem kvalitete. Pilot izabrati prema dostupnim podacima.
4. Uspostaviti osnovni model i vremensko testiranje prije dodavanja složenijih taktičkih interakcija. Sve dodatne faktore iz plana zadržati u opsegu faznog razvoja.

## Pravila modela i prikaza
- Cilj je usporediti tržišta i pronaći stabilan prediktivni doprinos, ne unaprijed obećati pobjednika ili dobit.
- Odvojiti snagu i okolnosti od dodatne taktičke korekcije; navesti nesigurnost procjene.
- Uključiti igrače i uloge, profil trenera kroz klubove, prioritete natjecanja, vrijeme i teren te pouzdano označene medijske informacije o atmosferi.
- Za povijesnu prognozu koristiti samo podatke dostupne u tadašnjem trenutku; stvarno vrijeme nije zamjena za tada dostupnu vremensku prognozu.
- Izbor tržišta/modela i konačni test moraju koristiti odvojena vremenska razdoblja. Čuvati točnu kvotu, granicu, vrijeme i pravila obračuna.
- Ne izmišljati podatke, vjerojatnosti, izmjerenu točnost ili preporuke. Bez dovoljne podloge prikazati da nema preporuke.
- Hrvatsko, pregledno, responzivno sučelje. Jasno razlikovati ručni scenarij, prototip i provjereni model.

## Izvještaj nakon rada
Navesti izmijenjene datoteke, konkretno ponašanje, provedene provjere, stvarno povezane izvore i preostale blokade. PR/issue ili ovaj dokument ne znače da je Claude pokrenut. Ne objavljivati status rada bez dokaza izvršenja.
