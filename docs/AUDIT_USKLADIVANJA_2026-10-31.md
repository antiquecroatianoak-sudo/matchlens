# Usklađivanje MatchLens koda s važećim pravilima — 31.10.2026.

Provjeriti cijeli tok od izvora, identiteta susreta, povijesnih obilježja, treniranja, validacije i selekcije do sučelja. Važeći prioritet: docs/KANONSKA_PRAVILA_ODABIRA_2026-10-30.md i docs/UVJET_11_PARAMETARA_2026-10-30.md; raniji kontradiktorni dio docs/PLAN_IZRADE.md nije operativno pravilo.

## Obavezni kriteriji
- Postojećih deset liga; bez Bugarske i Rumunjske.
- Analizirati sve utakmice kola, preporučiti najviše 25% susreta, najviše jedan konačni tip po susretu.
- Tipovi 1, X, 2, over 2.5, under 2.5 uz stvarnu datiranu kvotu >1.30; 1X i X2 samo uz sintetičku kvotu >2.00 jasno označenu kao teorijsku, nikad kao dostupnu tržišnu ponudu.
- Prije valjanog velikog testa najmanje 11 stvarnih prematch obilježja po prognozi, vremenski provjerljivih; NULL nije nula.
- Razvoj, izbor, kalibracija i novi neviđeni test odvojeni. Sezone 2024/25 i 2025/26 više nisu neviđeni test.
- Izračunati jedinstvenu uspješnost konačno odabranih tipova, obuhvat, promašaje, Brier/kalibraciju i nesigurnost.
- Ne prikazivati neprovjerene modele, izmišljene kvote ili simulacije kao stvarne preporuke.

## Nalaz pri pregledu
app/prediction-ranking.ts trenutačno sortira sve verificirane prognoze po vjerojatnosti, bez grupiranja po kolu i bez ograničenja 25% / jedan tip po utakmici. app/workspace.tsx prikazuje Top 10, Top 50 i 2.00+ iz istog rangiranja. To je suprotno novijim kanonskim pravilima za konačne preporuke.

## Implementacijski redoslijed
1. Uvesti jedinstven kanonski selector za prihvatljivost kvota, jedinstvenu ponudu po susretu, skup kola i limit floor(0.25 * broj svih susreta kola); ako su manje od četiri susreta, ne birati nijedan.
2. Jasno razdvojiti analizirane susrete, prihvatljive prognoze, konačno odabrane i isključene uz razlog; bez zaobilaženja ograničenja kroz Top 50 ili 2.00+.
3. U sučelju prikazati sve analizirane utakmice kola, izvore, datum osvježavanja, broj stvarnih obilježja, nedostajuće podatke, model/verziju, vjerojatnost, stvarnu ili sintetičku kvotu, razlog odabira ili odbijanja, te ukupni rezultat povijesnih testova.
4. Dodati testove rubnih slučajeva: 3/4/7/8 susreta, višestruke ponude istog susreta, kvote točno 1.30/2.00, nedostajuće kvote, NULL parametri, nepoznata liga i odgođeni susret.
5. Ne mijenjati produkciju i ne spajati PR #39 dok se ne provjere regresije i stvarni dry run.