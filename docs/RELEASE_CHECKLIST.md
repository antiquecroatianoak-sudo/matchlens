# MatchLens release readiness

Production release is blocked until all gates below are verified with evidence.

## CI
- [ ] GitHub Actions `matchlens-build.yml` has a successful run on the exact release commit.
- [ ] `npm run typecheck` and `npm run build` pass.
- [ ] Commit a reproducible `package-lock.json`; change workflow install to `npm ci`.
- [ ] Resolve warnings/errors before release; do not treat an absent CI run as success.

## Private deployment
- [ ] Deploy the Next.js app to an HTTPS host with server-side Node runtime.
- [ ] Set private environment variables in the host: `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_ROLE_KEY`, `MATCHLENS_ALLOWED_USER_ID`.
- [ ] Never put the service-role key in a `NEXT_PUBLIC_` variable or commit secrets.
- [ ] Confirm Supabase Auth owner ID is the intended user.
- [ ] Run `node scripts/check-deployment.mjs https://ACTUAL_HOST` and record HTTP outcomes.
- [ ] Test actual owner login, refresh, logout and denial of a different account without exposing passwords.

## Forecasts and release decision
- [ ] Verify data reads and date cutoffs against Supabase in production.
- [ ] Validate the 84-factor model separately on pre-match, out-of-sample data before enabling it.
- [ ] Record deployment URL, exact commit SHA and test evidence.
- [ ] Do not announce a live release until HTTPS endpoint and authenticated flows have been verified.
