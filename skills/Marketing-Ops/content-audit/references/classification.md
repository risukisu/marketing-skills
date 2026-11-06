# Classification rubric

Every content page gets one row: an **offering**, an **AIDA stage**, a **content type**, an
**audience fit**, a **confidence** and a piece of **evidence**. Subagents classify; Python counts.
This file is the whole brief a subagent needs, together with `taxonomy.json` and its batch file.

## The offering

Use the ids in `taxonomy.json`, plus three reserved values:

| Value | Use it when |
|---|---|
| an offering id | The page is about what that offering sells, or about a problem only that offering solves. Apply the offering's `includes` and `excludes` lists literally. |
| `cross` | The page serves every offering equally: homepage, general contact, pricing overview, "why us", company-wide case study hub. |
| `brand` | Company and community content with no offering behind it: culture, hiring stories, office news, awards, events recaps, charity work. |
| `none` | Content that fits no offering and is not about the company: generic tutorials, news commentary, topics the company does not sell. |

Rules:

1. **Pick the offering a buyer of that offering would recognise the page as theirs.** A tutorial on a
   tool the company uses, but does not sell work around, is `none`, not the nearest offering.
2. **One primary offering.** If a page clearly serves two, put the second in `secondary_offering`.
   Never put the same id in both.
3. **Do not stretch an offering to absorb volume.** A large pile of `none` pages is a finding, not
   a classification failure.

## The AIDA stage

The stage is the page's **main job for a buyer**, judged from the title, H1, H2s and text. Ask which
question the page answers.

| Stage | The buyer's question | Typical pages | Tell-tale signs |
|---|---|---|---|
| **Attention** | "What is this problem, and does it matter to me?" | Educational posts, explainers, trend pieces, definitions, news commentary, how-to tutorials | Vendor-neutral; the company's services are absent or a footnote |
| **Interest** | "How could this be solved, and what are my options?" | Approach comparisons, methods, frameworks, buyer's guides, evaluation checklists (ungated), webinars on approaches, "build vs buy" | Compares ways of solving the problem; still mostly vendor-neutral, but closer to a purchase |
| **Desire** | "Why this company?" | Service and product pages, case studies, testimonials, pricing, "us vs them" comparisons, methodology pages, team or about pages that argue expertise | The company is the subject; proof, outcomes, differentiation |
| **Action** | "How do I raise my hand?" | Contact, demo or consultation booking, quote request, gated download landing pages, newsletter or webinar sign-up, free trial | The page's main purpose is a form, a booking or a sign-up |

Decision rules, applied in order:

1. If the page's main purpose is to capture a name or an email (the form is the point of the page),
   it is **Action**, whatever its topic. A blog post with a newsletter box in the sidebar is not Action.
2. If the company or its offering is the subject of the page, it is **Desire**.
3. If the page compares approaches, tools or ways to solve a problem, it is **Interest**.
4. Otherwise it is **Attention**.

When torn between two stages, pick the earlier one and set confidence to `med`.

## Content type

One of: `homepage`, `service`, `product`, `solution`, `industry`, `pricing`, `case-study`, `testimonial`,
`comparison`, `blog`, `guide`, `whitepaper-ebook`, `webinar-event`, `video-podcast`, `research-report`,
`glossary`, `docs`, `tool-calculator`, `landing`, `contact-demo`, `newsletter`, `about-team`, `news-pr`,
`careers`, `partner`, `other`. The batch's `type_hint` comes from URL patterns; confirm or correct it.

## Audience fit

| Value | Meaning |
|---|---|
| `icp` | Written for the buyer described in `taxonomy.json` (`icp`), or the people who influence that purchase |
| `adjacent` | Same industry or function, but not the buyer (for example practitioners who will never buy) |
| `off` | An audience that will not buy (students, hobbyists, job seekers, a different industry) |
| `unclear` | The page does not say who it is for |

## Confidence and evidence

- `high`: title, H1 and text agree. `med`: the stage or offering needed judgement. `low`: little
  text, or the page could reasonably sit in two places. Low-confidence pages are listed in the report
  for a human check, so use `low` honestly.
- `evidence`: one short phrase taken from the page (title, H1, an H2 or a sentence) that justifies
  the stage and offering. Never invent it. Up to 25 words.
- `note`: optional, for anything a reviewer should know (for example "series part 2 of 4").

## Subagent brief

Send each classification subagent this, filled in (one subagent per batch file):

> You are classifying pages of `{host}` for a content audit. Read
> `{skill_dir}/references/classification.md` (the rubric) and `{run_dir}/taxonomy.json` (the offerings,
> the ICP and the brand terms). Then read `{run_dir}/batches/batch_{NN}.json`: one object per page with
> its id, URL, type hint, title, H1, meta description, H2s, a text excerpt, word count, lead-capture
> signals and body links.
>
> For every page write one row with exactly these keys: `id`, `url`, `offering`, `secondary_offering`
> (or null), `stage`, `content_type`, `icp_fit`, `confidence`, `evidence`, `note`. Use only the values the
> rubric allows. Judge from the batch data; open a page on the web only when the excerpt is empty or
> contradicts the title.
>
> Write the rows as a JSON array to `{run_dir}/labels/batch_{NN}.json` with a file-writing tool, then
> reply with one line: the file path and the number of rows. Do not summarise the pages.

## Worked examples (fictional company: a data consultancy for retailers)

| Page | Offering | Stage | Why |
|---|---|---|---|
| "What is a semantic layer?" | data-platform | Attention | Explains a concept; vendor-neutral |
| "Warehouse vs lakehouse for retailers" | data-platform | Interest | Compares approaches |
| "How a 40-store grocer closed the month in two days" | data-platform | Desire | Proof from the company's own work |
| "The retail data platform checklist" (form to download) | data-platform | Action | The page exists to capture an email |
| "Contact us" | cross | Action | General hand-raise for every offering |
| "Our team offsite" | brand | Attention | Company news, no offering |
| "Twenty spreadsheet shortcuts" | none | Attention | A topic the company does not sell; audience `off` |
