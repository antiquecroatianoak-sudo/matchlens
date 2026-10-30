# Provjera stvarnog StatsBomb xG uvoza (2026-10-30)

Izvor: GitHub Actions run https://github.com/antiquecroatianoak-sudo/matchlens/actions/runs/41106556878

- 34/34 uspješno preuzetih datoteka utakmica; 0 pogrešaka.
- 137765 događaja, 68 zapisa klub–utakmica, 18 različitih klubova.
- Svaka utakmica ima po dva klupska zapisa.
- Prosječni xG po klubu/utakmici: 1.477979; raspon: 0.038901–4.301661.
- Bayer Leverkusen: 34 zapisa, prosječni xG 2.138097.
- Provjera: svih 68 xG vrijednosti su brojevi >= 0.
- Izvorni artefakt: statsbomb-event-pilot-41106556878 (GitHub Actions).

**Važno:** Ovo su post-match statistike. Izvorne event datoteke ne
potvrđuju kada je svaka utakmica prvi put objavljena. Stoga je broj
*potvrđeno prihvatljivih za prematch evaluaciju* zasad 0 (ne tvrdimo
da nijedan podatak nije bio dostupan). Nije izvedena usporedba
baseline/challenger niti tvrdnja o povećanju točnosti.

Sljedeći uvjet: provjereno vrijeme objave događaja i eksplicitna
kanonska mapa timova za svaki zapis; potom rolling prior-match xG,
isključivo kada available_at < prediction_at. Nakon toga evaluirati
iste utakmice, isti cutoff i top 25% po pouzdanosti, uz usporedbu s
baselineom i intervale pouzdanosti. Bez ovih uvjeta xG se ne smije
uključiti u produkcijske prognoze.
