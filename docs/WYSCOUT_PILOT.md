# Stvarni treneri i postave — retrospektivni pilot 29.10.2026.

Izvor: Pappalardo, Luca; Massucco, Emanuele (2019), Soccer match event dataset, figshare, https://doi.org/10.6084/m9.figshare.c.4415000 . Autorski članak: https://www.nature.com/articles/s41597-019-0247-7 . Licenca podataka CC BY 4.0: https://creativecommons.org/licenses/by/4.0/ . Mirror koenvo: https://github.com/koenvo/wyscout-soccer-match-event-dataset . Podaci su preuzeti, raspakirani, normalizirani i pretvoreni u izvedena obilježja. Licenca ovog skupa ne daje pristup komercijalnom Wyscout API-ju.

Stvarno uvezenih 1.826 ligaških susreta 2017./18.: EN380, FR380, DE306, IT380, ES380. SP i EURO iz arhive nisu korišteni. Kanonski ID utakmice, momčadi, trenera i igrača; datum UTC; početnih 11 i rezultat. Duplicirani susreti i nevaljane postave odbijaju se. `currentTeamId` nije korišten. Dostupnost ciljane postave/trenera prije utakmice nije arhivirana: izvor je objavljen 2019. Zato je ovo **ideal-information retrospektivni pokus**, a ne potvrđeni povijesni as-of backtest. Ne popunjava kadrovske podatke 2024.–2026.

Ulazni whitelist odvaja konačne golove, kartone i zamjene od obilježja ciljne utakmice. Povijest isključuje datum susreta i prethodna dva dana. Osnovno: golovi za/protiv kroz 5/20 prethodnih utakmica, Elo razlika, razmak zabilježenih ligaških susreta i liga. Dodatni trener: raniji bodovni rezidual prema zamrznutoj pre-match Elo referenci, promjena trenera, nedostajući identitet; isti protivnik tek uz pet prethodnih susreta. Referenca je fiksni heuristički Elo model, a ne dokaz potpuno uklonjenog utjecaja snage. Dodatni igrači: prosjek zaglađenih reziduala ranijih početnih nastupa, zadržavanje prethodne postave i nedostatak povijesti. To je povezanost osobe s momčadskim ishodom, ne individualna ili uzročna kvaliteta. Ne koristi uloge, xG ni dokazane izravne duele.

Četiri ablacijske skupine × tri regularizacije × dvije obitelji tržišta = 24 razvojna podešavanja. Učenje prije 1.1.2018. (645 susreta nakon embarga); razvoj siječanj–veljača (372); refit na podacima prije 27.2.; usporedba ožujak–svibanj (545 istih susreta). Standardizacija uči samo iz treninga. Regresija za 1X2 i više/manje 2,5 odvojena; odabir prema razvojnom log lossu, ne audit pogocima. Lock spremljen prije audit ocjenjivanja; nema ponovnog ugađanja prema ovim ishodima.

| Varijanta | 1X2 | Golovi | Najvjerojatnija ponuda | Pogoci / promašaji | Brier |
|---|---:|---:|---:|---:|---:|
| Osnovno | 53,94% | 55,78% | 57,43% | 313 / 232 | 0,215722 |
| + trener | 53,94% | 53,58% | 56,33% | 307 / 238 | 0,215575 |
| + postava | 53,21% | 54,68% | 56,15% | 306 / 239 | 0,216243 |
| Oboje | 54,13% | 52,48% | 54,68% | 298 / 247 | 0,216153 |

Trener daje vrlo malo niži Brier, ali manje pogodaka najbolje ponude; nema procjene statističke značajnosti ni dokaza korisnosti za budućnost. Nijedna skupina nije promovirana u glavni model. Ovo je drugi skup i drugi osnovni model: postotke ne uspoređivati kao lift s 59,86% na 2024.–2026.

U audit uzorku 21 zapis momčadi s trenerovom poviješću u drugom klubu; 403 sa starterom koji ima povijest iz drugog kluba. Dvije strane utakmice nisu neovisni susreti. Nula trener–protivnik zapisa doseže pet ranijih utakmica. Nula potvrđenih izravnih parova igrača. Dodatna sezona/dublja povijest i dopušteni povezani događaji potrebni su za izvorni zahtjev osobnih međudjelovanja. Ne spuštati minimum nakon pregleda rezultata radi prividnog poboljšanja.

Ponovljivost: ručno pribaviti `raw_data/matches.zip` iz navedenog mirrora, provjeriti SHA256 u `data/wyscout/manifest.json`, raspakirati sedam JSON datoteka u `data/wyscout/raw`. Pokrenuti `OPENBLAS_NUM_THREADS=1 python -m analytics.wyscout_pilot --output data/experiments/novi-nepostojeci-direktorij`. Izvorni ciklus se ne prepisuje; svi razvojni pokušaji, izbor, normalizacija i prognoze ostaju u privatnoj arhivi, javno su kod, manifest, zbirni izvještaj i lock. Testovi vremenskih granica koriste sintetičke ulaze; zasebna stvarna provjera pokrivenosti preskače se samo ako raw snapshot nije prisutan.

Sljedeće: više sezona s dopuštenim identitetima, dokaz dostupnosti postava i trenera prije prognoze, povezani izravni događaji, jača pre-match referenca te unaprijed zaključana nezavisna vremenska provjera. Cilj >90% nije postignut; nema aktualnih preporuka ili jamstva.
