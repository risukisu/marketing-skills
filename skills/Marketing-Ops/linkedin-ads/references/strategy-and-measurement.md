# Strategy, Offers & Measurement

This file covers *what* to run and *how to prove it worked* - the parts that
separate teams who dominate LinkedIn from teams who quietly defund it. Pick the
strategy first; the format and settings serve the strategy, never the reverse.

## Starter strategies, cheapest-ROI first

For B2B services with long, sales-led cycles, these are the tried-and-true
starting points. With a small budget, do *one* of these well rather than several
badly.

### 1. Acceleration campaigns (best ROI, lowest budget)
Run ads **only against your open opportunities** - the people already in
conversations with sales. Cheap (budget scales with how many open opps you have)
and proven to improve win rates and shorten cycles. Two motions:
- **Social proof**: testimonials, case studies, customer wins - reinforce that
  you're the right choice.
- **Objection handling**: pre-empt the deal-killers (e.g. promote a pricing or
  ROI resource if pricing is the common objection).
Who's easier to convert than people already talking to your sales team? Start
here when you need ROI fast.

### 2. Remarketing (the "keep the party going" play)
Target people who already engaged - website visitors, company-page visitors, ad
engagers, video viewers. Critical for B2B because **timing is the enemy**: it can
be exactly the right person at the wrong moment. Remarketing keeps you present
until they're ready. Treat it as **relationship-building, not a follow-up
sequence** - nobody opted into being chased, so every touch must earn its place.
- **Split budget ~50/50 between content and offers.** Half adds value (social
  proof, product/explainer videos, thought leadership), half asks for action.
- **Be a sniper with demo/call asks** - only retarget high-intent page visitors
  (pricing, specific service pages, case studies), not everyone who ever visited.
- Don't pause remarketing because it looks weak on last-touch - it almost always
  does, and that's the wrong scorecard (see measurement below).

### 3. ABM / account-based (the precision play)
Upload a target-account list, layer titles → small, high-quality audience. For a
fast-ROI pilot: a **one-to-one ABM** motion on your top 30-50 accounts - one
campaign per company, call the company out by name in the creative, and have
sales outreach the *same* accounts in parallel. Focus on closing the deal, not
on assigning attribution credit.

### 4. Conversation ads (direct-response format, best in remarketing)
A message that lands in the prospect's LinkedIn inbox with branching CTAs. Tends
to convert better than image/video, *especially in remarketing* where there's
already familiarity. Use it as the "ask" half of a remarketing strategy.

A solid two-campaign starter for a warm audience: **thought leader ads** (build
affinity, native feel) + **conversation ads** (drive the next step). See
`references/ad-creative.md`.

## Offers - the highest-leverage thing you can fix

If conversions are low, it's almost always the offer, not the targeting. A cold
"book a demo / talk to sales" asks people who don't know you to take a
high-friction step toward a sales pitch. They predict what "demo" means (30 min,
a rep, a pitch) and bounce.

**Build a no-brainer offer** - a low-friction, genuinely valuable thing that
solves a *specific, felt* problem and positions you as the logical next step:
- **Narrow beats broad.** A broad problem gets a nod; a specific felt pain gets
  action. Ask: "what is the specific problem my ICP is frustrated about *this
  week*?" - start there, not "what should we gate?"
- **Match format to the time-to-value you're promising.** Checklists/templates
  signal immediate value; webinars/guides signal a time investment (and "webinar"
  already screams high-commitment before they've seen any value). Use the format
  that fits the promise.
- **Make them feel progress immediately** - even just *clarity* counts. If they
  leave seeing their problem in a new light, you're the brand that gave them
  that.
- **The rule of thumb: don't create something you wouldn't pay for.** If you
  wouldn't find it valuable, neither will they.

**Reposition the meeting itself.** The offer matters less than how it's framed.
"Book a demo" is what every competitor says. Name what the prospect actually
walks away with: if your call is really a teardown/assessment that reveals blind
spots and hands them a rollout plan, *sell that* ("free architecture review,"
"data-workflow teardown"), not "demo." Same meeting, completely different
perceived value, and a pattern interrupt in a sea of "book a demo."

**Messaging stories.** Map, per persona, the jobs-to-be-done and the one
overarching story that frames your solution (e.g. AdConversion sells Sammy as
"Zapier for ads" - instantly understood). Spawn all creative from the story so
everything reinforces one idea instead of broadcasting noise.

## Measurement - prove ROI without lying to yourself

LinkedIn is awareness-first. Measuring it on last-touch is the single biggest
reason good programs get killed. Educate leadership on this *before* launch, not
at the first budget review.

### Leading vs lagging KPIs (separate them)
- **Leading** (days): impressions on target accounts, engagement rate, account
  penetration, frequency, CTR. These are your proxy/control metrics - what you
  optimize toward week to week.
- **Lagging** (one full sales cycle): pipeline, SQLs, closed revenue. These take
  4-6 months for enterprise B2B, so you can't steer on them in-flight.
Define both up front, and frame the leading metrics as the proxies for the
lagging ones (the Netflix logic: optimize the things you *can* control that
predict the outcome you care about).

### The three levels of attribution (do them in order)
Most teams skip 1 and 2 and rush to buy a tool - which then "doesn't work"
because the foundations aren't there.
1. **Consistent UTMs across sessions** → ad UTM passes to the form → into the CRM
   → through lifecycle stages, so lead source is preserved. Foundational; fix
   this first.
2. **A simple source-of-truth / revenue dashboard.** Pull CRM + ad-channel data
   (paid, organic, direct - ignore unrelated channels) and watch the **halo
   effect**: as you run more awareness, direct/organic/brand-search conversions
   rise. Favorite blended metric: **pipe-to-spend** ("for every $1 in, how much
   pipeline back?"). If blended pipe-to-spend climbs quarter over quarter, your
   awareness is working - lean in. No fancy tool needed; a Looker dashboard or
   exports suffice.
3. **Multi-touch attribution tool** - only once 1 and 2 are solid and you need
   account-journey detail and multiple attribution models.

### Self-reported attribution (cheap and powerful)
Add a "How did you hear about us?" field to every conversion form. When LinkedIn
starts showing up there, that's direct evidence it's working. Reinforce with
call-recording keyword tracking (flag when prospects mention LinkedIn on calls).
These qualitative signals often tell the truth that last-touch data hides.

### Cross-reference for target-account proof
For ABM, cross-reference companies that booked meetings (via direct/organic/brand
search) against your LinkedIn impression data: "how many impressions did these
accounts get in the last 90 days?" That overlap is your proof point.

## Design the experiment before you spend

Get clear on the hypothesis first, so that when leadership inevitably asks "is it
working?" you're ready. The cleanest approach for ABM: **incrementality test**.
Split your target list 50/50 - an **exposed** group that gets ads and a
**holdout** that doesn't. Then compare everything across the two: outbound email
open/response rates, connect rates, meetings booked, pipeline created, win rate,
sales-cycle length. This gives you a control group, so performance is measured
*relative to* something - and "performance is only relative to what it's compared
against" is the lesson most people learn too late. A $50 cost-per-lead is
meaningless until you know whether your norm is $5 or $500.

## Don't let tech outrun fundamentals

A Formula 1 car with no driver goes nowhere. Intent data, attribution tools, and
automation don't fix weak media planning, fuzzy KPIs, no messaging story, or a
bad offer. Get the fundamentals right first; tech amplifies good fundamentals and
does nothing for bad ones.
