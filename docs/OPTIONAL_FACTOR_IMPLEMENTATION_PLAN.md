# MatchLens — plan provedbe novih komponenti

Razdoblje: **2024-10-30 do 2026-10-30**. Ne koristiti starije utakmice za treniranje, kalibraciju ni povijesnu provjeru.

## Obvezni redoslijed
1. Uvesti utakmice grupno iz dozvoljenih izvora i spremiti izvještaj s brojem stvarno preuzetih zapisa. Ne izmišljati nedostajuće podatke.
2. Uskladiti identitet utakmice, datum, vrijeme početka u UTC-u i stadion. Dvosmislene podudarnosti ostaju neriješene.
3. Potvrditi koordinate stadiona uz izvor i preuzeti vremensku prognozu koja je bila dostupna prije utakmice; naknadno opaženo vrijeme ne koristiti kao prediktor.
4. Za svaku od osam skupina (weather, injuries, lineups, tactics, player_stats, xg, odds, pitch) izbrojiti: ukupno utakmica, prisutne podatke, potvrđeno dostupne prije početka, nedostajuće i nepotvrđene.
5. Testirati svaku skupinu zasebno na istim utakmicama kao osnovni model, kronološki, bez curenja budućih informacija; izmjeriti razliku i nesigurnost.
6. Uključiti u aktivne prognoze samo skupine s potvrđenim poboljšanjem i prihvatljivom pokrivenošću. Nedostajuće vrijednosti ne smiju se predstavljati kao poznate.
7. Provjeriti GitHub Actions, izvršene uvoze i stvarne zapise u bazi prije tvrdnje da automatika radi. Tek nakon uspješnih provjera objaviti.

## Trenutačno poznato
- Postojeći model koristi 84 faktora; osam novih skupina nisu potvrđene kao aktivne.
- Skripta `scripts/audit_optional_factor_coverage.py` postoji, ali rezultati stvarnog izvršavanja nisu potvrđeni.
- Uvoznici za utakmice i vrijeme postoje; potpuna veza stadion–koordinate–UTC–vremenska prognoza nije potvrđena.
- GitHub workflow za metapodatke postoji na razvojnoj grani; to nije dokaz uspješnog uvoza u glavnu bazu.
- Ne koristiti starije podatke ni tvrditi da su testovi prošli dok se ne potvrdi njihov rezultat.

## Kriterij završetka
Objaviti stvarne brojke pokrivenosti po skupini, usporedni kronološki test s osnovnim modelom, popis uključenih/odbijenih skupina i potvrdu uspješnog automatskog unosa u bazu.
