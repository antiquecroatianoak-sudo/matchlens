# Dvostruka šansa uz kvotu najmanje 2,00

Izričita korisnikova uputa od 29.10.2026. proširuje raniji opseg. Uz 1/X/2 i više/manje 2,5 gola dodaju se isključivo:

- **1X:** pobjeda domaćina ili neriješeno.
- **X2:** neriješeno ili pobjeda gosta.

Uvjet vrijedi uvijek, uključujući obični Top10/Top50: stvarna kvota baš na odabranu dvostruku šansu mora biti >=2,00. Kvota 1,99, odsutna ili nevaljana kvota, kvota za drugi susret ili drugu ponudu ne prolazi. Ne izračunavati kvotu kao 1/p, ne prenositi kvotu čistog ishoda i ne dodavati opciju12 ili kombinacije s golovima. Regularno vrijeme ostaje pravilo obračuna.

## Izvedba

`analytics/double_chance.py` računa P(1X)=P(1)+P(X), P(X2)=P(X)+P(2), iz koherentne 1X2 distribucije. Te dvije ponude nisu međusobno isključive: obje pogađaju na remiju, pa se njihove vjerojatnosti međusobno ne normaliziraju. Adapter prima eksplicitne quote zapise i izostavlja ponudu bez prihvatljive kvote. Po istoj selekciji/izvoru uzima posljednju dostupnu valjanu kotaciju, a zatim provjerava prag: starija kvota2,00 ne ostaje prihvatljiva ako je novija pala na1,90. Iz više izvora s prihvatljivom kvotom bira najveću. `source` mora jednoznačno označavati izvor kotacije/kladionicu za tu ponudu.

Quote ulaz: `match_id`, `market: "Dvostruka šansa"`, `selection: "1X" | "X2"`, broj `odds`, ne-prazni `source`, `timestamp` s vremenskom zonom. Vrijeme kotacije <=vrijeme prognoze <početak susreta. Izlaz prenosi identitet kvote u `oddsMatchId`, `oddsMarket`, `oddsSelection`, `oddsSource`, `oddsTimestamp`. Provjera izvornog sadržaja, aktualnosti i roka važenja mora se odraditi u budućem pravom adapteru izvora. Sam ovaj matematički adapter ne dodjeljuje `verified`, kalibraciju ni validationId; takva potvrda zahtijeva stvarnu modelsko-tržišnu provjeru.

`app/prediction-ranking.ts` primjenjuje isti tvrdi uvjet prije sortiranja i deduplikacije. Za provjerene prognoze zahtijeva brojčanu kvotu, točnu vezu susreta/tržišta/selekcije, izvor i tada dostupnu vremensku oznaku s vremenskom zonom. Postojeći zahtjevi kalibracije, vremena početka i aktivne modelVersion ostaju. API i JSON uvoz ručnih trial zapisa također odbijaju1X/X2 ispod2,00; dnevnik ostaje ručni, bez provjerenog statusa. U obrascu je zasebna vrsta ponude, odabir1X/X2 i minimalna kvota2.

## Stvarna pokrivenost i rezultati

U ovom nastavku nije preuzet novi izvor kvota. Postojeća povijesna baza i arhivirani pokusi nemaju stvarne datirane kvote dvostruke šanse. Zato nema nove izmjerene nogometne točnosti, ROI-ja ili potvrde90% za ovaj uvjet. Veća teorijska vjerojatnost unije nije dokaz da postoji kvota>=2 niti dokaz isplativosti. Stari lockovi, pet ponuda i njihove stope ostaju povijesno nepromijenjeni. Za buduću usporedbu tržišta i promjenu strategije trebaju stvarni quote snapshotovi, odgovarajuća tržišna validacija i usporediv obuhvat; ne uspoređivati7ponuda s ranijih5 kao čisti lift.

Provjere pokrivaju inkluzivnu granicu2,00, nedostajuće/loše kvote, identitet ponude, objavu nakon prognoze ili bez vremenske zone, ručni uvoz i zaobilaženje pogrešnim tržištem, matematičke unije i obračun remija, te povlačenje stare kvalificirane kvote nakon pada nove ispod praga. Sintetički testovi ugovora nisu dokaz nogometne uspješnosti.
