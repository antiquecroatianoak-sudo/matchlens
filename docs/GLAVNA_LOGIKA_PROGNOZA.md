# MatchLens — obvezujuća specifikacija odabira prognoza (2026-10-30)

## Glavni cilj
Aplikacija ne predviđa svaki tip zasebno niti bira sve utakmice. Za svako kolo svake obuhvaćene lige automatski bira **25% utakmica** za koje procjenjuje da je ishod najpredvidljiviji. Za svaku odabranu utakmicu daje **točno jedan** tip iz skupa: 1, X, 2, više od 2,5 gola, manje od 2,5 gola, 1X, X2.

- Izbor utakmica i izbor tipa moraju biti **zajednički model/algoritam**, na temelju svih dostupnih provjerenih parametara koji su bili poznati prije prognoze.
- Za **svih pet ostalih tipova (1, X, 2, više 2,5, manje 2,5)** uvjet je kvota **strogo veća od 1,30**. Tip s kvotom 1,30 ili manjom ne smije ući u odabir. Kvota mora imati dokaz dostupnosti prije prognoze; bez valjane kvote tip je nedopušten.
- Za 1X i X2 izračunava se **sintetička fer kvota** iz vlastitih kalibriranih vjerojatnosti: 1/(P1+PX), odnosno 1/(PX+P2). Ti tipovi su dopušteni samo ako je izračunata kvota **strogo veća od 2,00**. To nije ostvariva kladioničarska kvota ni dokaz zarade.
- Rangirati sve **parove (utakmica, dopušteni tip)** prema predviđenoj vjerojatnosti uspjeha, uz kalibraciju i procjenu pouzdanosti. Za svaku utakmicu zadržati samo njezin najbolji dopušteni tip; zatim odabrati gornjih 25% utakmica po tom rezultatu. Izbjegavati preferiranje nekalibriranih tržišta samo zato što daju veće sirove postotke.
- Ako kolo ima broj utakmica koji nije djeljiv s četiri, politika zaokruživanja mora biti eksplicitna, stabilna i testirana (predloženo: najbliži cijeli broj, najmanje jedna utakmica za neprazno kolo). Ne miješati utakmice različitih kola pri odabiru.
- Na povijesnom testu simulirati odabir **prije početka kola** iz podataka tada dostupnih; ne birati 25% retroaktivno na temelju stvarnih ishoda. Zadržati jedan konačni izbor po utakmici.
- **Primarna metrika:** udio točnih izabranih tipova u svih odabranih 25% utakmica kroz testna kola. Prikazati broj kola, broj odabranih utakmica, pokrivenost, kalibraciju i rezultate po tržištu samo kao dijagnostiku, ne kao zasebne ciljeve.
- Trenirati zajednički sa svim stvarno dostupnim faktorima; nakon osnovnog testa raditi ablacijske analize i uklanjati faktore koji smanjuju rezultate na usporedivim vremenskim testovima.
- Ako nisu dostupni stvarni povijesni faktori i potvrđeno izvršavanje testa, ne predstavljati rezultat jednostavnog Poissonovog baselinea kao rezultat konačne aplikacije.

## Prioritet
Ova specifikacija **zamjenjuje prethodnu interpretaciju** u kojoj se sedam tržišta testira kao sedam zasebnih prognoza. Test je jedan: 25% utakmica kola, jedna najbolja prognoza po utakmici.
