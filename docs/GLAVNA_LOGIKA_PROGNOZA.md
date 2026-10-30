# MatchLens — aktualna obvezujuća logika (2026-10-30)

## Povijesni test
- Obuhvatiti **sve dostupne lige**, cilj **najmanje deset**; ne ograničavati rangom ili državom.
- Koristiti pet tržišta: **1, X, 2, više 2,5, manje 2,5**. U ovom testu **bez kvota** i **bez 1X/X2**.
- Za svaku utakmicu izračunati pet vjerojatnosti i zadržati jedan najbolji tip.
- **Jedna globalna kvota od 25% utakmica** iz cijelog testnog skupa (ili zajedničkog vremenskog prozora pri prospektivnom radu), bez zasebnih kvota po ligi. Izbor može uključiti nula utakmica neke lige.
- Odabrati prema kalibriranoj procjeni pouzdanosti; usporediti kalibraciju između liga i tržišta. Zaokruživanje 25%: najbliži cijeli broj, polovica prema gore.
- Simulirati kronološki, samo s podacima poznatim prije prognoze; ne koristiti rezultate ili kasnije objavljene značajke za izbor.
- Prikazati **jednu ukupnu uspješnost** svih izabranih tipova, uz dijagnostiku po ligi/tržištu.
- Ako nema dovoljno valjanih prognoza za 25% skupa, prijaviti nedostatak pokrivenosti, ne nadopunjavati izmišljenim prognozama.

## Podaci i kontrola uvoza
- Provjeriti starije povijesne uvoze prije novog preuzimanja: u ranijem radu zabilježeno je **10 liga i 20.517 utakmica**, ali datoteke i njihova dostupnost u aktualnom repozitoriju još nisu potvrđene.
- U aktualnom PR #13 eksplicitno je potvrđeno šest snapshotova za pet liga i **2.112 utakmica**. Ne prikazivati to kao cjelokupnu povijest projekta.
- Prije novog uvoza utvrditi gdje su stariji podaci, njihove licence, identifikatore utakmica i pokrivenost; izbjegavati duplikate.
- Dodavati samo provjerljive, vremenski označene dodatne faktore; nedostajući faktori nisu nula.
- Jednostavni Poissonov test samo na rezultatima nije konačan test punog modela.

## Stvarno predviđanje
- Povijesne kvote uključiti tek u stvarnom režimu prognoziranja, kad postoje stvarne pravodobne cijene.
- Režim s kvotama i eventualnim 1X/X2 odvojiti od aktualnog pet-tržišnog testa. Nema automatskog vraćanja tih tipova u povijesni test.
