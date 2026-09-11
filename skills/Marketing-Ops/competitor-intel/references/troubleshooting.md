# Troubleshooting

## `node` is missing

The skill stays on the default tier automatically — `discover.sh` and `fetch.sh` only need
bash/curl/sed/grep/awk, so a scan still runs and still writes a full briefing. Screenshots and
real LinkedIn ad extraction are unavailable until `node` is on PATH. To add the deep tier,
install Node (any current LTS), then follow the Playwright step below.

## Playwright is missing (deep tier)

`node` being on PATH is not enough — the deep tier also needs its own dependencies installed
once, from inside the skill folder:

```bash
cd scripts/deep
npm install
npx playwright install chromium
```

The Chromium download is about 310 MB. If `scripts/deep/node_modules` doesn't exist, the skill
falls back to the default tier for that run and says so once, rather than failing the scan.

## 403 / 429 on a competitor's site

Recorded as an entry in that competitor's `errors[]`, never silently dropped. The scan skips
the rest of that competitor's subpages for the run (no retry storm against a site that's
already blocking you) and the briefing's Data notes flag it. Two ways forward: try the deep
tier (a real browser is less likely to be blocked than a plain curl fetch), or check the site
manually.

## Locale leakage in fetched content

If a competitor's site geo-detects and serves the wrong-language version, pin the locale
explicitly. The default-tier scripts take it from `competitor-intel/config.json`'s `locale`
field; the deep tier's `scan.mjs` takes the same value via `--locale` (default `en-US`). Set it
per project, not globally — different competitors in different projects may need different
locales.

## Empty LinkedIn Ad Library results

Before assuming a competitor really runs zero ads, check the third field in
`competitor-intel/competitors.md` (`Name | https://url/ | linkedin-account-name`). The Ad
Library is searched by LinkedIn company/account name, which frequently differs from the
marketing brand name or domain — a mismatch here silently searches the wrong account and comes
back empty. If that field is blank, the skill defaults it to the company name, which is often
wrong. Set it explicitly.

## LinkedIn ad extraction — unverified against real markup (read this before trusting a `0`)

**This has never been confirmed against a real, unblocked LinkedIn Ad Library page.** Every
attempt during development hit a 403 block before the page rendered, so the card selectors and
the "no ads" empty-state markers in `scripts/deep/scan.mjs` are a best guess, not something
observed working. The code is written to fail closed: if the page doesn't clearly show either
ad cards or a recognizable empty state, it's recorded as an entry in `errors[]`, never as
`count: 0`. That means a `0` you see in a briefing should be genuine — but treat it with a
little more skepticism than the rest of the report, and if `errors[]` mentions the LinkedIn ad
library, that error may reflect blocking rather than the competitor genuinely running no ads.
Don't read silence there as "no ads."

## Surface verification

| Surface | Scripts run? | Verified on | Notes |
|---|---|---|---|
| Claude Code CLI | yes | 2026-09-11 | Windows 11, Git Bash, curl 8.17.0 |
| Claude Desktop | unverified | — | Shell availability not confirmed in official docs |
| Codex | unverified | — | `agents/openai.yaml` shipped; execution untested |
