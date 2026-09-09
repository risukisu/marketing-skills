# Dry-run eval — content-strategy skill, Build flow

**Date:** 2026-09-04
**Scenario:** Ledgerline, a B2B payroll consultancy for UK SMEs (50-500 staff)
**Mode tested:** Build flow, full run, entered via explicit `/content-strategy`
**Method:** One transcript, two roles — "Claude" runs the skill exactly as
SKILL.md and its references prescribe; "User" answers using only the facts
supplied for this eval, saying "I don't know" for anything not covered.

No context pack exists at `references/*-context.local.md` (checked before the
run — none found), so no pack was read or applied.

---

## Entry

**User:** `/content-strategy`

**Claude (internal):** Entry gate — user typed the command explicitly, so skip
the passive-trigger offer text and go straight to Step 0.

## Step 0: Intake

**Claude:** Tell me about your content program today: what do you publish, for
whom, and what is it supposed to do for the business?

**User:** We're Ledgerline, a B2B payroll consultancy for UK SMEs — 50 to 500
staff. We have 40 blog posts, mostly generic payroll tips. It's not generating
leads. No documented mission for the blog. We've never done original research.
No guest posts anywhere. We did co-host one webinar last year with an
accounting software partner. All the images are stock.

**Claude (internal):** This describes a running program with 40 published
posts, which per the routing table would normally point at the Audit flow.
But there's no documented mission, no research, no guest posts, and the
existing posts are generic and unconverted — closer to "nothing that's
actually working" than "a program to audit." Routing is genuinely unclear
between the two modes here, so per Step 0 ("Unclear → ask which they want"),
asking rather than assuming.

**Claude:** You've got 40 posts live, but no documented mission, no research,
no guest posts, and they're not converting — so this could go either way. Do
you want me to build a fresh, documented strategy from here (treating the
existing posts as background, not a foundation), or audit the current 40
posts against the framework and rank what's missing?

**User:** Let's build it fresh.

**Claude (internal):** Routing to Build flow.

---

## Build flow

### Step 1 — Sales page core

*(Read `references/sales-page-checklist.md` before asking.)*

**Claude:** Which service page should generate leads, and what
commercial-intent phrase should it rank for? What's the site's Domain
Authority and the phrase's difficulty? And: what does the page currently fail
to answer or prove?

**Claude (internal — data hooks):** No `analytics-mcp`, `gsc`, or DataForSEO
tools are loaded this session, so I can't offer to pull DA, phrase difficulty,
or landing-page conversion split. Asking directly instead.

**User:** The page is `/outsourced-payroll`, target phrase "outsourced payroll
for SMEs". Site DA is 22. I don't know the competitor DA or the phrase
difficulty. I don't know what the page fails to answer or prove either — we
haven't audited it.

**Claude (internal):** Recording DA 22, phrase and page confirmed, competitor
DA / difficulty / page gaps all marked unknown per the checklist's "never make
the numbers a precondition" rule.

### Step 2 — Mission

*(Read `references/mission-statement.md` before asking.)*

**Claude:** Who exactly is the content for, what topics, and what do they get
from it? Let's draft the one-sentence mission together.

**User:** I don't know how to phrase it — you draft something from what I've
told you and I'll react to it.

**Claude:** Working from what's on record — you sell outsourced payroll to
50-500 staff UK SMEs, and the sales questions you get are about cost, mistakes,
and pension auto-enrolment — here's a draft:

> Where finance and HR leads at 50-500 person UK companies find plain answers
> on payroll cost, compliance, and pension auto-enrolment, so they can decide
> whether to outsource without guessing.

Does that hold, or does it claim something you can't back?

**User:** That works.

**Claude (internal):** Mission confirmed as drafted. Audience: finance/HR
leads at 50-500 staff UK SMEs. Topics: payroll cost, compliance, pension
auto-enrolment. Benefit: an informed outsourcing decision.

### Step 3 — Original research

*(Read `references/original-research.md` before asking.)*

**Claude:** What does your audience wish someone would measure? What data can
you reach that competitors can't?

**User:** I don't know.

**Claude (internal):** Both answers unknown. Flagging in the document: no
research topic identified this round, and the checklist's own gate ("headline
written before data collection starts") can't be passed without one. This
also means slot #2 of the twelve-slot hub (the research anchor) has no
material yet — flagging that downstream too.

### Step 4 — Prospect questions

*(Read `references/prospect-questions.md` before asking.)*

**Claude:** What three questions came up in sales conversations last month?
What do prospects get wrong about the offer?

**User:** Sales hears "is it cheaper than in-house?" every week. "What happens
if you make a mistake on payroll?" comes up often. "Can you handle our pension
auto-enrolment?" comes up sometimes. I don't know what prospects get wrong
about the offer.

**Claude (internal):** Three questions captured, mapped below. "What prospects
get wrong" recorded as unknown.

| Question | Frequency | Article title | Sales use |
|---|---|---|---|
| "Is it cheaper than doing it in-house?" | Weekly | The real cost of in-house payroll for a 50-500 person UK company | Send after first call |
| "What happens if you make a mistake on payroll?" | Often | What happens when a payroll error slips through — and who's on the hook | Send when risk/liability comes up |
| "Can you handle our pension auto-enrolment?" | Sometimes | Outsourced payroll and pension auto-enrolment: what's actually covered | Send during scoping |

### Step 5 — Visuals

*(Read `references/visuals.md` before asking.)*

**Claude:** Which existing or planned piece deserves a visual version? Who can
produce it?

**User:** We have one part-time designer. No video capacity.

**Claude (internal):** No original research exists yet (Step 3 came back
unknown), so the usual first candidate — a chart set from the research — isn't
available. Falling back to the checklist's other repurposing targets: the top
how-to and the sales-page proof. Since sales questions are the strongest
material on hand, proposing the highest-frequency prospect question as the
visual candidate, and ruling out video and any format needing more than one
part-time designer's bandwidth.

**Claude:** No research to build a chart set from yet, so the candidate is the
"is it cheaper than in-house?" article — a simple cost-comparison graphic your
designer can produce without video. Does that fit their bandwidth?

**User:** I don't know.

**Claude (internal):** Recording the visual pick as proposed, producer
capacity for this specific piece unconfirmed — flagging in the document.

### Step 6 — Influencer collaboration

*(Read `references/influencer-collab.md` before asking.)*

**Claude:** Who does your audience already trust and read? Which of the five
free formats fit this quarter?

**User:** Two UK accounting newsletter writers and one HR podcast. I don't
know their names.

**Claude (internal):** Named-people target (5-10 per the checklist) can't be
filled — only three unnamed roles exist. Recording as roles, not names, and
flagging the gap. For format: a contributor quote is the lowest-effort of the
five and fits a first quarter with no existing relationships, so proposing
that plus a round-up once names exist.

**Claude:** With three trusted voices in view but no names yet, the realistic
move this quarter is a contributor quote — from whichever of the three you can
name first — used in the cost-comparison article. Round-ups and interviews can
wait for next quarter once you have names and a warm-up in progress. Sound
right?

**User:** That works.

### Step 7 — Guest posting

*(Read `references/guest-posting.md` before asking.)*

**Claude:** Which five sites would you most want to appear on? What could you
pitch them this quarter?

**User:** AccountingWEB and two HR trade sites. I don't know their names.

**Claude (internal):** Two of five-to-ten target sites named (one specifically:
AccountingWEB; two more described but unnamed). Recording as-is, flagging the
gap against the checklist's five-to-ten target. For pitch angle: since original
research doesn't exist yet, the evil-twin of the strongest prospect-question
article is the only available pitch material this quarter.

**Claude:** With research not yet built, the pitch this quarter has to be the
evil twin of the in-house-cost article — something like "Five ways UK SMEs
miscalculate the true cost of in-house payroll" — pitched to AccountingWEB
first, since that's the one you've named. The two HR trade sites go on the
target list once you have names. Does that work as a first move?

**User:** Yes.

---

## Hub assembly

*(Read `references/content-hub-template.md` before assembling.)*

**Claude (internal):** The twelve-slot skeleton assumes an original-research
anchor (slots 2, 3, 6, 7, 8, 9, 10, 12 all point at it). Step 3 came back
unknown, so this hub cannot be built as specified — flagging this explicitly
in the document rather than inventing a research topic to fill the slots. The
hub below substitutes the three prospect-question articles and the one
webinar relationship as the connective material available this quarter, and
marks every slot that would normally depend on research as blocked.

---

## Output

**Claude:** That's all seven parts. Default filename would be
`content-strategy-ledgerline.md` in the current directory — good to use that?

**User:** Yes, default's fine.

**Claude (internal):** Per the output contract, the finished file would now
get `/copy-deslop` run on it before being considered done. **Not executed in
this dry run** — noting it here instead, as instructed.

Below is the document as it would be written to
`content-strategy-ledgerline.md`.

---

### `content-strategy-ledgerline.md` (as produced)

```markdown
# Content strategy — Ledgerline

Built with the Orbit Media 7-part B2B content strategy framework (Andy
Crestodina). Source:
https://www.orbitmedia.com/blog/content-strategy-framework/

## 1. Content mission

> Where finance and HR leads at 50-500 person UK companies find plain answers
> on payroll cost, compliance, and pension auto-enrolment, so they can decide
> whether to outsource without guessing.

- **Audience:** Finance and HR leads at UK SMEs, 50-500 staff.
- **Topics:** Payroll cost, compliance, pension auto-enrolment.
- **Benefit:** An informed, confident outsourcing decision.

## 2. Sales page target

- **Page:** `/outsourced-payroll`
- **Target phrase:** "outsourced payroll for SMEs"
- **Current DA:** 22
- **Competitor DA for this phrase:** Unknown
- **Phrase difficulty:** Unknown
- **Gap:** Unknown — cannot be sized without competitor DA or difficulty data
- **What the page fails to answer/prove:** Unknown — not yet audited

**Rank fixes** (from the checklist, apply regardless of the unknowns above):
- Confirm phrase appears in title tag, H1, URL, and naturally in body copy.
- Build internal links to this page from at least three relevant blog posts,
  using descriptive anchor text.
- Verify technical basics: fast, mobile-friendly, indexable, schema where it
  fits.

**Convert fixes:**
- First screen should answer "what do you do" and "who is it for" — verify
  once the page is audited (unknown gap above).
- Address the three known buyer questions on the page itself, not just in
  blog posts: cost vs. in-house, error liability, pension auto-enrolment
  coverage.
- Place evidence (client examples, credentials, volume/years) next to each
  claim — current evidence inventory unknown.
- Confirm CTA above the fold and at the end, with a specific verb.

**Flag:** Competitor DA, phrase difficulty, and the page's specific content
gaps are all unknown. No DataForSEO/GSC/GA4 tools were available this
session — these numbers should be pulled before the rank-fix work is
prioritized.

## 3. Original research

**Status: not identified this quarter.**

Both scoping questions — what the audience wishes someone would measure, and
what data Ledgerline can reach that competitors can't — came back unknown.
No research topic, data route, or contributor list exists yet. This is a gap,
not a placeholder: the framework treats original research as the strongest
link-earning asset in the program, and the hub below is built without one.

**First step for next quarter:** identify one measurable claim Ledgerline
already makes anecdotally to clients (e.g., about cost, error rates, or
processing time) and check whether client data could support it.

## 4. Prospect questions captured

| Question (prospect's words) | Frequency | Article title | Sales use |
|---|---|---|---|
| "Is it cheaper than doing it in-house?" | Weekly | The real cost of in-house payroll for a 50-500 person UK company | Send after first call |
| "What happens if you make a mistake on payroll?" | Often | What happens when a payroll error slips through — and who's on the hook | Send when risk/liability comes up |
| "Can you handle our pension auto-enrolment?" | Sometimes | Outsourced payroll and pension auto-enrolment: what's actually covered | Send during scoping |

What prospects get wrong about the offer: unknown.

## 5. Visual repurposing plan

- **Producer:** One part-time designer. No video capacity this quarter.
- **Candidate piece:** The in-house-cost comparison article (highest sales
  frequency, and the only material available since no research exists to
  chart yet) — proposed as a simple cost-comparison graphic.
- **Designer bandwidth for this specific piece:** Unknown — confirm before
  committing it to the calendar.
- **Research-derived visuals (chart set, infographic):** Blocked until
  Part 3 has a topic.

## 6. Influencer collaboration plan

**Trusted voices named by role, not name (names unknown):**
- Two UK accounting newsletter writers
- One UK HR podcast

**Gap:** Checklist target is five to ten named people; only three unnamed
roles are on record.

**Format for this quarter:** Contributor quote — lowest-effort of the five
free formats, usable in the cost-comparison article once one of the three
voices is named. Round-up and interview formats deferred to next quarter,
after names are identified and a two-week warm-up (follow, share, comment)
runs ahead of any ask.

## 7. Guest posting plan

**Target sites:**
- AccountingWEB (named)
- Two UK HR trade sites (unnamed — identify before pitching)

**Gap:** Checklist target is five to ten sites; two of five are on record,
one of those unnamed.

**Pitch for this quarter:** Evil twin of the cost-comparison article — working
title "Five ways UK SMEs miscalculate the true cost of in-house payroll" —
pitched to AccountingWEB first. No research exists yet to offer as a citation
or infographic pairing, so the pitch relies on the prospect-question material
until Part 3 is filled.

## 8. Quarter 1 content hub

**Flag before the table:** The twelve-slot skeleton assumes an original
research anchor running through most slots. Ledgerline has no research topic
this quarter (Part 3), so slots that depend on it are marked **BLOCKED** below
rather than filled with invented material. The hub instead runs on the three
prospect-question articles, the sales-page fixes, and the one available guest
pitch.

| # | Piece | Purpose | Links to | Status |
|---|---|---|---|---|
| 1 | Sales page fixes on `/outsourced-payroll` | Rank, convert | — | Ready — apply checklist fixes from Part 2 |
| 2 | Original research | Links, credibility | Sales page | **BLOCKED** — no topic identified |
| 3 | Gated content upgrade (deeper research) | Pipeline | Research | **BLOCKED** — depends on #2 |
| 4 | "The real cost of in-house payroll" | Rank, pipeline | Sales page | Ready |
| 5 | Evil twin of #4, pitched to AccountingWEB | Links | Sales page (bio) | Ready — pitch drafted above |
| 6 | Infographic from research | Links, reach | Research | **BLOCKED** — depends on #2 |
| 7 | Infographic + article pitched to a second site | Links | Research | **BLOCKED** — depends on #2 and on naming the two HR trade sites |
| 8 | Influencer interview | Credibility, reach | Research | **BLOCKED** — depends on #2 and on naming a trusted voice |
| 9 | Podcast/contribution pitch | Links, credibility | Research | Partial — the named HR podcast is a candidate once contact is made; not research-based |
| 10 | "What happens when a payroll error slips through" | Pipeline | Sales page | Ready |
| 11 | "Outsourced payroll and pension auto-enrolment: what's actually covered" | Pipeline | Sales page | Ready |
| 12 | Cost-comparison visual (from Part 5) alongside piece #4 | Reach | Sales page, #4 | Ready, pending designer bandwidth confirmation |

**Twelve-week calendar (adjusted for the blocked slots):**

| Weeks | Work |
|---|---|
| 1-4 | Apply sales-page fixes (#1). Publish "the real cost of in-house payroll" (#4) and its visual (#12). Draft and send the AccountingWEB pitch (#5). Start identifying a research topic to unblock #2, #3, #6, #7, #8. |
| 5-8 | Publish the error-liability and pension-auto-enrolment articles (#10, #11). Follow up on the AccountingWEB pitch. Name at least one of the two accounting newsletter writers or the HR podcast host and open a warm-up (follow, share, comment). |
| 9-12 | If a research topic and a named contributor exist by week 9, scope the smallest possible version of Part 3 for next quarter rather than trying to run it inside this one. Otherwise: publish evil twin if accepted, send contributor-quote request, review what worked, and carry #2, #3, #6, #7, #8, #9 unchanged into Q2 planning. |

## 9. Timeline expectation and what to measure

Per the framework's own estimate, this is the shape of the curve, not a
promise: each hub typically earns five to ten links; from DA 22, a
mid-difficulty commercial phrase is roughly a nine-month target; leads through
the contact form within a year. Ledgerline's phrase difficulty is unknown, so
this timeline cannot be sized more precisely without a DataForSEO or GSC pull.

**What to measure, monthly unless noted:**

| Metric | Where | Cadence |
|---|---|---|
| Links earned per hub (referring domains) | Search Console links report or any SEO tool | End of quarter |
| Domain Authority | SEO tool | Quarterly |
| Sales page rank for "outsourced payroll for SMEs" | Search Console, rank tracker | Monthly |
| Conversion rate by landing-page type (service vs. blog) | GA4 segments | Monthly |
| Articles sent by sales to prospects | Ask sales; CRM if tracked | Monthly |

**Known unknowns carried into next quarter:** competitor DA and phrase
difficulty for the target phrase; the sales page's specific content gaps;
an original research topic; names for the two accounting newsletter writers,
the HR podcast, and the two HR trade sites; designer bandwidth for the
cost-comparison visual. None of these were estimated — each is labeled
unknown above and should be resolved before the blocked hub slots can run.
```

---

## Where `/copy-deslop` belongs

Per the output contract's last line — "Run `/copy-deslop` on the finished
file" — this is the point in the real flow where Claude would invoke
`/copy-deslop` against `content-strategy-ledgerline.md` before handing it
back to the user. **Not run in this dry run**, as instructed.

---

## Eval notes

See the reply accompanying this file for places where SKILL.md or a
reference was unclear, contradictory, or required a judgment call.
