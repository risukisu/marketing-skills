# Diagnosis rules

`analyze.py` applies these rules; this file explains them so the narrative can, too. Thresholds are
the defaults in `analyze.py` `DEFAULTS` and can be overridden per run with `--config thresholds.json`.
The report's method section prints the values used.

## The grid

Rows are the confirmed offerings (diagnosed) plus `cross`, `brand` and `none` (context rows, shown
greyed, never diagnosed). Columns are the four AIDA stages. Each page counts once, under its primary
offering.

### Cell status

| Status | Rule |
|---|---|
| `missing` | No page at this stage |
| `shared` | Action only: no offering-specific Action page, but the offering's pages link in the body to a cross-offering Action page (general contact form). Treated as covered |
| `thin` | Fewer pages than the minimum for the stage: Attention 5, Interest 3, Desire 2, Action 1 |
| `ok` | At or above the minimum |

### Cell flags (on top of the status)

| Flag | Rule | Needs |
|---|---|---|
| `invisible` | The cell's pages have zero search impressions together (not used for Action) | Search Console export that is not truncated |
| `not-in-export` | None of the cell's pages appear in a truncated Search Console export: unknown, not zero | Search Console export at its row limit |
| `disconnected` | Under 50% of the cell's pages have an onward step | Crawl only |
| `no-capture` | Action pages exist but none has a form, booking link or email link | Crawl only |

**Onward step:** an Attention or Interest page has one when it links in the body to a Desire or Action
page of the same offering (or a cross-offering one), or carries a form or booking link itself. A
Desire page has one when it links in the body to an Action page, or carries a form or booking link.
Links in the header, navigation, sidebar or footer do not count: every page has those, and buyers
reading an article do not use them as the next step.

## The verdicts per offering

Each check is either assessed (gap or no gap, with evidence) or not assessed (with the data it needs).

| Check | Flags a gap when | Needs |
|---|---|---|
| **Content gap** | Any stage is missing or thin | Crawl |
| **Conversion path gap** | Attention, Interest or Desire is disconnected; or Action is missing; or Action pages have no capture | Crawl |
| **Findability gap** | The offering's share of search impressions is under half its share of pages (both counted among offering pages only, so an off-ICP tutorial cannot distort it); or its Desire pages have zero impressions, or an average position worse than 20 | Search Console pages |
| **Conversion gap** | With at least 100 sessions: key-event rate under half the site's rate, or zero first-touch contacts | GA4 key events or HubSpot |
| **Distribution gap** | With at least 100 sessions: under 10% of the offering's sessions come from channels other than organic search and direct (email, social, referral, paid) | GA4 with the channel dimension |
| **Paid reliance** (information) | Ads clicks are over 60% of ads plus organic clicks on the offering's pages | Google Ads and Search Console |

**Primary gap**, in this order, first flagged wins: content → conversion path → findability →
conversion → distribution. The order follows what has to be true first: a page that does not exist
cannot be found, and traffic to a page with no next step cannot convert. "Working" means every check
was assessed and none flagged; "partial read" means nothing flagged but some checks lacked data.

## What each gap means for investment

| Primary gap | The problem | Where money and time go | Next skill |
|---|---|---|---|
| Content gap | The content a buyer needs at that stage does not exist | Create content for the missing stage of that offering, Desire and Action first | `/content-strategy` (plan), `/seo-content-brief` (briefs), `/lead-magnets` (Action assets) |
| Conversion path gap | Pages exist but do not lead to the next step | Calls to action, body links, Action pages, forms | `/cro`, `/internal-linking` |
| Findability gap | Content exists but buyers do not find it in search | SEO on existing pages before new ones | `/seo-page`, `/seo-cluster`, `/internal-linking`, `/seo-technical` |
| Conversion gap | Traffic arrives and does not convert | Offer, proof, calls to action on the pages with traffic | `/cro`, `/customer-research` |
| Distribution gap | Good, findable content reaches too few people | Email, social, partners, paid amplification of proven pages | `/linkedin-ads`, `/content-strategy` (distribution part) |
| Value proposition gap (from the 0–2 grid) | Buyers cannot tell why this company | Messaging on homepage and service pages | `/customer-research`, `/cro`, `/copy-longform` |

Name a skill in the report only if the user has it; the library ships all of the above.

## Site-wide reads

- **Audience fit:** share of pages and of impressions by `icp_fit`. A site whose impressions come
  mostly from `off` pages has traffic that looks healthy and produces no pipeline.
- **Freshness:** last published or updated year per page; share older than 24 months.
- **Duplicates:** pairs of pages in the same offering whose title words overlap by 75% or more, a
  consolidation candidate list (title overlap is a hint; check the pages).
- **Close to page one:** pages at position 4 to 20 with at least 100 impressions, not Action.
- **Branded vs non-branded demand:** query share containing a brand term. Mostly branded clicks means
  search brings people who already know the company; content is not creating new demand.
