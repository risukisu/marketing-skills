# Dry-run eval — content-strategy skill, Audit flow — 2026-09-04

Full two-role transcript. ASSISTANT = Claude running `content-strategy`. USER = scripted
persona answering only with the facts supplied for this eval (Northgate Freight); any
question outside those facts is answered "I don't know." No real MCP tools were called —
this is a fictional company, and the scenario stipulates no analytics/GSC/DataForSEO
access on their side, so the data-hook offers are declined in character.

---

## Entry (passive trigger)

**USER:** can you audit our content strategy? we've been at it two years

**ASSISTANT:** I have a content-strategy skill that fits this. It either builds a
documented SEO-driven strategy from scratch (7 parts, then a quarterly content hub of
about 12 connected pieces), or audits what you already publish against the same 7 parts
and ranks the gaps. Want me to run it? Build, audit, or not now?

**USER:** audit

---

## Step 0: Intake

**ASSISTANT:** Tell me about your content program today: what do you publish, for whom,
and what is it supposed to do for the business?

**USER:** We're Northgate Freight, a B2B logistics firm for mid-size manufacturers in
Poland and the Baltics. We've had a written mission for two years: "Where operations
managers at manufacturers find practical guidance on freight and warehousing to keep
delivery promises." It's shown at the top of the blog and recent posts fit it. We also
publish an annual "Baltic freight cost benchmark" report — done it for 2025 and 2026,
each with a method note. The 2026 one got picked up by a couple of trade sites, though I
don't have referring-domain numbers. Beyond that it's just our own writers, no guest
voices, occasional guest posts elsewhere (about one a year, bio link only, never hosted
one ourselves). We have service pages for contract logistics and cross-border freight but
they're thin — mostly a paragraph and a contact form, never picked a target phrase for
either. No DA number, no analytics/GSC/DataForSEO tools hooked up on our end. Sales tells
us prospects ask constantly how we handle customs delays, and we don't have an article for
it — sales doesn't send articles to anyone right now. Our research reports have charts;
the blog posts just use stock photos.

**ASSISTANT (routing):** That's a running program with two years of published content, so
this is the Audit flow — scoring what exists against the same seven parts, then ranking
the gaps. *(Internal: read `references/audit-rubric.md` before scoring — done.)*

---

## Audit flow — evidence gathering, one part per message

**ASSISTANT (Part 1 — Sales page core):** Two things for the sales pages: which
commercial-intent phrase is each one targeting today (contract logistics, cross-border
freight), and do you have a Domain Authority number for the site, or for the pages
currently ranking on those phrases? If you've got GA4, Search Console, or a DataForSEO
connection I can pull conversion rate by landing-page type and DA directly — otherwise
just tell me what you know.

**USER:** No tools connected on our side, so I can't pull any of that. And no, we never
picked a target phrase for either page — they're thin, mostly a paragraph and a contact
form. DA unknown.

**ASSISTANT (Part 2 — Mission):** You gave me the sentence already — where's it published
beyond the blog header, and can you name three recent post titles to check they still fit
it?

**USER:** Just the blog header, that's the one place. I don't have specific titles handy,
but I can tell you recent posts have stayed on freight/warehousing/delivery topics for
manufacturers — nothing's wandered off it.

**ASSISTANT (Part 3 — Original research):** Tell me about the benchmark reports — publish
dates, and any sense of referring domains or links earned, even rough.

**USER:** 2025 and 2026 editions, both with a method note. The 2026 one got picked up by a
couple of trade sites — I don't know the referring-domain count, no tool to check it.

**ASSISTANT (Part 4 — Prospect questions):** What are sales hearing from prospects, and is
any of it turned into an article they can send?

**USER:** The recurring one is "how do you handle customs delays?" — comes up constantly.
No article answers it, and sales isn't sending articles to prospects right now, on that
question or anything else.

**ASSISTANT (Part 5 — Visuals):** What visual treatment does the top content get —
research pieces and blog posts both?

**USER:** The research reports have charts. Regular blog posts just run stock photos.

**ASSISTANT (Part 6 — Influencer collaboration):** Any contributor quotes, round-ups,
interviews, or a named list of people you work with in the field?

**USER:** None of that. Single-voice content only — just our own writers. No list.

**ASSISTANT (Part 7 — Guest posting / PR):** How often do you place content on other
sites, and where does the link land?

**USER:** Occasional — roughly one guest post a year, and the link is only in the author
bio, never in the body. We've never hosted a guest post ourselves either.

---

## Scoring, 1% test, ranked gaps

**ASSISTANT:**

Scored each part against `audit-rubric.md`'s present/partial/missing criteria, evidence
quoted from what you told me. Unknowns (DA, referring-domain counts, conversion rates) are
marked unknown, not estimated — you don't have the tools connected to get them right now.

Two calls worth flagging before the scorecard:

- **Visuals** lands on Partial, not Missing: the rubric's Missing bar is "text only," but
  your research charts exist — they just haven't reached the blog. That's a real asset,
  underused.
- **Prospect questions** lands on Missing per the rubric's own tie-break rule ("if the
  user can't produce evidence, that's missing"): you named one clear, recurring question
  with zero content against it and no sales-side usage of anything. I don't have evidence
  of other prospect-sourced articles either way, so I'm not assuming any exist.

1% test: 2 of 4 (mission and research are the two rare practices you've actually got).

Gap ranking starts from the rubric's default order (research, guest posting, influencer,
sales page, mission, prospect questions, visuals), drops the two parts that are already
Present (research, mission), then adjusts: prospect questions moves up from its default
slot because sales is visibly starving for material on a specific, constantly-asked
question — the rubric calls this the fastest-payoff case. Sales page fixes stay in their
default slot rather than jumping to first, since I don't have evidence the pages convert
at zero — I just don't have the conversion number at all. That's a flag, not a score.

Capacity adjustment: you're a single-voice, two-person-feeling content operation (no
guest hosting, no influencer list, occasional pitching). I'm sequencing the two cheapest,
fully in-house fixes first (the prospect-question article, the sales-page phrase pick) and
leaving relationship-built items (influencer list, guest pitching) for the quarter's
back half rather than asking you to start all five gaps in parallel.

---

## Output document

**ASSISTANT:** Default filename would be `content-audit-northgate-freight.md` in the
current directory — good to write it there?

**USER:** yes, default's fine

**ASSISTANT:** *(writes the file; in a live run, `/copy-deslop` runs on it next before
handing it back — noted here, not executed in this dry run.)*

---

## `content-audit-northgate-freight.md` (as produced)

```markdown
# Northgate Freight — content strategy audit

## 1. Scorecard

| Part | Score | Evidence | First fix |
|---|---|---|---|
| 1. Sales page | Missing | Contract logistics and cross-border freight pages exist but are "thin, mostly a paragraph and a contact form"; no target phrase ever chosen for either; DA unknown, no tool connected to check it. | Pick one commercial-intent phrase per page in buyer vocabulary, rebuild each around it: answer the top buyer questions, add evidence next to claims, CTA top and bottom. |
| 2. Mission | Present | "Where operations managers at manufacturers find practical guidance on freight and warehousing to keep delivery promises." Written two years ago, shown at the top of the blog, user confirms recent posts stay on topic (no specific titles logged — flagged as a soft spot in the evidence, not a score downgrade). | None needed to hold the score; log three example titles next audit so the fit claim is checkable, not just asserted. |
| 3. Original research | Present | Annual "Baltic freight cost benchmark," 2025 and 2026 editions, each with a method note; 2026 edition picked up by a couple of trade sites. Referring-domain count unknown — no tool connected to check it. | Get referring-domain data on record (Search Console links report or any SEO tool) so the "picked up" claim has a number behind it next time. |
| 4. Prospect questions | Missing | Sales reports "how do you handle customs delays?" as a constant, recurring question; no article answers it; sales does not send articles to prospects at all right now. | Write the customs-delays article, mapped directly to that question, hand it to sales this week — this is the fastest payoff of any gap here. |
| 5. Visuals | Partial | Research reports carry original charts; blog posts run stock photos only. | Pull one chart set from the 2026 benchmark into a short blog post or infographic — the asset already exists, it just hasn't left the research report. |
| 6. Influencer collab | Missing | Single-voice content only; no contributor quotes, round-ups, interviews, or named list of people in the field. | Draft a first list of five to ten people in Polish/Baltic logistics and manufacturing trade press who publish; start the warm-up (follow, share, comment) before any ask. |
| 7. Guest posting | Partial | Roughly one guest post a year; link lands only in the author bio, never in the body; never hosted a guest post. | On the next pitch, cite the 2026 benchmark research in the body of the piece, not just the bio — that's the link that counts toward authority. |

## 2. The 1% test

**2 of 4.** Documented mission (true) and anchored in original research (true) are both
in place — the two rarer practices Northgate has that most B2B programs don't. Ongoing
influencer collaboration (false — single-voice, no list) and PR-focused guest posting
(false — occasional, bio-link-only, scored Partial not Present) are both missing. The
source article's math puts all four together at roughly 1% of programs; Northgate is
already ahead of most on two of them, which is worth telling the team, not just the gap
list below.

## 3. Gaps ranked, with one first fix each

Research and mission are Present and excluded from this list — they're not gaps.

1. **Prospect questions (Missing).** Moved up from the rubric's default slot: sales is
   visibly starving for material on one specific, constantly-asked question, and this
   is the rubric's own fastest-payoff case. *First fix: write the customs-delays article
   and get it into sales' hands this week.*
2. **Guest posting (Partial).** *First fix: cite the benchmark research in the body of
   the next pitch, not just the bio.*
3. **Influencer collaboration (Missing).** *First fix: draft a five-to-ten-person target
   list from Polish/Baltic logistics and manufacturing trade press, start warming up.*
4. **Sales page (Missing).** Held at its default slot rather than promoted to first,
   because there's no evidence the pages convert at zero — conversion rate is unknown,
   not confirmed bad, since no analytics tool is connected. That gap in the evidence is
   itself worth closing before deciding how urgent this one is. *First fix: pick one
   target phrase per page (contract logistics, cross-border freight) and rebuild around
   it.*
5. **Visuals (Partial).** *First fix: repurpose one existing research chart set into a
   blog post or infographic instead of stock photos.*

**Capacity note:** sequenced the two fully in-house, no-relationship-building fixes
first (prospect-question article, sales-page phrase pick) and left the two
relationship-dependent gaps (influencer list, guest pitching) for the back half of the
quarter — a single-voice team with only occasional guest placement shouldn't start all
five gaps at once.

## 4. Next-quarter hub (from the missing and partial parts only)

Anchor stays the existing 2026 Baltic freight cost benchmark — already Present, marked
"existing" and linked from below rather than rebuilt.

| # | Piece | Purpose | Links to | Status |
|---|---|---|---|---|
| 1 | Sales page rebuild: contract logistics page around a chosen phrase | Rank, convert | 2026 benchmark (as proof) | New |
| 2 | 2026 Baltic freight cost benchmark | Links, credibility | Sales pages | Existing |
| 6 | Infographic pulled from the 2026 benchmark's existing charts | Links, reach | Benchmark | New |
| 8 | Influencer interview: one trade-press contact on the benchmark topic | Credibility, reach, links | Benchmark | New (depends on gap 3 fix) |
| 5 | Evil-twin guest pitch built from the customs-delays article, cited to the benchmark in the body | Links | Benchmark, sales page (bio) | New (depends on gap 2 fix) |
| 11 | Blog post: the customs-delays prospect question, answered directly | Pipeline | Sales page | New |
| 12 | Blog post: a second finding from the 2026 benchmark, expanded | Mission, reach | Benchmark | New |

Slots 3, 4, 7, 9, 10 from the full twelve-slot skeleton are not populated this quarter —
no gated content upgrade, second how-to, second guest pitch, podcast, or extra finding
is committed yet given the capacity note above. Fill them once the first five land.
```

---

## Post-run notes (Claude's eval commentary, not part of the delivered document)

Where SKILL.md or a reference was unclear, contradictory, or forced a guess:

1. **Audit flow doesn't name which references to read beyond `audit-rubric.md`.** The
   Build flow table explicitly maps each step to a reference file; the Audit flow (SKILL.md
   step 1) only says "Read `references/audit-rubric.md`." I read all seven part-reference
   files anyway for scoring judgment calls (e.g., what "evil twin" means for the guest-posting
   fix), but the skill doesn't instruct that, so a stricter run might skip them and lose that
   context. Worth a line in SKILL.md's Audit flow saying whether the seven part references are
   in-scope for audit or build-only.
2. **Mission's "Present" criterion asks for "three recent titles to test fit," but the audit
   rubric's evidence line doesn't say what to do when the user has the sentence and a verbal
   assurance but not the titles.** I kept the Present score (nothing in the rubric requires
   downgrading on missing titles specifically) but had to invent the handling — flag it as a
   soft evidence spot rather than a partial. A stricter reader could argue this should be
   Partial ("implied" / unverifiable), and the rubric doesn't clearly resolve which.
3. **The sales-page gap-ranking rule ("unless the page converts at zero, in which case it
   jumps to first") doesn't say what to do when conversion is simply *unknown*** — not
   confirmed zero, not confirmed nonzero. I treated unknown as "stay in default slot, flag the
   gap in evidence" rather than promoting it, but the rubric is silent on this specific case,
   which is going to recur often since DataForSEO/GA4/GSC access is optional, not guaranteed.
4. **"Data hooks at step 1" (SKILL.md) is written only for the Build flow** (it sits under the
   Build flow table) but the Audit flow's step 2 says "Offer the data hooks above at part 1 if
   tools are loaded," pointing back at Build-flow language. It works, but a reader following
   Audit flow top-to-bottom has to jump back into Build-flow prose to know what the offer text
   actually is. Minor structural nit.
5. **No guidance on what "quote the evidence" should look like when the user's answer is a
   short spoken sentence rather than a URL/number.** I quoted the user's own phrasing verbatim
   in the scorecard's Evidence column, which produces long cells; the rubric's evidence lines
   (e.g. "URL, target phrase, DA...") read as if URLs/numbers are the default shape, so
   verbatim-quote-of-a-sentence was a judgment call, not a prescribed format.

**1% test result computed in this run: 2 of 4** (documented mission — true; anchored in
original research — true; ongoing influencer collaboration — false; PR-focused/guest
posting — false, scored Partial not Present).
