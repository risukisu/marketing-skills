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
to be `{"name": …, "baseline": true}` on an otherwise-diffed run — e.g. a competitor added to
the tracking list this cycle, while the rest have history. A baseline entry still carries its
`name`, so it can be attributed like any other; it just carries none of the seven fields.
Treat every baseline check below as per-competitor: read the top-level flag for framing the
Executive summary, but check each competitor's own entry before writing that competitor's
per-competitor subsection.

## Sections

`briefing.md` has exactly five sections, in this order. No other section is added, and none of
these five is dropped, merged, or reordered — even on a baseline run. (`## Style`, below, is
guidance for producing every section — it is never itself rendered as a heading in
`briefing.md`, and does not count toward the five.)

### Ordering rule for page-drawn lists

This is contract guidance, not a sixth section — it is never rendered as its own heading in
`briefing.md`; it governs how content inside Sections 1–3 below is assembled. `pages[]` carries
no guaranteed order (`diff-rules.md` §2) — the same content can arrive in a
different sequence on two runs. Every list below that is drawn from `pages[]` — the comparison
table's "Primary services (from nav)" row, the per-competitor "Primary services" list, "Secondary
pages flagged as not-in-nav," and the page scan behind "Products/platforms" — must be sorted
before it is capped or rendered, using this rule: sort the qualifying pages by `title`
(case-insensitive), falling back to the raw (non-normalized) `url` string lexicographically when
titles tie or are both empty. Apply a cap, if any, **after** sorting, so the same five (or
however many) items show on every run given the same underlying pages regardless of scan order.

### 1. Executive summary

3–4 sentences.

- **If the top-level `baseline` is `true`** (first-ever run): lead with the competitive
  landscape instead of any change — who's covered, how many competitors, what the market looks
  like at a glance — and say "baseline run" explicitly, in those words.
- **Otherwise**, lead with what changed since the last scan. Cover only competitors that have
  at least one non-empty changed field (or are themselves `{"name": …, "baseline": true}`); a
  competitor with all seven fields empty is not mentioned here — it gets a one-line "no changes
  since last scan" note in its own per-competitor subsection instead, not space in the summary.
- When covering changes, order by this materiality ranking and lead with the highest-ranked
  item that actually occurred, across all competitors: (1) `home_changes` — positioning
  language changed; (2) `new_pages` / `removed_pages`; (3) `moved_pages`; (4)
  `services_changes`; (5) `ad_count_delta` / `new_ad_headlines`. If a competitor's entry is
  `{"name": …, "baseline": true}` on an otherwise non-baseline run, mention it as "first scan
  of [competitor] — no comparison yet," ranked alongside `new_pages` since there is no prior state
  to compare either way. When two or more competitors tie at the same materiality rank, break
  the tie by `changes.json`'s `competitors[]` order — the same order Section 3 uses — and name
  the earlier one first.
- Never introduce a fact that isn't traceable to a changed field or a snapshot value.

### 2. Comparison table

Competitors as columns. Exactly these rows, top to bottom:

| Row | Source | Cell rule |
|---|---|---|
| Positioning | current snapshot `home.title` / `home.h1` | One short phrase in your own words (see Quoting rule) — never blank. |
| Primary services (from nav) | current snapshot `pages[]` where `kind == "services"` and `source == "nav"`, sorted per the Ordering rule above | Comma-separated `title`/`h1` list, first 5 items after sorting; beyond 5, append "+N more". If none, write "none listed in nav." |
| Products/platforms | named products/platforms found by scanning exactly this closed set: current snapshot `home` (`title`, `h1`, `headings`, `text`) plus every `pages[]` entry with `kind == "services"` (same fields), sorted per the Ordering rule above with `home` scanned first | Name each distinct product found (dedupe identical names case-insensitively; keep the first-seen casing; list in the order the set above was scanned). If the scan finds none, write "unnamed — not distinguished from services." |
| Target audience | homepage copy | One phrase. If not stated outright, infer from the copy and mark it "(inferred)". |
| LinkedIn ads (count + theme) | current snapshot `linkedinAds.count` and `linkedinAds.ads[]` | `"<count> — <theme>"`, e.g. `"3 — migration urgency"`. If count is 0, write `"0 — none observed"`. |

Every cell holds a specific, written value. Never a checkmark, never "Yes"/"No" — if a fact is
binary, write the fact itself (the service name, the count, the phrase), not a stand-in for it.

### 3. Per competitor

One subsection per competitor, headed with the competitor's name, in the order it appears in
`changes.json`'s `competitors[]`. Each subsection covers, in this order:

1. **Positioning/tagline** — same source as the comparison table's Positioning row, one to two
   sentences.
2. **Primary services** — same source and Ordering rule as the comparison table's row, no
   5-item cap here; list all, in sorted order.
3. **Secondary pages flagged as not-in-nav** — current snapshot `pages[]` entries where
   `source` is `"sitemap"`, regardless of `kind`, sorted per the Ordering rule above.
   (`"sitemap"` and `"nav"` are the only two values a page's `source` can carry:
   `discover.sh` emits `SOURCE: none` only when there were zero URLs to begin with, so no page
   can exist carrying it.) List URL + title. If there are none, omit this bullet entirely
   (don't write "none found").
4. **Products** — the same closed scan and dedupe as the comparison table's Products/platforms
   row, with one line of detail each if available (what it does, who it's for).
5. **Ad activity** — `linkedinAds.count`, and for each entry in `new_ad_headlines`, quote the
   headline (a headline is not marketing prose to paraphrase — quote it directly) plus a short
   note on theme. One caveat on what you are quoting: a deep-tier `headline` is the leading
   excerpt of an ad card's text, not a distinct headline field — the Ad Library markup has
   never been observed, so there is no verified selector for one (see
   `references/troubleshooting.md`). Quote it as the excerpt it is; never pad it out into a
   sentence, and never present a truncated excerpt as a complete headline.
6. **What changed and what it might signal** — this is where the seven changed fields land.
   - If this competitor's entry is `{"name": …, "baseline": true}`: write "Baseline run — no
     prior scan to compare" and stop; there are no changed fields to report.
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
   when it isn't the default, or when it differs from a prior run. Also name any competitor the
   deep pass was supposed to cover but produced no line for (per `SKILL.md` step 5), since its
   `"default"` tier values there mean "not read," not "nothing found."
3. **Pages capped** — read this off `discover.sh`'s `CAPPED: about=N case-study=N other=N`
   line, where `N` is the number of rows the cap **dropped**. The line is only emitted when a
   cap actually dropped something, so its presence is the fact. Name the competitor and which
   categories were capped, and by how many. Never infer a cap from "exactly 5 about pages are
   present" — the dropped rows leave no other trace, and a guess presented as a run fact is
   exactly what this section exists to prevent.
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
