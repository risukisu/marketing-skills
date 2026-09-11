# Briefing format

This is the contract for `briefing.md`, the one artifact in this skill a human actually reads.
`SKILL.md` generates `briefing.md` from `changes.json` (produced per `references/diff-rules.md`)
plus the current run's snapshots. Follow this file literally — the test is that two runs given
the same `changes.json` and snapshots produce briefings with the same structure and the same
editorial judgment about what belongs where.

`changes.json` carries exactly seven per-competitor fields, defined in `diff-rules.md` §3:
`new_pages`, `removed_pages`, `moved_pages`, `home_changes`, `services_changes`,
`ad_count_delta`, `new_ad_headlines`. Every reference to a "changed field" below means one of
these seven, named exactly as written here.

**Baseline is per-competitor, not just per-run.** `changes.json` has a top-level `baseline`
flag for a first-ever run, but `diff-rules.md` §5 also allows an individual competitor's entry
to be `{"baseline": true}` on an otherwise-diffed run — e.g. a competitor added to the tracking
list this cycle, while the rest have history. Treat every baseline check below as
per-competitor: read the top-level flag for framing the Executive summary, but check each
competitor's own entry before writing that competitor's per-competitor subsection.

## Sections

`briefing.md` has exactly five sections, in this order. No other section is added, and none of
these five is dropped, merged, or reordered — even on a baseline run.

### 1. Executive summary

3–4 sentences.

- **If the top-level `baseline` is `true`** (first-ever run): lead with the competitive
  landscape instead of any change — who's covered, how many competitors, what the market looks
  like at a glance — and say "baseline run" explicitly, in those words.
- **Otherwise**, lead with what changed since the last scan. Cover only competitors that have
  at least one non-empty changed field (or are themselves `{"baseline": true}`); a competitor
  with all seven fields empty is not mentioned here — it gets a one-line "no changes since last
  scan" note in its own per-competitor subsection instead, not space in the summary.
- When covering changes, order by this materiality ranking and lead with the highest-ranked
  item that actually occurred, across all competitors: (1) `home_changes` — positioning
  language changed; (2) `new_pages` / `removed_pages`; (3) `moved_pages`; (4)
  `services_changes`; (5) `ad_count_delta` / `new_ad_headlines`. If a competitor's entry is
  `{"baseline": true}` on an otherwise non-baseline run, mention it as "first scan of
  [competitor] — no comparison yet," ranked alongside `new_pages` since there is no prior state
  to compare either way.
- Never introduce a fact that isn't traceable to a changed field or a snapshot value.

### 2. Comparison table

Competitors as columns. Exactly these rows, top to bottom:

| Row | Source | Cell rule |
|---|---|---|
| Positioning | current snapshot `home.title` / `home.h1` | One short phrase in your own words (see Quoting rule) — never blank. |
| Primary services (from nav) | current snapshot `pages[]` where `kind == "services"` and `source == "nav"` | Comma-separated `title`/`h1` list, up to 5 items; beyond 5, append "+N more". If none, write "none listed in nav." |
| Products/platforms | named products or platforms mentioned on the homepage or a matching page | Name each one. If the competitor names no distinct product, write "unnamed — not distinguished from services." |
| Target audience | homepage copy | One phrase. If not stated outright, infer from the copy and mark it "(inferred)". |
| LinkedIn ads (count + theme) | current snapshot `linkedinAds.count` and `linkedinAds.ads[]` | `"<count> — <theme>"`, e.g. `"3 — migration urgency"`. If count is 0, write `"0 — none observed"`. |

Every cell holds a specific, written value. Never a checkmark, never "Yes"/"No" — if a fact is
binary, write the fact itself (the service name, the count, the phrase), not a stand-in for it.

### 3. Per competitor

One subsection per competitor, headed with the competitor's name, in the order it appears in
`changes.json`'s `competitors[]`. Each subsection covers, in this order:

1. **Positioning/tagline** — same source as the comparison table's Positioning row, one to two
   sentences.
2. **Primary services** — same source as the comparison table's row, no 5-item cap here; list
   all.
3. **Secondary pages flagged as not-in-nav** — current snapshot `pages[]` entries where
   `source` is `"sitemap"` or `"none"` (i.e. not `"nav"`), regardless of `kind`. List URL +
   title. If there are none, omit this bullet entirely (don't write "none found").
4. **Products** — as identified for the comparison table, with one line of detail each if
   available (what it does, who it's for).
5. **Ad activity** — `linkedinAds.count`, and for each entry in `new_ad_headlines`, quote the
   headline (a headline is not marketing prose to paraphrase — quote it directly) plus a short
   note on theme.
6. **What changed and what it might signal** — this is where the seven changed fields land.
   - If this competitor's entry is `{"baseline": true}`: write "Baseline run — no prior scan to
     compare" and stop; there are no changed fields to report.
   - Otherwise, walk the seven fields in this fixed order — `new_pages`, `removed_pages`,
     `moved_pages`, `home_changes`, `services_changes`, `ad_count_delta`,
     `new_ad_headlines` — and for each **non-empty** field, render its entries and add one
     sentence of signal (a hypothesis about what the change suggests, phrased with "suggests"
     or "may indicate" — never stated as fact). Skip a field entirely if it's empty; do not
     write "no change" per field. If all seven fields are empty, write one line: "No changes
     since last scan" and stop.
   - Render each entry type as: `new_pages`/`removed_pages` — the URL; `moved_pages` — `"from"
     → "to"` with `matchedOn` noted; `home_changes`/`services_changes` — the `field` name with
     before → after (apply the Quoting rule below to any `before`/`after` text taken from the
     competitor's own copy); `ad_count_delta` — the signed number with direction in words (e.g.
     "up 2"); `new_ad_headlines` — each headline, quoted directly (headlines are short and
     literal, not the mannered marketing prose the Quoting rule guards against).

#### Quoting rule

This block appears verbatim — it is the guard against reproducing a competitor's marketing
copy unmarked in a briefing that gets circulated internally:

<example>
Correct:
  Atlas leads with "validated pipelines for regulated data" on the homepage — a compliance-first
  framing. The rest of the page argues speed, but the H1 spends its words on trust.

Wrong (unmarked reproduction):
  Atlas builds validated pipelines for regulated data, delivering speed without compromising trust.

Rule: at most one short marked quotation per competitor per section. Everything else is indirect
speech. If a sentence could be pasted into their site unchanged, rewrite it.
</example>

This rule binds the comparison table, every per-competitor subsection, and any `before`/`after`
text rendered from `home_changes` or `services_changes`. Ad headlines quoted under "Ad
activity" and `new_ad_headlines` are the one deliberate exception — a headline is already a
short, discrete unit, not prose to be indirectly reported, so quote it directly and it does not
count against the one-quotation-per-section limit.

### 4. Recommendations

3–5 recommendations, each concrete enough to assign to a person. A recommendation meets that
bar only if it satisfies all three:

- **Names a deliverable** — a noun a person can start building today: a landing page, an ad, a
  calculator, an email sequence, a pricing page section. Not an activity with no end state
  ("look into," "consider," "revisit").
- **Cites the change that drove it** — name the competitor and the changed field (or table row)
  behind the recommendation, so a reader can trace it back to section 2 or 3.
- **Requires no further decision meeting** — if satisfying the recommendation would mean
  scheduling a meeting to decide what to do, rewrite it as the action that meeting would have
  decided.

  - Good: "Create a SAS-migration landing page with an ROI calculator." (deliverable: the page;
    traceable: e.g. Atlas's `new_pages` entry for a migration page, or its ad theme)
  - Bad: "Consider revisiting positioning." (no deliverable, no end state, not assignable)

### 5. Data notes

Final section. Covers everything about the run itself that isn't a competitive fact — never
about what changed on a competitor's site, always about how the run went. In this fixed order,
one line per item, grouped by competitor where applicable; omit any category with nothing to
report:

1. **Fetch errors** — entries from each competitor's current-snapshot `errors[]`.
2. **Tier used** — each competitor's `tier` (page fetch) and `linkedinAds.tier` (ad fetch), only
   when it isn't the default, or when it differs from a prior run.
3. **Pages capped** — where `discover.sh`'s per-kind caps were hit (about/case-study pages
   capped at 5, other pages capped at the configured max), name the competitor and which
   category was capped.
4. **Duplicate pages dropped** — per `diff-rules.md` §2's de-duplication step: the normalized
   URL that had duplicates, how many entries shared it, and the raw `url` of the entry that won.
5. **Ambiguous-tie notices** — per `diff-rules.md` §2 rules 2–3: any title or h1 tie (zero or
   ambiguous) that contributed to a page's removed/new verdict, named by competitor and URL.
6. **Schema-drift fallbacks** — per `diff-rules.md` §6: any competitor whose run was treated as
   a baseline because a previous snapshot failed the schema-rigidity check, with the missing key
   that triggered it.
7. **Anything else skipped** — any other fetch, parse, or assembly step that was skipped or
   fell back, not covered above.

If none of the above produced anything to report for the whole run, write: "No fetch errors,
capped pages, duplicate pages, ambiguous ties, or schema-drift fallbacks this run."

## Style

Banned outright, in any section: "table stakes", "battleground", "game-changer", "leverage" as
a verb, "best-in-class", "double down", "moving the needle", "robust", "seamless".

Remove all mannered prose. When a literal phrase is available, use it.
