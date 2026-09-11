# Troubleshooting

## `node` is missing

The skill stays on the default tier automatically — `discover.sh` and `fetch.sh` only need
bash/curl/sed/grep/awk, so a scan still runs and still writes a full briefing. Screenshots and
real LinkedIn ad extraction are unavailable until `node` is on PATH. To add the deep tier,
install **Node 20 or newer** — Playwright 1.63.0 declares `engines.node >= 20`, so an older
Node will not install it cleanly — then follow the Playwright step below. `node -v` older than
20 is treated the same as `node` missing: the run falls back to the default tier and says so
once.

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
already blocking you) and the briefing's Data notes flag it.

**The deep tier will not recover the content.** A real browser is less likely to be blocked
than a plain curl fetch, so it is worth a try — but all `scan.mjs` does on a competitor's own
site is take a homepage screenshot. It extracts no title, h1, meta description, body text or
links, so it cannot supply a single field the 403 cost you. What it buys you is an image of
the page that a person can read by eye.

So: if the fields matter, check the site manually and fill them in by hand. Turn on the deep
tier if you want the screenshot (and the LinkedIn ad read, which is unaffected by the site
blocking you), not as a way to get the page's copy back.

## Locale leakage in fetched content

If a competitor's site geo-detects and serves the wrong-language version, pin the locale
explicitly in `competitor-intel/config.json`'s `locale` field.

`SKILL.md` threads that value into both tiers. The default-tier scripts read it from the
`FETCH_LOCALE` environment variable and send it as the `Accept-Language` header on every curl
request (default `en-US` when unset); `discover.sh` passes it down to `fetch.sh`, so setting it
once on the `discover.sh` call covers the nav fetch too. The deep tier's `scan.mjs` takes the
same value via `--locale` and applies it as the browser context's locale. Set it per project,
not globally — different competitors in different projects may need different locales.

To pin it for a one-off manual run:

```bash
FETCH_LOCALE='de-DE' bash scripts/fetch.sh 'https://example.com/' 3000
```

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

Two consequences of the same unobserved markup, worth knowing before you quote anything:

- **An ad's `headline` is a leading excerpt, not a headline.** `headline` (120 chars) and
  `body` (300 chars) are both slices of the same card `textContent`, because there is no
  verified selector for a card's headline element. So `new_ad_headlines` diffs 120-character
  text blobs, and what a briefing quotes under "Ad activity" is an excerpt of an ad, not its
  headline. Read it that way.
- **`count` and `ads[]` can disagree.** `count` is every card found on the page; `ads[]` is
  capped at 25. For a competitor running more than 25 ads, `ad_count_delta` can move with no
  matching `new_ad_headlines`.

## Surface verification

| Surface | Scripts run? | Verified on | Notes |
|---|---|---|---|
| Claude Code CLI | yes | 2026-09-11 | Windows 11, Git Bash, curl 8.17.0 |
| Claude Desktop | unverified | — | Shell availability not confirmed in official docs |
| Codex | unverified | — | `agents/openai.yaml` shipped; execution untested |
