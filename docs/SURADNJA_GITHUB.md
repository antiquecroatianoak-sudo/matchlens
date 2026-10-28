# Razmjena zadataka ChatGPT ↔ Claude preko GitHuba

Stanje 28.10.2026., oko 22:10 Europe/Zagreb. **Automatsko pokretanje nije testirano i ne smatra se funkcionalnim.**

## Što je provjereno
- Prije ovog rada repozitorij nije imao `.github/workflows/` ni GitHub Actions workflowe (GitHub API: 0 workflowa). Raniji `@claude` komentari u issueu #1 zato nisu ništa pokrenuli.
- Claude je na ovom zadatku radio u ručno pokrenutoj Claude Code sesiji vlasnika: https://claude.ai/code/session_01XjqfQVhHbKVrHjWEGhqkqh

## Pripremljeno rješenje
`.github/workflows/claude.yml` koristi službenu akciju `anthropics/claude-code-action@v1` (primjer iz `examples/claude.yml` te akcije i https://code.claude.com/docs/en/github-actions). Pokreće se na komentar, review ili novi issue koji sadrži `@claude`. Claude zatim radi u GitHub Actions okruženju, odgovara komentarom i može otvoriti granu i PR. Sam komentar ili PR iz te sesije nije dokaz uspjeha; dokaz je uspješan run u kartici Actions.

`.github/workflows/tests.yml` na svaki PR i push na `main` pokreće Python testove. Ne treba mu nikakva tajna.

## Koraci koje vlasnik mora napraviti osobno
1. **Instalirati Claude GitHub App** samo za repozitorij `matchlens`: https://github.com/apps/claude (potreban je administrator repozitorija).
2. **Napraviti token pretplate:** lokalno u terminalu pokrenuti `claude setup-token`. To je dostupno uz pretplatu Pro, Max, Team ili Enterprise. Taj token troši postojeću pretplatu, ne naplaćuje se po API pozivu. Ne koristiti `ANTHROPIC_API_KEY`, jer se on naplaćuje po potrošnji.
3. **Dodati tajnu:** GitHub → matchlens → Settings → Secrets and variables → Actions → New repository secret. Naziv `CLAUDE_CODE_OAUTH_TOKEN`, vrijednost je token iz koraka 2. Token nikada ne pisati u komentar, issue ili datoteku.
   - Koraci 1–3 mogu se napraviti i odjednom naredbom `/install-github-app` u lokalnom Claude Code terminalu (traži prijavljen `gh` CLI).
4. **Spojiti PR s workflowom u zadanu granu `main`.** GitHub pokreće workflowe za `issue_comment` samo iz zadane grane.
5. **Probni test:** u issueu #1 napisati `@claude Potvrdi pokretanje kroz GitHub Actions i navedi run ID.` Zatim u kartici Actions provjeriti zeleni run „Claude Code”. Tek nakon toga upisati u `docs/STATUS.md` da automatizacija radi.

GitHub Actions minute su besplatne za javne repozitorije. Pokretanje troši kvotu pretplate iz koraka 2.

## Kako ChatGPT predaje zadatak
- ChatGPT objavi komentar u issueu ili PR-u koji sadrži `@claude` i jasan zadatak. Pravila: opseg samo MatchLens, bez tajni, upućivanje na `docs/STATUS.md`.
- Pravo pokretanja: korisnik koji je napisao komentar mora imati pravo pisanja u repozitoriju, a botovi su odbijeni ako nisu na popisu `allowed_bots`. Komentar koji ChatGPT objavi preko vlasnikova GitHub priključka trebao bi se voditi kao vlasnikov, pa bi trebao proći tu provjeru. **To je pretpostavka iz dokumentacije i nije testirano.** Ako ChatGPT objavljuje kao GitHub App ili bot, treba ga dodati u `allowed_bots`.
- Rezultat: Claude odgovara komentarom i/ili PR-om, a test `Testovi` mora proći. ChatGPT čita komentar, PR i `docs/STATUS.md`.
- Svaki rezultat mora navesti commit, provedene provjere i otvorene blokade. Odobrenje i spajanje PR-a ostaju vlasnikova odluka, osim ako vlasnik izričito ne odluči drukčije.

## Ograničenja
- Akcija radi u svježem GitHub runneru. Nema pristup ovoj Claude Code sesiji ni njezinoj memoriji, nego čita repozitorij (`CLAUDE.md`, `AGENTS.md`, `docs/`).
- Bez koraka 1–4 workflow se ne pokreće ili pada na autentikaciji. To nije greška koda.
