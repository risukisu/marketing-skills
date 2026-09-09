# Google SEO Best Practices Checklist

Distilled from Google's official Search documentation (developers.google.com/search/docs), with focus on the "Creating helpful, reliable, people-first content" guidelines and the SEO Starter Guide.

Use this checklist to evaluate a website and generate actionable recommendations. Each section maps to a part of the SEO report.

## Table of Contents

1. [Content Quality (E-E-A-T)](#content-quality)
2. [Helpful Content Self-Assessment](#helpful-content)
3. [The "Who, How, Why" Framework](#who-how-why)
4. [Technical Fundamentals](#technical)
5. [On-Page SEO](#on-page)
6. [Crawling & Indexing](#crawling)
7. [Mobile Usability](#mobile)
8. [Page Experience & Core Web Vitals](#page-experience)
9. [Structured Data](#structured-data)
10. [Link Quality](#links)
11. [Common SEO Myths (What NOT to Recommend)](#myths)
12. [Common SEO Pitfalls](#pitfalls)

---

## 1. Content Quality (E-E-A-T) {#content-quality}

Google's ranking systems reward content that demonstrates **Experience, Expertise, Authoritativeness, and Trustworthiness**.

### Experience
- Does the content show first-hand experience with the topic?
- Are there original insights, data, images, or examples the creator actually produced?
- Would a reader say "this person has actually done/used/tried this"?

### Expertise
- Is the content produced by someone with demonstrable knowledge?
- Is there evidence of depth — not just surface-level coverage?
- For YMYL topics (Your Money or Your Life — health, finance, safety), is there professional-level expertise?

### Authoritativeness
- Is the site recognized as a go-to source for this topic?
- Do other reputable sites link to or reference this content?
- Is the author identifiable and credible?

### Trustworthiness
- Is the site secure (HTTPS)?
- Is there clear contact information, about pages, privacy policy?
- Are claims sourced and factual?
- Is advertising clearly separated from content?

**What to check in GA4:** High engagement rates and returning visitors on topic-focused content clusters suggest E-E-A-T signals are working. Low engagement on cornerstone content is a red flag.

---

## 2. Helpful Content Self-Assessment {#helpful-content}

Google's helpful content system evaluates whether content is **made primarily for people**, not to manipulate search rankings. These are the questions Google recommends asking:

### Content and quality questions
- Does the content provide substantial, original information, research, or analysis?
- Does the content provide a complete description of the topic?
- Does the content provide insightful analysis beyond the obvious?
- If the content draws on other sources, does it add substantial value beyond just copying?
- Does the main heading or page title provide a descriptive, helpful summary?
- Is this the sort of page you'd want to bookmark, share, or recommend?
- Would you expect to see this content in a printed magazine, encyclopedia, or book?

### Expertise questions
- Does the content present information in a trustworthy way (clear sourcing, author expertise, background about the site)?
- Would someone researching this site come away thinking it's well-established and recognized?
- Is the content written by an expert or enthusiast who demonstrably knows the topic well?
- Is the content free of easily verified factual errors?

### Presentation and production
- Is the content well-produced and free of spelling/style issues?
- Was care put into producing the content, or does it appear sloppy or hastily produced?
- Is the content mass-produced or outsourced to a large number of creators where individual quality suffers?
- Does the content have an excessive number of ads that distract from the main content?
- Does the content display well on mobile devices?

### People-first assessment
- Does the site have an existing or intended audience who would find the content useful if they came to it directly?
- Does the content clearly demonstrate first-hand expertise and depth of knowledge?
- Does the site have a primary purpose or focus?
- After reading the content, will someone leave feeling they've learned enough to achieve their goal?
- Will someone reading the content leave feeling they've had a satisfying experience?

### Avoid these patterns (search-engine-first content)
- Content made primarily to attract search engine visits rather than for humans
- Producing content across many different topics hoping some will rank
- Using extensive automation (including AI) to produce content on many topics without adding value
- Mainly summarizing what others say without adding value
- Writing about trending topics instead of topics the site's audience cares about
- Content that leaves readers needing to search again for better information
- Writing to a particular word count because someone said Google has a preferred count (Google does not)
- Content about niche topics with no real expertise, only because of expected traffic
- Promising answers to questions that have no answer (e.g., unconfirmed release dates)
- Changing page dates to make content seem fresh when it hasn't substantially changed
- Adding/removing lots of content primarily to make the site seem "fresh" (this doesn't help)

**What to check in GA4:**
- Pages with high bounce rate + short session duration = users didn't find what they needed
- Pages where users immediately search again (if site search is tracked) = content gap
- Thin pages (low engagement across all channels) = candidates for improvement or removal
- Content clusters with declining traffic over time = possibly flagged by helpful content system

---

## 3. The "Who, How, Why" Framework {#who-how-why}

Google's official guidance recommends evaluating content through three lenses. This framework is particularly useful for assessing content quality from GA4 data.

### Who (created the content)
- Is it clear who authored the content? (bylines, author pages)
- Do bylines link to background about the author and their expertise?
- Can visitors understand why they should trust this author on this topic?

**What to check:** Look at the site's top organic landing pages. Do they have clear authorship? This is an on-site audit item, but if the site has high engagement on authored content vs. anonymous content, that's a useful signal.

### How (the content was created)
- For reviews: is there evidence of actual testing (photos, test methodology)?
- If AI/automation was used: is it disclosed?
- Is there transparency about the creation process?
- Does the content show evidence of original work (original data, photos, research)?

**Relevant for AI-heavy sites:** Google doesn't penalize AI content per se, but content generated primarily to manipulate rankings (regardless of how it's made) violates spam policies. The key question: does automation serve the user or just scale production?

### Why (was the content created)
- Is the content created primarily to help people, or to attract search engine visits?
- Would this content exist if search engines didn't?
- Does the site have a genuine audience beyond search traffic?

**What to check in GA4:** Compare organic vs. direct/referral traffic ratio. A site that exists only for search traffic (90%+ organic, near-zero direct) may lack genuine audience — a "why" red flag. Healthy sites typically have a mix of channels.

---

## 4. Technical Fundamentals {#technical}

### Accessibility to search engines
- Site is accessible to Googlebot (no accidental robots.txt blocks on important content)
- Pages return proper HTTP status codes (200 for live pages, 404 for removed)
- XML sitemap exists and is submitted
- Site uses clean, descriptive URLs

### Site architecture
- Important content is reachable within 3 clicks from the homepage
- Clear internal linking between related content
- Logical URL hierarchy that reflects content organization
- No orphan pages (pages with no internal links pointing to them)

### HTTPS
- All pages served over HTTPS
- No mixed content warnings
- HTTP properly redirects to HTTPS

**What to check in GA4:**
- 404 error pages appearing in page path data (indicates broken links or removed content)
- Pages with zero or very low traffic that should be getting traffic (might be deindexed or blocked)

---

## 5. On-Page SEO {#on-page}

### Title tags
- Each page has a unique, descriptive `<title>`
- Titles accurately describe page content
- Titles are compelling for users in search results (not just keyword-stuffed)
- Length: generally under 60 characters to avoid truncation

### Meta descriptions
- Each page has a unique meta description
- Descriptions summarize the page content and encourage clicks
- Length: 120-160 characters

### Headings
- One `<h1>` per page that describes the main topic
- Subheadings (`<h2>`, `<h3>`) create logical content hierarchy
- Headings describe what follows, not just keywords

### Content structure
- Content is scannable: short paragraphs, lists, clear sections
- Images have descriptive alt text
- Important content isn't hidden behind tabs, accordions, or JavaScript-only rendering
- Internal links use descriptive anchor text (not "click here")

### URL structure
- URLs are simple, readable, and use words relevant to the content
- Use hyphens, not underscores, to separate words
- Avoid unnecessary parameters or session IDs in URLs
- Keep URLs reasonably short

---

## 6. Crawling & Indexing {#crawling}

### robots.txt
- Allows access to important content, CSS, and JavaScript
- Blocks only truly private or duplicate content
- References XML sitemap

### Sitemaps
- XML sitemap includes all important pages
- Sitemap is updated when content changes
- Large sites split sitemaps (max 50,000 URLs per sitemap)
- Sitemap submitted to Google Search Console

### Canonical tags
- Self-referencing canonical on each page
- Duplicate/similar content points canonical to preferred version
- Canonical URLs match the indexed version

### Indexing
- Important pages have `index` (or no robots meta tag)
- Noindex only on pages that genuinely shouldn't appear in search
- Check for accidental noindex tags on important pages

**What to check in GA4:** Pages getting zero organic traffic that should be indexed may have crawling/indexing issues. Cross-reference with GSC Coverage report when available.

---

## 7. Mobile Usability {#mobile}

Google uses **mobile-first indexing** — the mobile version of a site is what Google primarily indexes and ranks.

### Requirements
- Responsive design (same content on mobile and desktop)
- Text readable without zooming
- Touch targets (buttons, links) appropriately sized and spaced
- No horizontal scrolling needed
- Content not wider than screen
- Interstitials don't block content (especially on mobile)

### Common issues
- Content hidden on mobile but visible on desktop (won't be indexed)
- Images that don't scale or are too large for mobile
- Navigation menus that are hard to use on mobile
- Forms that are difficult to complete on mobile

**What to check in GA4:** Compare engagement_rate, bounce_rate, and session_duration between mobile and desktop. Significant gaps (>15% engagement rate difference) indicate mobile usability problems that directly impact rankings.

---

## 8. Page Experience & Core Web Vitals {#page-experience}

Google considers page experience as a ranking factor. Core Web Vitals are the key metrics:

### Largest Contentful Paint (LCP)
- Measures loading performance
- Good: under 2.5 seconds
- Needs improvement: 2.5-4.0 seconds
- Poor: over 4.0 seconds

### Interaction to Next Paint (INP)
- Measures interactivity/responsiveness
- Good: under 200 milliseconds
- Needs improvement: 200-500 milliseconds
- Poor: over 500 milliseconds

### Cumulative Layout Shift (CLS)
- Measures visual stability
- Good: under 0.1
- Needs improvement: 0.1-0.25
- Poor: over 0.25

### Other page experience signals
- HTTPS (required)
- No intrusive interstitials
- Mobile-friendly

**Note:** Core Web Vitals data comes from Chrome User Experience Report (CrUX) or PageSpeed Insights, not from GA4. Recommend checking https://pagespeed.web.dev/ for specific URLs. If CrUX data is available in the user's GA4 setup via custom metrics, use that.

---

## 9. Structured Data {#structured-data}

Structured data helps Google understand page content and can enable rich results in search.

### High-value structured data types
- **Article**: For blog posts and news articles
- **FAQ**: For frequently asked questions
- **HowTo**: For instructional content
- **Product**: For product pages
- **Organization**: For company information
- **BreadcrumbList**: For navigation breadcrumbs
- **LocalBusiness**: For businesses with physical locations

### Best practices
- Use JSON-LD format (Google's recommended format)
- Only mark up content that's visible on the page
- Be specific and accurate — don't mark up content that doesn't match the type
- Test with Google's Rich Results Test (search.google.com/test/rich-results)
- Monitor structured data issues in Google Search Console

**Note:** Structured data can't be checked via GA4 — this is an on-site audit item. Include it as a recommendation if the site doesn't use structured data.

---

## 10. Link Quality {#links}

### Internal linking
- Important pages receive the most internal links
- Use descriptive, natural anchor text
- Create logical link pathways between related content
- Update old content to link to new relevant content
- Fix broken internal links

### External links
- Link to high-quality, authoritative sources when citing data or claims
- Use `rel="nofollow"` for paid links and user-generated content
- Don't participate in link schemes (buying/selling links for ranking)

### Backlink health (GSC data)
- Diverse referring domains (not all from one source)
- Links from relevant, authoritative sites
- Disavow genuinely spammy links (rare — Google is usually good at ignoring them)

---

## 11. Common SEO Myths — What NOT to Recommend {#myths}

These are things Google has explicitly said don't matter or don't work the way people think. Never include these as recommendations in the SEO report — doing so would undermine credibility.

| Myth | Reality (per Google's SEO Starter Guide) |
|------|------------------------------------------|
| Meta keywords tag | Google Search doesn't use it at all |
| Keyword stuffing | Against spam policies; tiring for users |
| Keywords in domain name | Hardly any ranking effect beyond breadcrumbs |
| Minimum/maximum content length | No magical word count target; length alone doesn't matter |
| Subdomains vs subdirectories | No SEO difference; do what's best for the business |
| PageRank as the key factor | Just one of many signals; much more to ranking than links |
| Duplicate content "penalty" | Not a penalty — just inefficient; copying others IS a problem |
| Number/order of headings | Doesn't matter from Search perspective (but good for screen readers) |
| E-E-A-T is a ranking factor | It's NOT a direct ranking factor — it's a concept for understanding how systems work |

### Important nuance on E-E-A-T

Google's own docs state: "E-E-A-T itself isn't a specific ranking factor." Rather, Google uses "a mix of factors that can identify content with good E-E-A-T." This matters because recommendations should focus on demonstrating expertise and building trust through content quality, not on "optimizing for E-E-A-T" as if it were a checkbox.

### What to do instead

When making recommendations, ground them in observable outcomes:
- "This page has a 78% bounce rate from organic traffic — users aren't finding what they expected" (actionable)
- NOT: "You need to improve your E-E-A-T score" (not a real thing)
- "Adding author bylines and credentials would help users trust your health advice" (people-first)
- NOT: "You need more keywords in your meta tags" (doesn't work)

---

## 12. Common SEO Pitfalls {#pitfalls}

### Content issues
- **Thin content**: Pages with very little substantive content
- **Duplicate content**: Same or very similar content on multiple URLs
- **Keyword stuffing**: Unnaturally repeating keywords
- **Cloaking**: Showing different content to search engines vs users
- **Doorway pages**: Pages created solely to rank for specific queries, that funnel users to the same destination

### Technical issues
- **Soft 404s**: Pages that look like error pages but return 200 status
- **Redirect chains**: Multiple redirects (A→B→C) that slow crawling
- **Orphan pages**: Important pages with no internal links
- **Crawl budget waste**: Letting search engines crawl low-value pages (filters, sorts, etc.)
- **JavaScript-dependent content**: Critical content that only renders with JS (Googlebot can render JS but may deprioritize)

### User experience issues
- **Intrusive interstitials**: Popups that block content, especially on mobile
- **Excessive ads above the fold**: Pushing main content below the visible area
- **Slow page loads**: Particularly on mobile networks
- **Misleading titles**: Titles that don't match content (clickbait)

---

## Scoring Framework

When generating the SEO report, use this framework to rate each area:

| Rating | Symbol | Meaning |
|--------|--------|---------|
| Strong | [STRONG] | Performing well, minor optimizations possible |
| Adequate | [ADEQUATE] | Meeting baseline but has improvement opportunities |
| Needs Work | [NEEDS WORK] | Significant issues that likely impact rankings |
| Critical | [CRITICAL] | Fundamental problems that must be fixed |
| Not Assessed | [N/A] | Couldn't evaluate (missing data or tool access) |

Rate each section of the checklist and include specific evidence from the data to justify each rating.
