# MatchLens — izvori i protokol testiranja (30.10.2026.)

Popis izvora iz korisnikove fotografije / razgovora, trajni projektni zapis. Status "kandidat" ne znači da je izvor integriran.

| Izvor | Podaci | Status i ograničenja |
|---|---|---|
| FBref | povijesna statistika, momčadi, igrači | kandidat; provjeriti uvjete pristupa, vremensku dostupnost i dozvole |
| Transfermarkt | transferi, ozljede, sastavi, tržišne vrijednosti | kandidat; provjeriti licenciju, robots pravila i datume objave |
| SoccerSTATS | forma, golovi, domaći/gostujući | kandidat; provjeriti uvjete i arhivske snimke |
| Understat | xG, xA, šutevi | kandidat; provjeriti dostupnost liga i dozvole |
| Football-Data.co.uk | rezultati, kvote, statistika | kandidat; posebna provjera uvjeta za automatizaciju i AI |
| Sofascore | sastavi, rezultati, statistika | kandidat; ne raditi masovni scrape bez dopuštenja |
| FotMob | sastavi, xG, rezultati | kandidat; ne raditi masovni scrape bez dopuštenja |
| StatsBomb Open Data | događaji, postave, odabrana natjecanja | kandidat; otvoreni podaci samo za pokrivena natjecanja, uz atribuciju i provjeru licence |

Dodatni ranije razmatrani izvori: OpenFootball (osnovni rezultati), Open-Meteo (vremenski podaci uz strogu provjeru vremenske dostupnosti), football-data.org (uvjeti API-ja).

## Protokol
- Obuhvat: deset vodećih europskih liga, posljednje dvije završene sezone.
- Walk-forward po kolima: za svako kolo koristiti isključivo podatke dostupne prije početka utakmice; rezultat otkriti tek nakon predikcije.
- Bez curenja informacija: bilježiti published_at, ingested_at, effective_at, source URL, ligu, sezonu, ID utakmice i dopuštenje za korištenje.
- Najviše 25% utakmica kola, jedan najbolji dopušteni tip po utakmici.
- Tipovi: 1, X, 2, over/under 2.5 uz kvotu >1.30; 1X i X2 samo uz dokumentirano izračunatu sintetsku kvotu >2.00.
- Jedna agregirana uspješnost (pogodci / odabrani tipovi), uz broj pogodaka i uzorak. Posebno evidentirati ROI ako su kvote valjane.
- Usporediti baseline i nove faktore na istim kolima; zadnji dio razdoblja držati netaknutim holdoutom.
- Nedostajuće povijesne snimke faktora ne nadomještati današnjim vrijednostima.
- Ne označavati izvor integriranim ili test pokrenutim bez stvarnog izvršavanja i zapisnika.

## Dodatni izvori sa screenshota Sports Data Campus (30.10.2026.)
Na fotografiji je popis 14 servisa. Već zabilježeni: FBref, Sofascore, FotMob, StatsBomb Open Data, Football-Data.co.uk, Transfermarkt i Understat. **Novi kandidati**:
- FootyStats.org — timske statistike, golovi, trendovi; provjeriti API, povijesni opseg i licenciju.
- Futbolme.com — rezultati, rasporedi i natjecanja; provjeriti dostupnost arhive i uvjete.
- API-Football — API za utakmice, statistike, sastave i ozljede; provjeriti cijene, povijesnu dubinu i plan.
- 5DollarFootballAPI — provjeriti aktualnu dostupnost, dokumentaciju, povijesne podatke i uvjete.
- PlayeRank (Wyscout) — napredni podaci igrača; provjeriti komercijalno licenciranje i povijesni pristup.
- WhoScored — statistika igrača i utakmica; provjeriti dozvoljeni pristup i povijesne snimke.
- Opta Analyst — analize i napredne statistike; provjeriti postoji li dozvoljen strukturirani izvoz.
Fotografija je korisnikov referentni popis, a ne dokaz da su podaci preuzeti. Bez potvrđenih prava i vremenskih oznaka ne uvoziti u backtest.
