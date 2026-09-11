---
name: competitor-intel
description: Scan competitor websites and ad libraries, detect what changed since the last scan, and write a competitive briefing. Use when the user says "/competitor-intel", "competitor scan", "what are our competitors doing", "competitive intelligence", "competitor briefing", or asks to track a competitor's website or ads over time. First run walks through a short intake that stores company and competitor details in a competitor-intel/ folder in the current project — no company data lives in the skill. Works with no dependencies (curl); adds screenshots and LinkedIn ad extraction when Node and Playwright are available.
---

# Competitor Intel

Scans competitor websites (and, at the deep tier, LinkedIn ad libraries), diffs the result
against the last scan, and writes a briefing a person actually reads. Everything the skill
learns about a company lives in a `competitor-intel/` folder inside the current project — never
in this skill folder, never in any repo this skill ships from.

## Routing

Check for `competitor-intel/company.md` in the current working directory.

- Missing → run **Intake**.
- Present, user said `scan` or gave no argument → run **Scan**.
- Present, user said `setup` → re-run **Intake** against the existing files (confirm before
  overwriting).
- Present, user said `report [run-id]` → run **Report** (no re-scraping — read the existing
  `runs/<run-id>/snapshot.json` and `changes.json`, or the latest run if `run-id` is omitted,
  and regenerate `briefing.md` from them per `references/briefing-format.md`).

## Intake

**Always ask the intake question, even when the project looks pre-loaded and the setup seems
obvious.** Do not infer company or competitor details from the repo, from CLAUDE.md, or from
earlier conversation and skip straight to writing files. The user's own words — how they name
their competitors, what they think changed, which one worries them — shape the whole briefing
downstream, and skipping the question throws that away even when you could technically guess
right.

Ask first, before anything else:

> "Setting up competitor tracking. Do you want to point me at files you already have (a
> competitor list, positioning doc, past research), or start from scratch — one question at a
> time?"

Offer this as an AskUserQuestion with two paths:

**(a) Point me at files.** Never assume a `competitor-intel/` or context folder already holds
the right thing. Scan the current launch directory for likely candidates (a competitor list,
CLAUDE.md/AGENTS.md, a `context/` folder, anything with "competitor," "positioning," or
"research" in the name). List what you found by filename only — don't read contents yet — then
ask the user to confirm one of: use these / redirect me to other files / paste it instead /
none of this, start from scratch. Wait for the answer, then read only what was approved.

**(b) From scratch.** Ask one question at a time, in this order:
1. Company name and URL (this is *your* company, for framing — not tracked as a competitor).
2. Competitors to track: name + URL for each.
3. For each competitor, the LinkedIn account name — **but only ask this when it would differ
   from the company name.** State why when you ask: a name-similar company on LinkedIn is an
   easy false match, and matching the wrong account silently pollutes the ad data with someone
   else's ads with no signal that it happened. If the company name is a safe-enough guess for
   the LinkedIn handle, don't force the question — confirm the guess instead.

From the answers, write:

**`competitor-intel/company.md`** — the user's own company name, URL, and any framing notes
they gave.

**`competitor-intel/competitors.md`** — one line per competitor, this exact format:

```
- Name | https://url/ | linkedin-account-name
```

**`competitor-intel/config.json`** — this exact default, before any user override:

```json
{ "tier": "auto", "maxSubpages": 10, "locale": "en-US", "lastRun": "" }
```

Then, regardless of which path was taken, check for the deep tier: is `node` on PATH? If yes,
offer it — explain that the deep tier adds screenshots and real LinkedIn ad extraction via
Playwright, and that turning it on means running `npm install` and `npx playwright install
chromium` in the skill's `scripts/deep/` folder, which downloads about 150 MB. Only do this
after the user says yes. If `node` is not on PATH, or the user declines, stay on the default
tier — `tier: "auto"` will still resolve to default at scan time (see Scan, and Error handling
below).

## Scan

You are operating autonomously during a scan. The user is not watching in real time. For
reversible steps that follow from the scan request, proceed without asking. Stop only for the
deep-tier install (downloads ~150 MB) and for anything destructive.

The fetch loop below is mechanical and cheap — a script does the extraction, you just batch the
calls and file the output. Don't spend judgment there. Save your attention for the briefing:
that's the one artifact a person reads, and it's where materiality calls, wording, and the
Quoting rule actually matter.

Procedure:

1. Read `competitor-intel/config.json` and `competitor-intel/competitors.md`.
2. Resolve the tier: `tier: "auto"` means deep if `node` is on PATH **and**
   `scripts/deep/node_modules` exists; otherwise default. If the config says `"deep"` but that
   check fails, fall back to default and say so once (see Error handling).
3. Per competitor, run `scripts/discover.sh <url> <maxSubpages>` (config's `maxSubpages`,
   default 10 — this caps `other` pages only; `services` is uncapped, `about` and `case-study`
   are capped at 5 by the script itself) to get the candidate list: a `SOURCE: nav|sitemap|none`
   line, then tab-separated `<kind>\t<url>` rows where `kind` is `services`, `about`,
   `case-study`, or `other`.
4. **Batch the fetches.** List what you need, then request every fetch that doesn't depend on
   another's result in one response. Run `scripts/fetch.sh <url> 3000` for the homepage and
   `scripts/fetch.sh <url> 1500` for each subpage. Each call emits `URL:`, `STATUS:`, `TITLE:`,
   `META:`, `H1:`, `HEADINGS:` (pipe-separated), `LINKS:` (pipe-separated), and `TEXT:` (last,
   the only multi-word field) — or `STATUS:` + `ERROR:` on a non-200 response, and the script
   still exits 0.
5. **Fill `references/snapshot-schema.json` literally.** Every key present, no extras, and an
   empty value written as `""`, `0`, or `[]` — never omitted, never `null`. This is the same
   rigidity contract `diff-rules.md` §0 states for the diff step, restated here because a
   schema you don't re-read at fill time is a schema you drift from:
   - Top level: `name`, `url`, `fetchedAt`, `tier`, `home`, `pages`, `linkedinAds`,
     `screenshots`, `errors`.
   - `home`: `title`, `metaDescription`, `h1`, `headings` (array), `text` (≤3000 chars).
   - Each `pages[]` entry: `url`, `kind`, `source`, `title`, `h1`, `text` (≤1500 chars) — no
     `metaDescription` key on page entries, only `home` has one.
   - `linkedinAds`: `tier`, `count`, `ads[]` — each ad: `headline`, `body`, `firstSeen`.
   - `screenshots`: `home`, `pages` (object keyed by page URL) — leave paths empty on the
     default tier.
   - `errors`: one entry per failed fetch (see Error handling).
   Write this to `competitor-intel/runs/<stamp>/snapshot.json`, where `<stamp>` is
   `YYYY-MM-DD_HH-mm`.
6. If a previous run directory exists under `competitor-intel/runs/`, apply
   `references/diff-rules.md` in full — including its §6 schema-drift guard — to produce
   `competitor-intel/runs/<stamp>/changes.json`. If there is no previous run, or a competitor's
   own comparison fails the drift guard, write the baseline form per diff-rules.md §5/§6 instead
   of skipping the file.
7. Read only `snapshot.json` and `changes.json` for this — never go back to raw HTML or the
   fetch output — and write `competitor-intel/runs/<stamp>/briefing.md` per
   `references/briefing-format.md`, all five sections, in order.
8. Update `competitor-intel/config.json`'s `lastRun` to the run stamp.

Scope: scan, diff, brief. If you find a bug in the scripts, or notice a page you could also be
scraping, note it as a follow-up at the end of the briefing's Data notes — don't fix or extend
anything mid-scan.

Progress: say in one line what you're about to do before you start; one short line per
competitor as it completes; close with the briefing itself, not a description of it — the
briefing must stand alone as the final message.

Before you send that final message, check your last paragraph: the turn ends with the briefing,
not a plan to write one.

## Error handling and size guard

- Every per-URL failure — a non-200 `STATUS:`, a transport error, a timeout — becomes one entry
  in that competitor's `errors[]`. The scan continues past it; a failed fetch never stops the
  run.
- A `403` or `429` on the homepage or a subpage means: skip the rest of that competitor's
  subpages for this run, record it in `errors[]`, and note in the briefing's Data notes that
  the site blocked default-tier fetches — suggest the deep tier (a real browser fetch is less
  likely to be blocked) or a manual check.
- `node` is on PATH but `scripts/deep/node_modules` is missing (Playwright never installed, or
  removed): fall back to the default tier for this run and say so once, in one line, before the
  fetch loop starts — not once per competitor.
- If a competitor's assembled snapshot exceeds 60 KB (the hard guard; target is 40 KB), truncate
  that snapshot's `text` fields — home first, then subpages, longest first — until it's under
  the guard, and note in Data notes which competitor was truncated and by roughly how much.

## Report

`report [run-id]` never re-scrapes. Read `competitor-intel/runs/<run-id>/snapshot.json` and
`changes.json` (or the most recent run directory if `run-id` is omitted), and regenerate
`briefing.md` from them per `references/briefing-format.md`. Use this to re-render a briefing
after a formatting fix, or to review an older run without burning a new scan.
