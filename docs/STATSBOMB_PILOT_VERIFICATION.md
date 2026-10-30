# StatsBomb pilot — provjera 30.10.2026.

Izravno provjereno preko GitHub pristupa izvornom repozitoriju `hudl/open-data`:
- `data/competitions.json`: 80 natjecanje/sezona zapisa.
- Njemačka Bundesliga 2023/24: `competition_id=9`, `season_id=281`.
- `data/matches/9/281.json`: **34 utakmice**; to NIJE kompletna sezona Bundeslige.
- Primjer: Union Berlin – Bayer Leverkusen, 06.04.2024., 0:1.

Zaključak: ovaj izvor je pogodan za istraživanje događaja, sastava i pojedinih taktičkih parametara, ali se ne smije zamijeniti za potpunu bazu rezultata ili koristiti sam za validaciju cijele lige. Prije modeliranja treba upariti utakmice s kanonskom bazom, potvrditi identitete i dostupnost podataka prije prognoze. **Nije izvršen produkcijski upis, treniranje ni završni backtest.** Skripta za lokalni pilot je dodana u ovom PR-u, ali izvršavanje u produkcijskom okruženju još nije potvrđeno.

Uvjeti izvora: https://github.com/hudl/open-data ; za objavu analiza potrebna je atribucija izvora. Komercijalna upotreba zahtijeva zasebnu provjeru uvjeta.
