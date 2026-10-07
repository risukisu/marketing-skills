# Internal linking rules

Ten checks every proposed link and every finding is held against. Distilled from Surfer's
"Internal Linking for SEO" and "SEO Best Practices" guides and the Google Search Central
guidance they cite (crawlable links, descriptive anchors, link architecture, John Mueller on
link stuffing), in this skill's own words.

## Contents

- Rule 1: relevance first
- Rule 2: value, not volume
- Rule 3: descriptive, concise anchors
- Rule 4: vary anchors to the same target
- Rule 5: important links high on the page and from the homepage
- Rule 6: authority flows downhill
- Rule 7: no link stuffing, no all-to-all
- Rule 8: no orphans
- Rule 9: keep links valid
- Rule 10: text links, crawlable
- Proposal checklist

## Rule 1: relevance first

Link only between pages that share a topic. Interlinked pages around a pillar tell search
engines the site covers the topic in depth. A keyword match alone is not relevance.

**Check:** the source page's title or headings share a term or a clear sub-topic with the target.
The analyzer's `shared_terms` is the hint, not the verdict; read both titles and decide.

## Rule 2: value, not volume

A link exists for the reader at that point in the text. If the sentence has to be bent to hold
the link, write a new sentence that earns it. Never attach a link to an unrelated sentence.

**Check:** the draft sentence reads as something the page would say without the link.

## Rule 3: descriptive, concise anchors

The anchor says what the target is about in a few words. Banned: "click here", "here", "read
more", "learn more", "this", "this post", "link", "more", "website", bare URLs, empty anchors
on image links.

**Check:** the anchor could stand as the target's short title. Three to seven words.

## Rule 4: vary anchors to the same target

Different source pages use different natural phrasings for the same target. The same anchor on
every inbound link reads as manipulation and tells the crawler less.

**Check:** across the proposals for one target, no two anchors are identical; vary with
synonyms and sentence fit, not keyword stuffing.

## Rule 5: important links high on the page and from the homepage

Links in the body, early on the page, carry more than footer or sidebar links. The homepage
should link in its body to the pages that matter most; navigation menus are not a substitute.

**Check:** proposals for priority pages prefer body placement on high-authority sources and,
where it fits, a homepage body link. Nav and footer are the fallback, not the plan.

## Rule 6: authority flows downhill

Old, well-linked, well-ranking pages should link to new and under-linked pages. A new page
linking out to old ones does not help the new page.

**Check:** sources in the plan are above the target in internal PageRank, or at least not far
below it.

## Rule 7: no link stuffing, no all-to-all

If every page links to every page there is no structure, and the crawler cannot tell which page
matters for a topic. Hierarchy (home → category → page) beats a mesh. Space links out with text
between them.

**Check:** the plan adds at most 5 new links to any one source page; no suggestion links a
cluster's pages to each other exhaustively; a page over the outbound threshold gets removals
suggested, not additions.

## Rule 8: no orphans

Every page meant to rank needs inbound links from indexable pages. A sitemap entry is not a link.

**Check:** every orphan in the report gets at least 2 proposed sources; near-orphans get at
least 1 body link.

## Rule 9: keep links valid

Links to 404s, redirect chains, and moved pages waste crawl and authority. After merges and URL
changes, update the links; redirect the old URL as well.

**Check:** every broken target in hygiene has a fix (update the link, restore the page, or
redirect); every redirected target has its sources pointed at the final URL.

## Rule 10: text links, crawlable

Plain `<a href>` links with text. Links built by JavaScript only, links behind forms, and
`nofollow` internal links do not pass authority.

**Check:** nofollow on internal links is flagged for removal unless the target must not rank;
a JavaScript-rendered site is reported with the crawler's limit stated.

## Proposal checklist

Copy this into the response and tick each line before handing back the report:

```
Proposal check:
- [ ] Every proposal names source, target, anchor, draft sentence, reason
- [ ] Every orphan has ≥ 2 sources; every near-orphan ≥ 1 body link
- [ ] No source page gets more than 5 new links
- [ ] No anchor is generic; anchors to one target differ
- [ ] No proposal duplicates an existing link
- [ ] No all-to-all cluster linking
- [ ] Sources sit at or above the target in internal authority, or the reason says why not
- [ ] Every broken and redirected target has a fix
```
