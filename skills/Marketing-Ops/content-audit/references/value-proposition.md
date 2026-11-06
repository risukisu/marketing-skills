# Value proposition clarity

Can a buyer who lands on the page tell what the company offers, for whom, and why it beats the
alternatives? Score the **homepage** and each offering's **main page** (from `taxonomy.json`
`main_pages`) on six criteria, 0 to 2 each, from the page itself.

## Read the page as a first-time buyer

Use the title, H1, H2s and the first screen of text in `crawl.json` (`excerpt` holds the main text in
reading order). Fetch the live page when the excerpt is cut short or empty. Judge what is written,
not what the company could have meant.

## The six criteria

| Key | Question | 2 = clear | 1 = partial | 0 = missing |
|---|---|---|---|---|
| `category` | What is it? | Names the service or product category in plain words in the H1 or first lines | Category inferable, but buried or vague ("solutions", "excellence") | Cannot tell what is sold |
| `audience` | Who is it for? | Names the buyer or the industry and size | Hints at an audience | No audience |
| `outcome` | What changes for the buyer? | A concrete result (time, money, risk, a capability) | A generic benefit ("better insights") | Features only, or nothing |
| `differentiation` | Why this company over another, or over doing nothing? | A specific reason that a competitor could not also claim | A reason that most competitors could also claim | None |
| `proof` | Why believe it? | A named client, a number, a case study, a recognisable logo with a result | Logos or testimonials without a result | None |
| `next_step` | What do I do now? | A specific call to action in the body, matched to the page (book, quote, download) | A generic "contact us" or navigation only | None |

Rules:

- **Every score above 0 needs a verbatim quote** from the page (up to 25 words). No quote, no point.
- **Every 0 needs a note** saying what is missing, in one sentence.
- Score the page, not the company: a strong case study elsewhere on the site does not earn `proof`
  on a service page that does not mention it.
- An offering with no page of its own gets a row with `"url": "none"` and zeros, noted "no page".

## Write `valueprop.json`

```json
{"scopes": [
 {"scope": "homepage", "url": "/", "criteria": {
  "category": {"score": 2, "quote": "…"},
  "audience": {"score": 1, "quote": "…"},
  "outcome": {"score": 1, "quote": "…"},
  "differentiation": {"score": 0, "note": "No reason to choose this company is given."},
  "proof": {"score": 2, "quote": "…"},
  "next_step": {"score": 2, "quote": "…"}}},
 {"scope": "data-platform", "url": "/services/data-platform", "criteria": {"…": {}}}
]}
```

Then run `check_labels.py --run-dir RUN valueprop`. It refuses missing scopes, missing quotes and
unexplained zeros.

## Reading the result

The report shows a 0–2 grid per scope with every quote. In the narrative, name the weakest criterion
across pages (the analyzer computes it) and say what a buyer cannot learn from the site today.
`differentiation` and `proof` are the usual gaps; they are the ones that decide whether Desire pages
convert.
