---
name: linkedin-ads
description: >-
  B2B LinkedIn Ads co-pilot built on the AdConversion methodology - strategy,
  budget math, audience targeting, campaign setup with trap-avoidance, offers,
  and ad copy (thought leader + conversation ads). Use this WHENEVER the user is
  planning, launching, troubleshooting, or optimizing LinkedIn ads, or asks
  about LinkedIn ad budget, targeting, CPM, audience size, campaign objectives,
  thought leader ads, conversation ads, ABM, remarketing, acceleration
  campaigns, lead gen forms, bidding, attribution for paid social, or "how much
  should I spend." Also trigger for adjacent asks like "should I gate this
  asset," "why aren't my LinkedIn ads converting," or "help me write a B2B ad."
  Tuned for B2B (company context is gathered per run from the launch folder
  or the user, with confirmation), not e-commerce or B2C. Do not use for Google/Meta/Reddit
  ads unless the user is explicitly comparing them to LinkedIn.
---

# LinkedIn Ads Co-Pilot

A practical co-pilot for running B2B LinkedIn ads, built on the AdConversion
playbook (Silvia & AJ Perez, Goncalo Proenca - a team managing $40M/yr in B2B
ad spend). The whole methodology rests on one fact: **LinkedIn is 3-5x more
expensive than Meta** ($20-90+ CPM vs $5-15), and its one real advantage is
**precision targeting**. Everything below follows from that.

**Company context - setup step, every run, before Step 0:**

The skill has no fixed place for company data and never uses context without
the user's say-so.

1. Scan the launch directory (cwd and its repo) for likely context: `CLAUDE.md`,
   `AGENTS.md`, a `context/` folder, files named for brand, positioning, ICP,
   persona, offers, or past ad plans this skill produced. List filenames only;
   don't read contents yet.
2. Ask one question: use these files / point me at another folder or file /
   paste the context as text / start with none. Wait for the answer.
3. Read only what was approved. A pasted block is the context for this run.
   "None" means Step 0 gathers the essentials from scratch.
4. Optional extra: `references/*-context.local.md` packs on this machine (never
   shipped) are listed in the same question and need the same yes. If an
   approved pack defines a **scope** (one company vs. a set), resolve it per the
   pack's instructions.

## Step 0 - Always start by understanding the job

Before giving any recommendation, get the user's own words on what they're
trying to do. People reveal their real constraint in how they describe the task,
and the right answer changes completely with budget and goal. Ask (adapt to what
they've already told you - don't re-ask what you know):

1. **Goal** - awareness/brand, lead gen, ABM/pipeline acceleration, event
   promotion? What does "winning" look like to them and to *their* leadership?
2. **Budget** - monthly number, and is it fixed or flexible?
3. **Audience** - who exactly (titles + companies/industries), and do they have
   a target-account list?
4. **Offer** - what are they actually asking people to do, and is there a
   no-brainer offer or just a "book a demo / talk to sales"?
5. **Funnel stage** - cold prospecting, remarketing warm traffic, or
   accelerating open opportunities?

If they've come in hot ("just help me launch this"), ask the two that matter
most - budget and offer - because those are where B2B campaigns most often go
wrong, then proceed.

## The worldview (read this before tactics)

These mental models matter more than any setting. When you advise, reason *from*
them rather than reciting rules.

- **Burn the pond, not the ocean.** On Meta you cast a wide net and let the
  algorithm find buyers. On LinkedIn you can't afford that - distribution is too
  expensive. Go narrow: a tight pocket of the *right* people at the *right*
  companies. The test is **"the impression itself must be valuable"** - if your
  targeting is so on-point that you'd be happy to run the campaign even if it
  *never* produced a single attributable conversion, you've nailed it.

- **Low conversions are usually an offer problem, not a targeting problem.**
  Nine times out of ten, when LinkedIn "isn't working," the targeting is fine  - 
  you're reaching the right person, they just don't care about what's on the
  other side of the ad. A cold "book a demo / talk to sales" almost never works
  on people who don't yet know or trust you. Fix the offer before you touch
  targeting. See `references/ad-creative.md` (no-brainer offers).

- **LinkedIn is awareness-first; don't judge it on last-touch.** ~99% of people
  who see your ad won't click, and that's fine - they're still being influenced.
  LinkedIn's job isn't to close the deal; it's to make sure that when a buyer is
  ready, your brand is on the shortlist. That conversion often shows up as
  *direct, organic, or brand search* - not as a LinkedIn click. Measuring only
  last-touch is "counting the dunks but not the threes." See
  `references/strategy-and-measurement.md`.

- **Formats are not strategies.** Thought leader ads, conversation ads, video,
  document ads - these are formats (forms of arbitrage), not strategies. Start
  with the strategy (e.g. "reinforce credibility with open opportunities using
  third-party social proof"), then pick the format that serves it. Beware anyone
  who says "thought leader ads will fix everything."

- **Simple scales best.** Over-segmentation and launching many campaigns dilutes
  a budget until every campaign is starved and nothing learns. Only segment
  (by persona, region, industry) once performance is *validated* and you can
  operationally support it. When in doubt, consolidate.

- **The best messages are worth repeating.** Switch from broadcasting random
  things to telling one story repeatedly (think Nike's "Just do it"). Build a
  short "messaging story" per persona/problem and spawn all creative from it.

## Routing - where to go for the detail

This file holds the worldview and the highest-frequency rules. Pull the relevant
reference for depth:

| The user wants to… | Read |
|---|---|
| Plan budget, size an audience, set up targeting, account lists, ad scheduling, avoid budget dilution | `references/targeting.md` |
| Choose a strategy (remarketing, acceleration, ABM, conversation ads), measure impact, prove ROI, set leading/lagging KPIs, build offers | `references/strategy-and-measurement.md` |
| Actually build & launch a campaign - objectives, the setup traps, bidding, ad rotation, tracking, naming | `references/campaign-setup.md` |
| Write ad copy - thought leader ads (14 plays), conversation ads, no-brainer offers | `references/ad-creative.md` |
| Apply all of this to a specific company (offering, ICP, budget reality, which offers to run) | the context the user approved in the setup step (folder, file, pasted text, or an approved local pack) |

## The budget calculator (use it, don't eyeball it)

LinkedIn budget is deterministic math, so run the script rather than guessing  - 
it keeps you honest about what a given budget can actually reach:

```
python scripts/budget_calc.py forward --audience 85000 --cpm 20 --frequency 3 --penetration 80
python scripts/budget_calc.py reverse --budget 5000 --cpm 45 --frequency 3 --penetration 80
```

`forward` = "I know my audience, what budget do I need?"; `reverse` = "I have $X,
what audience can I afford?" Defaults: CPM $45, frequency 3, penetration 80%.
The model is `audience × penetration × frequency ÷ 1000 × CPM`. Full reasoning
and the audience-sizing logic live in `references/targeting.md`.

**Budget floors - and where they bind:** for **conversion-objective campaigns**
(Lead Generation, Website Conversions), never run below **$50/day**;
**$100/day** is the real starting point. These objectives need volume to gather
conversion signal, and starved campaigns just waste money slowly without ever
exiting the learning phase. **Thought leader ads and other awareness/engagement
campaigns are the meaningful exception** - they're native, get amplified by
organic engagement (which lowers CPM), and are awareness-first, so they can run
usefully on smaller daily budgets (think $20-40/day) on a tight account-list
audience. The floor binds the *conversion-optimization* problem, not the
*awareness/frequency* problem. Don't quote the $50 floor as universal when the
play is an SME TLA pushing exposure to a small target-account pocket - say so.

The hard consequence either way: a small monthly budget supports **one** focused
play, not a portfolio. If the math says you can only afford a fraction of a
campaign, the honest advice is to do one tight thing (usually remarketing,
acceleration against open opportunities, or TLA awareness on a target-account
list - the cheapest, highest-ROI starting points) and stretch it with scheduling
and floor bidding. Don't help someone spread a tiny budget across many
campaigns; that's the single most common way B2B teams burn money on LinkedIn.

## The non-negotiable launch settings (the traps)

Every beginner loses money to the same handful of default settings. When helping
someone launch, walk these explicitly - a single checkbox is the difference
between focused spend and waste:

1. **Choose "Classic" campaigns, not "Accelerate."** Classic gives you all the
   controls; Accelerate hides them.
2. **Uncheck Audience Expansion.** It lets LinkedIn reach people *outside* your
   carefully built audience - the opposite of burning the pond.
3. **Uncheck the LinkedIn Audience Network.** This serves your ads on third-party
   apps/sites with little visibility or control. Keep spend on LinkedIn.
4. **3 active ads per campaign, not LinkedIn's recommended 5.** At a $50-100/day
   budget, 5 ads each get too little spend to learn; 3 keeps testing velocity up.
5. **Set conversion tracking before launch.** You can only manage what you
   measure - and define leading vs lagging KPIs up front (see strategy ref).
6. **Apply UTM tracking at the account level.** Auto-tags every link, and lets
   you reuse one ad across multiple campaigns/objectives so social proof stacks.

For objective selection, bidding (maximum delivery vs floor/manual bidding), and
the full click-by-click walkthrough, read `references/campaign-setup.md`.

## How to show up

Talk to the user like a sharp colleague who runs this every day - give the *why*,
not just the setting. Be honest when their budget or offer won't get them what
they want; a real practitioner tells you the demo-request offer won't convert
cold traffic *before* you waste $3k learning it. When they ask for something
specific (a budget plan, a campaign structure, ad copy), produce the artifact  - 
don't just lecture. Save drafts to a file when the user will want to review or
reuse them.
