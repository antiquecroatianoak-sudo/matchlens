# MatchLens — zadnje potvrđeno stanje

Ažurirano: 28.10.2026. (Europe/Zagreb).

## Glavni plan
Kanonski plan: docs/PLAN_IZRADE.md. Obvezan početak rada: AGENTS.md. Upute za Claudea: CLAUDE.md.

## Potvrđeno
- Vlasnik je odobrio zaseban javni repozitorij antiquecroatianoak-sudo/matchlens. Objavljena aplikacija ostaje privatna.
- Preneseni su MatchLens sučelje, API funkcionalnosti, shema, razvojni plan i upute. Prvi prijenos: 65d7316728432a2b8985953e09f899ea0ef65fd8.
- Platformski hosting paket nije prenesen nakon odbijanja sigurnosne provjere. Izabran je uži prijenos projektnih datoteka. Repo zato još nije samostalno pokretljiv: nedostaju razvojno okruženje i integracije baze/autentikacije.
- Streaming CSV→SQLite uvoz i test dodani su commitom b36f1920d8c26bb0db24c9460d9b5e92f93518d9. Lokalno je prošao python -m unittest discover -s tests -v: 12.001 sintetički zapis, ponovljivi uvoz bez duplikata, ispravak rezultata, odbijanje neispravnog retka. To nije dokaz stvarnih uvezenih utakmica niti web-integracije.
- Zadatak za Claudea objavljen je na https://github.com/antiquecroatianoak-sudo/matchlens/issues/1. Pri posljednjoj provjeri komentara nije bilo odgovora. Preuzimanje i pokretanje Claudea nisu potvrđeni.
- Vlasnik je zatražio da se plan trajno održava i nadograđuje te čita pri svakom nastavku rada.

## Još nije potvrđeno ili dovršeno
- Automatski izvori, povijesni podaci i trenirani model nisu povezani.
- Samostalno pokretanje GitHub verzije nije provjereno.
- Aktivna Claude integracija u ovom repozitoriju nije potvrđena. Sam @claude spomen nije dokaz pokretanja.

## Sljedeći koraci
1. Provjeriti issue #1 i eventualne nove PR-ove/odgovore; ne slati duplicirani zadatak.
2. Razriješiti način stvarnog preuzimanja od strane Claudea. Ne koristiti kanale drugih aplikacija. Ne čekati ga za neovisni, već odobreni lokalni rad.
3. Dovršiti samostalno razvojno okruženje i provjeru API-ja, autentikacije i izolacije korisnika.
4. Provjeriti izvore i njihove uvjete, pokrivenost i stvarni dohvat; zatim povezati prvi povijesni pilot.
5. Razvijati osnovni model i vremenski odvojenu evaluaciju prema kanonskom planu. Ne izmišljati prognoze ni uspješnost.

## Dopuna: provjera izvora
Izvještaj docs/IZVORI_PROVJERA_2026-10-28.md spremljen je commitom 843844fd501c420f93e01de30de9798757ff6e5c i objavljen kao dopuna issuea #1. Uspješno probno dohvaćeni: 380 susreta EPL 2024/25 iz Football-Data.co.uk, StatsBomb katalog s 80 kombinacija natjecanja/sezone i Open-Meteo uzorak 24 satna zapisa. To nisu podaci integrirani u aplikaciju. SofaScore nije potvrđen dopušteni masovni izvor; puni uvjeti StatsBomb licence i ostali faktori tek slijede. Sljedeći podatkovni korak je CSV adapter uz provjeru vremenske zone, identiteta i nedostajućih vrijednosti. Glavni plan već sadrži odobrenu pomičnu povijesnu provjeru.
