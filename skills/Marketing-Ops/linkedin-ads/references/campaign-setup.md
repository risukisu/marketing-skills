# Campaign Setup & Launch Walkthrough

The click-by-click for launching without bleeding budget. On LinkedIn, a single
checkbox is often the difference between focused spend and waste - so when you
walk a user through this, be explicit about each trap.

## The hierarchy

**Campaign Groups → Campaigns → Ads.** Groups are folders/tags - organize them
with *some* rhyme and reason (you can rename later). Common schemes:
- By **region** (NA / EMEA / APAC)
- By **funnel stage** (e.g. AdConversion's 5-stage model: Create, Capture,
  Accelerate, Revive, Expand - or simple Tofu/Mofu/Bofu)
- By **offer** (one group for ebook, one for webinar, etc.)

Campaigns hold targeting + objective + budget; ads hold creative.

## Naming conventions matter (LinkedIn reporting is bad)

Reporting keys off your campaign and ad names, so be explicit and consistent.
A simple, durable pattern: `region | objective | ad-type` →
`EMEA | Engagement | ThoughtLeader`. Decide a convention before you launch the
first campaign or you'll regret it at reporting time.

## Choosing the objective

The objective determines what LinkedIn optimizes for and what you're charged for.

| Objective | When to use | Notes |
|---|---|---|
| **Brand awareness** | Maximize distribution at the lowest CPM; get content/event seen, push audience penetration | Cheapest inventory |
| **Engagement** | Drive reactions/comments/shares | Pairs *beautifully* with thought leader ads - more positive engagement signals the auction your ad resonates, which lowers CPM and increases distribution |
| **Website visits** | Pay per click to your site | Tip: pair with Spotlight/Text ads - they get few clicks, so you bank lots of near-free impressions |
| **Video views** | Drive views of a video | Straightforward |
| **Lead generation** | Native in-platform forms, pre-filled from LinkedIn profile → higher form-conversion | Higher CPM; watch lead *quality* - low friction means easy to sign up and easy to ignore |
| **Website conversions** | Drive a conversion action on your site | Higher CPM (conversion inventory is premium) |
| **Talent leads / Job applicants** | Recruiting | Irrelevant for ~99% of B2B marketing |

Conversion-objective campaigns (lead gen, website conversions) cost more - only
run them when the cost-per-lead / cost-per-opportunity actually pencils out.

## The non-negotiable traps (walk these every launch)

1. **Pick "Classic," not "Accelerate."** Classic exposes all controls.
2. **Uncheck Audience Expansion** - it reaches people outside your audience,
   diluting your carefully built targeting. Scale later by *adding attributes*,
   not by handing LinkedIn the wheel.
3. **Uncheck the LinkedIn Audience Network** - serves ads off-platform with poor
   visibility/control. Keep spend on LinkedIn. (If you genuinely want the open
   internet, that's a programmatic/DSP job, not this.)
4. **Apply UTM tracking parameters at the account level.** Auto-tags every link
   (no more manual tagging) *and* lets one ad run across multiple
   campaigns/objectives without duplicating - so social proof (reactions,
   comments) stacks on a single post, improving CPM/CTR everywhere it runs.
5. **Set up conversion tracking before launch** - you can only manage what you
   measure.

## Budget & schedule

- **Daily budget floor depends on objective.** For conversion-objective
  campaigns (Lead Gen, Website Conversions), $50/day is the floor and $100/day
  is the real starting point - below that, conversion signal can't accumulate.
  For thought leader ads and awareness/engagement campaigns the floor binds
  much less; TLAs on a tight account-list audience can run usefully at
  $20-40/day because they're awareness-first and ride organic engagement to
  lower CPMs. See `references/targeting.md` for the full rule.
- **Set a campaign-group total budget cap as a hard safety net.** Even after
  you've set a daily budget, the group-level total cap is the only thing that
  *guarantees* you can't overspend the whole pot - useful if a daily budget
  gets fat-fingered or pacing surprises you. Always set one on a first campaign.
- **LinkedIn can spend up to ~20% over your stated daily budget on
  high-traffic days.** It averages out over the month, but any single day can
  overshoot. If a daily cap is critical, set the daily budget ~20% lower than
  your true ceiling, and rely on the group total cap as the real backstop.
- **Always set an end date.** Don't leave campaigns running open-ended;
  campaigns that outlive the offer (e.g. a webinar that's already happened) are
  the silent way budget vanishes.
- **Ad schedule:** LinkedIn has no native dayparting; use a third-party tool to
  concentrate spend on business days/hours if budget depletes early (see
  `references/targeting.md`, "Stretching a small budget").

## Bidding

- **Maximum delivery (default)** is fine for awareness / engagement / video
  views - let LinkedIn spend efficiently.
- **Manual / floor bidding** to arbitrage cost: set the bid at the floor (LinkedIn
  will warn it's "too low" - fine), launch, watch reach/spend, then ramp up
  incrementally (e.g. $1 → $1.30 → $1.50) to find the equilibrium between reach
  and cost. More work, but worth it on expensive conversion/lead-gen campaigns.

## Ads

- **3 active ads per campaign** (not LinkedIn's recommended 5). At $50-100/day,
  5 ads split spend so thin that each learns too slowly; 3 keeps testing velocity
  up and gets each enough volume before you judge it.
- **Ad rotation:** "Optimize for performance" lets LinkedIn favor the front-runner
  (can starve a variation before you can judge it). "Rotate evenly" forces equal
  delivery for clean comparison. Reasonable approach: start with rotate-evenly to
  gather fair data, or start optimized and switch to even if delivery is lopsided.
- **Thought leader ads:** in the ad setup, "browse existing content" → pick a
  company post *or* a LinkedIn member's post (with their approval) - founder,
  employee, customer, or partner. The member route is where the magic is (see
  `references/ad-creative.md`).

## Post-launch hygiene

- **Audit the demographics report** - confirm you're serving the titles and
  companies you intended; build exclusions to remove junk (multiple-open-roles
  problem). See `references/targeting.md`.
- **Catch wasted spend fast** - decide kill criteria up front (e.g. pause an ad
  that spends 2-3x target CPL with no conversion); overspend on losers compounds
  silently.
- **Optimize the leading KPIs** (CPM, engagement rate, account penetration) while
  the lagging ones (pipeline, revenue) mature over the sales cycle.
