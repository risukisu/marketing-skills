# Targeting, Audience Sizing & Budget

The whole game on LinkedIn is precision, because you're paying a premium for
every impression. This file covers how to build the right audience, size it,
and translate that into a budget that can actually do something.

## Build the audience in the Audience Insights tool first

Before spending a dollar, preview the audience. In the LinkedIn Campaign Manager,
go to **Plan → Audiences → Saved audiences → Create audience** (the Audience
Insights tool). Adjust targeting and watch the estimated audience size update
live. Save it as a saved audience so it's reusable across campaigns.

LinkedIn has 255+ targeting attributes. The ones that matter most for B2B:
- **Job titles, seniority, function** - what the person does.
- **Company** - by name (via lists), industry, size, growth.
- **Member skills, groups, schools, degrees** - secondary refinements.

### The single most important targeting move: upload an account list

Combine a **company list + job titles**. This is what makes LinkedIn worth its
premium. Even if you're *not* doing formal ABM, upload a list of target
accounts, because of the **multiple-open-roles problem** (below). Without it you
will pay premium CPMs to reach junk.

Upload via **Plan → Audiences → Matched audiences → Create → Company list**
(CSV of company names + domains). This can be automated from a CRM to stay
dynamic. Then layer titles on top. Result: a much smaller audience, but every
impression lands on someone who matters.

### The multiple-open-roles trap ("super titles")

LinkedIn mixes and matches a person's *multiple* current roles. Someone who is a
Software Engineer at a big company but also lists themselves as "Founder" of a
side project becomes eligible for *both* engineer and founder targeting. So if
you target "CMOs at Fortune 100," you can end up serving a junior IC who happens
to also run a tiny side company. Two defenses:
1. **Upload an account list** so company is pinned down, not inferred.
2. **Audit the demographics report** after launch - check which titles and
   companies you actually served, and build **exclusions** to hack away the
   irrelevant ones over time. Don't trust that targeting is perfect.

## Audience sizing

- **Sweet spot: under ~250,000.** Above that you almost always have room to
  tighten (add an account list, narrow titles). Bigger is not better here.
- You *may* break the 250k rule only if the audience is genuinely on-point and
  you're happy with the quality you see in the preview.
- For small budgets, much smaller is good - a 30-50k pocket of account-list ×
  titles is a strong, affordable starting audience.

## The budget model

Required monthly budget to saturate an audience:

```
impressions = audience_size × (penetration % ÷ 100) × frequency
monthly_budget = (impressions ÷ 1000) × CPM
```

Inputs and starting points:
- **Audience size** - from the Insights tool.
- **CPM** - ranges $20 (large audience) to $90+ (tiny audience). Lower audience
  size → higher CPM. If you've run ads already, use your actual CPM.
- **Frequency** - how often each person sees your ad. Start at **3** (bare
  minimum 1; for ABM reaching multiple people per account, 3+ matters).
- **Penetration** - what % of the audience you reach. **80% minimum**, 60%
  floor - don't go lower or you're barely showing up.

**Always run the script instead of doing this by hand:**
```
python scripts/budget_calc.py forward --audience 85000 --cpm 20 --frequency 3 --penetration 80
python scripts/budget_calc.py reverse --budget 5000 --cpm 45 --frequency 3 --penetration 80
```
`forward` = audience → budget needed. `reverse` = budget → max affordable
audience. Worked example: 85k audience × 80% × 3 ÷ 1000 × $20 = **~$4,000/mo**.

CPM is the "vanity metric that actually matters" - at $20 CPM that 85k audience
needs $4k; at $30 CPM it needs $6k. Once live, you can optimize CPM down (e.g.
testing brand-awareness vs engagement objectives) to reach more people for the
same money.

### Daily budget floors and what a budget can actually support

The floor is **objective-specific** - treat it as a rule for conversion-optimized
campaigns, not a universal law.

- **Conversion-objective campaigns** (Lead Generation, Website Conversions):
  never below **$50/day**; **$100/day** is the real starting point. These need
  volume to accumulate conversion signal; below the floor, ads can't exit the
  learning phase and you waste money slowly.
- **Thought leader ads and awareness/engagement campaigns**: the floor binds
  much less. TLAs are native, ride organic engagement to lower CPMs, and are
  measured on frequency-on-target-accounts rather than conversion-signal speed.
  On a tight account-list audience (say 5-30k), a TLA running awareness or
  engagement can produce meaningful frequency at **$20-40/day** - lower than the
  conversion floor and still useful. The constraint is "did the right people see
  it enough times," not "did the algorithm find converters."
- Quick capacity math: `monthly ÷ 30.4 = daily`; for conversion campaigns
  `daily ÷ 100` (or `÷ 50` at the floor) tells you how many you can sustain.
  For TLA/awareness, you can sustain at much lower per-campaign daily spend, but
  the consolidation rule still holds - one well-fed campaign beats five starved
  ones at any objective.

### The Insight Tag prerequisite (for retargeting audiences)

You can't retarget website visitors unless the LinkedIn Insight Tag has been
firing on your pages first - and a website audience needs roughly **300+
members** before LinkedIn will serve ads to it. Check this before promising
anyone a remarketing campaign:

1. In Campaign Manager: **Analyze -> Insight Tag** - confirm it's installed and
   "Active / Receiving data." If not, install (one snippet in `<head>` or via
   Google Tag Manager) and *wait* - the audience pool builds forward from
   install, not retroactively.
2. After it's live, build the Website audience in **Plan -> Audiences -> Matched
   audiences -> Website**. Check the member count there.
3. If you're under 300, the campaign cannot launch yet. Either broaden the URL
   rule (e.g. all `/services/*` not just one page), wait for more visitors, or
   run an engagement/awareness campaign first to seed the pool.

The advice that follows in this file assumes the tag is already live. If it
isn't, that's task one - everything else has to wait.

## Stretching a small budget

When budget is tight (the common case for B2B services), these tactics matter
more than anything fancy:

1. **Focus targeting** (account list × titles) - covered above. Non-negotiable.
2. **Ad scheduling.** LinkedIn has no native dayparting, so use a third-party
   tool. Concentrating $100/day across Mon-Fri instead of 7 days ≈ +50%
   effective daily budget; restricting to ~8 business hours instead of 24 can
   effectively multiply it further. If your budget depletes by midday anyway,
   you're already losing the afternoon - scheduling just makes that intentional.
3. **Manual / floor bidding.** LinkedIn's suggested bid is usually higher than
   you need. Start bids at the floor (e.g. $1), launch, watch reach and spend,
   then ramp up incrementally to find the equilibrium between reach and cost.
   This arbitrages the auction. Worth the manual effort especially on
   conversion/lead-gen campaigns where CPCs are expensive; for
   awareness/engagement, maximum delivery is usually fine.
4. **Avoid budget dilution.** The classic failure: $20/day on a campaign with a
   $15 CPC = one click, then you're done - it takes forever to gather signal.
   Consolidate: pause the also-rans and pour budget into the one campaign that
   can actually learn ($100-200/day).
5. **Catch wasted spend fast.** Decide the cost target up front (e.g. "kill an ad
   if it spends 2-3x the target cost-per-lead with no conversion"). Without
   active monitoring, overspend on losers silently compounds. Automation (hourly
   checks that pause or alert) helps, but the discipline is the point.

## When to segment (and when not to)

Segmentation (separate campaigns by persona / region / industry / product) is
only worth it when **performance is validated** and you can operationally support
it. Example: only split out an industry into its own targeting once you know it
converts at a higher win rate with better deal sizes. Until then, consolidate so
you can test and learn faster. Complexity scales badly - "you can't scale
complicated," whether you're spending $1k or $1M a month.
