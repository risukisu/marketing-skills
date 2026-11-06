---
name: content-audit
description: >-
  Diagnose how a website's content works as an inbound lead channel. Crawls the site, derives the
  offerings from the site as a whole (confirmed by the user), classifies every page by offering and
  AIDA stage (Attention, Interest, Desire, Action) with parallel subagents, scores value-proposition
  clarity, and finds where each offering's buyer journey breaks: missing or thin stages, pages with
  no onward step, content that is not found in search, traffic that does not convert. Optional
  Search Console, GA4, HubSpot and Google Ads exports, dropped into an ingest folder after the
  first run, add findability, traffic and first-touch leads. Python does every count. Output is one
  readable HTML report plus markdown and a page-level CSV, ending in a per-offering verdict
  (content, findability, conversion or distribution gap) and priorities handed to other skills. Use
  when the user says "/content-audit", "content audit", "content gap analysis", "AIDA audit",
  "journey gaps", "which offering lacks decision content", "does our content generate leads", or
  wants to know whether to invest in content, SEO, distribution or paid. Not the 7-part strategy
  audit (/content-strategy), not an internal-link audit (/internal-linking), not a technical SEO
  audit (/seo-audit).
---

# /content-audit — offering × AIDA content diagnosis

Crawl, map offerings, classify, score, measure, report. The scripts count; you judge offerings,
stages and value propositions, and write the narrative. A run lives in one folder in the user's
workspace and can be continued later with analytics exports.

| Reference | Use it for |
|---|---|
| [references/offering-map.md](references/offering-map.md) | Deriving offerings, `taxonomy.json`, the confirmation question |
| [references/classification.md](references/classification.md) | The AIDA and offering rubric, and the subagent brief |
| [references/value-proposition.md](references/value-proposition.md) | The six-criterion 0–2 score, `valueprop.json` |
| [references/exports.md](references/exports.md) | Which exports to request, the ingest folder, loader options |
| [references/diagnosis-rules.md](references/diagnosis-rules.md) | Cell statuses, verdict rules, thresholds, handoff skills |
| [references/report-rules.md](references/report-rules.md) | `narrative.json`, writing rules, build, final checklist |

Requires Python 3.9+ on the PATH (`python`, `python3` or `py`), standard library only. Scripts live in
`~/.claude/skills/content-audit/scripts/`; call them by full path from the launch folder so every
output lands in the user's workspace, never in the skill folder (a public repository). Static HTML
only: content rendered by JavaScript is not seen (the crawler warns).

## Workflow

Copy this checklist into your response and tick items as you go:

```
Content audit:
- [ ] Step 0: Context intake (scan, list, ask, read only what is approved)
- [ ] Step 1: Intake question (one question; new run or continue a run)
- [ ] Step 2: Crawl (crawl_site.py)
- [ ] Step 3: Prepare (prepare.py) and read site_profile.md
- [ ] Step 4: Offering map, then the confirmation gate (taxonomy.json)
- [ ] Step 5: Classify in parallel subagents, validate (check_labels.py labels)
- [ ] Step 6: Value proposition scores (valueprop.json, check_labels.py valueprop)
- [ ] Step 7: Ingest folder (ingest.py init; load if files are already there)
- [ ] Step 8: Analyze (analyze.py)
- [ ] Step 9: Narrative, build, verify (build_report.py, report-rules.md checklist)
- [ ] Step 10: Announce the report and the ingest folder
```

**Step 0: Context intake.** The skill stores no company data and uses none without the user's say-so.

1. Scan the launch directory (cwd and its repo) for `CLAUDE.md`, `AGENTS.md`, a `context/` folder,
   files named for brand, positioning, offering, ICP, persona or marketing audit, and earlier
   `content-audit-*/` run folders. List names only.
2. Ask one question: use these files / point me at another folder or file / paste the context as
   text / start with none. Wait.
3. Read only what was approved. A marketing audit or positioning doc informs the offering map and
   the narrative; it never overrides what the site says (differences between the two are findings).

**Step 1: Intake question.** Always ask it, once, even when the request seems to answer it: pre-fill
what the user already said and let them correct it. Their own words about the site and its offerings
are input for Step 4.

> **Which site, and anything I should know before I crawl it?**
>
> 1. Start URL (the homepage).
> 2. Optional: offerings you already know of, brand terms, sections to skip (for example `/de/` or
>    `/docs/`), a different page cap (default 1,000).
> 3. Analytics exports are not needed now: after the first report I create an `ingest` folder with
>    exact export steps, and you can add Search Console, GA4, HubSpot or Google Ads files any time.

If Step 0 found a run folder with `metrics.json`, ask instead: continue that run (load new exports
and rebuild) or start a new one. Continuing goes straight to Step 7 with `load`.

**Step 2: Crawl.** Run folder: `content-audit-<host>-<YYYY-MM-DD>` in the launch folder (`<host>`
without `www.`; characters other than letters, digits, dots and hyphens become `-`).

```bash
python ~/.claude/skills/content-audit/scripts/crawl_site.py https://example.com/ --run-dir content-audit-example.com-2026-01-31
```

A large crawl takes time (about 1,000 pages in 10 to 15 minutes): run it in the background
(`run_in_background: true` in Claude Code) and wait for it to finish, or give a foreground call the
longest timeout for sites under about 400 pages. The crawler saves `crawl.json` every 50 pages; if a
run stops, repeat the same command with `--resume` and it continues from there.

Options: `--max-pages 1000`, `--delay 0.3`, `--exclude REGEX` (repeatable; use for language folders
and sections the user named), `--no-sitemap`, `--urls list.txt` (crawl only listed URLs), `--resume`.
Exit code 2: the start URL failed; report it and ask for another. Read every `warning:` line; they go
into the report. A JavaScript warning means the classification will rest on titles alone: tell the
user before continuing.

**Step 3: Prepare.**

```bash
python ~/.claude/skills/content-audit/scripts/prepare.py --run-dir RUN
```

Excludes legal, utility, listing, careers, post-conversion and canonicalised duplicates (kept in the
CSV with a reason), writes `pages.json`, `site_profile.md` and batches of 50 pages. Read
`site_profile.md` in full.

**Step 4: Offering map and the gate.** Follow `references/offering-map.md`: write `taxonomy.json` with
`"confirmed": false`, ask the confirmation question, apply the answer, set `"confirmed": true`, then:

```bash
python ~/.claude/skills/content-audit/scripts/check_labels.py --run-dir RUN taxonomy
```

Nothing is classified before this passes. This is the run's second and last question.

**Step 5: Classify.** One subagent per batch file, brief from `references/classification.md`
("Subagent brief"). Send up to 10 in one message, then the next wave. Subagents write
`RUN/labels/batch_NN.json` and reply with one line; do not ask them for summaries. Then:

```bash
python ~/.claude/skills/content-audit/scripts/check_labels.py --run-dir RUN labels
```

It prints every problem and `rerun: …` batch numbers. Re-dispatch those batches with the problem
lines added to the brief (at most twice); a batch that still fails, classify yourself. Without a
subagent tool, classify batch by batch yourself, writing the same files.

**Step 6: Value proposition.** Score the homepage and each offering's main page per
`references/value-proposition.md`, write `RUN/valueprop.json`, then run
`check_labels.py --run-dir RUN valueprop` and fix what it lists.

**Step 7: Ingest folder.**

```bash
python ~/.claude/skills/content-audit/scripts/ingest.py --run-dir RUN init
python ~/.claude/skills/content-audit/scripts/ingest.py --run-dir RUN load    # only if files are there
```

`init` writes `RUN/ingest/README.md` with the export steps. `load` prints each file's detected kind,
the columns used and the date window. Exit code 3 means an unrecognised file: show its columns to the
user and ask what they are; never guess a mapping (`references/exports.md` lists the override flags).
Warnings about truncated exports go into the report.

**Step 8: Analyze.**

```bash
python ~/.claude/skills/content-audit/scripts/analyze.py --run-dir RUN
```

Prints the offering × AIDA grid with statuses and primary gaps, and warns when an export matches
under 70% of crawled pages (check the host or the crawl cap before writing anything). Read
`metrics.json` for the narrative: `per_offering` (verdicts with evidence), `matrix`, `icp_fit`,
`freshness`, `brand_split`, `valueprop`, `duplicates`, `striking_distance`, `layers`.

**Step 9: Narrative and build.** Write `RUN/narrative.json` per `references/report-rules.md`, run the
clean-up pass it describes, then build:

```bash
python ~/.claude/skills/content-audit/scripts/build_report.py --run-dir RUN
```

Fix every unverified number and every `style:` line, rebuild, then tick the checklist in
`references/report-rules.md`.

**Step 10: Announce.** Verdict and top priority in a few sentences, then the HTML path with the 📄
marker, the markdown and CSV paths. After a site-only run, name the ingest folder and what each export
would add; after a Phase 2 run, say what changed from the site-only read.

## When things go wrong

| Situation | Do this |
|---|---|
| Crawler exit 2 | Report the status; ask for another start URL (often `www.` vs bare domain) |
| Crawl stopped or timed out | Rerun the same command with `--resume`; it keeps the pages saved so far |
| Markup warning ("almost every link as navigation") | Nothing to do: body links were separated by repetition across pages; mention it under limits |
| JavaScript warning | Say so; offer `--urls` with a sitemap list, or continue on titles and headings and mark confidence `low` |
| Several languages | Audit one: rerun with `--exclude` for the other language folders |
| Page cap reached | Say which sections were covered; offer a rerun with a higher cap or excluded sections |
| A batch keeps failing validation | Classify it yourself; note it in `limits` |
| Export not recognised (exit 3) | Show its columns, ask the user, rerun `load` with `--source`/`--column` |
| Export window unknown | Ask the user for the dates; rerun `load` with `--window` |
| Under 70% of an export matches | Check host, language folder and cap before analysing; report the match share either way |
| An offering has no pages | Keep it; every cell shows missing, which is the finding |

## Scope

Diagnoses and points at fixes; does not write content, change the site, or plan the calendar. The
priorities hand work to `/content-strategy`, `/cro`, `/internal-linking`, `/seo-*` and the other
skills named in `references/diagnosis-rules.md`. Rerun the skill later on the same site to compare
against an earlier run folder.
