---
name: content-strategy
description: Build or audit an SEO-driven B2B content strategy on the 7-part Orbit Media framework (sales page core, content mission, original research, prospect questions, visuals, influencer collaboration, guest posting) and turn it into a quarterly content hub. Use when someone says "content strategy", "content plan", "content marketing plan", "content mission", "editorial calendar", "content hub", "content audit", "our blog doesn't generate leads", "blog isn't converting", or asks for an original research idea. Triggered from context, it offers help and asks before doing anything.
metadata:
  built: 2026-09-04
  author: risu (https://github.com/risukisu/)
  built-with: Claude Fable 5.1
  framework-credit: Andy Crestodina, Orbit Media - https://www.orbitmedia.com/blog/content-strategy-framework/
---

# Content Strategy Builder & Auditor

An interactive skill that either builds a documented content strategy from
scratch or audits an existing content program, using the same seven-part
framework in both directions. The end product is a markdown file: a strategy
with a first quarterly content hub, or a scorecard with ranked gaps and fixes.

The framework rests on one observation about B2B sites: people who land on a
blog post are looking for information, not a vendor, so they almost never turn
into leads directly. What blog content does do is earn links. Links raise the
site's authority. Authority is what lets the service pages rank for the phrases
buyers actually search. And service-page visitors are the ones who convert. So
the strategy starts at the sales page and works outward, and every content
piece has a job: earn links, build relationships with people who publish, or
answer a question that's stalling a deal.

> Framework: Andy Crestodina, Orbit Media,
> [The B2B Content Strategy Framework](https://www.orbitmedia.com/blog/content-strategy-framework/).
> Everything in this skill is a distillation in our own words. Statistics keep
> their source links in the reference files.

## Company context: setup step, every run

The skill has no memory and no fixed place for company data. Context comes from
wherever the user was launched, or from the user directly, and nothing is used
without their say-so.

Run this after the entry gate and before the intake question:

1. **Scan the launch directory** (current working directory and its repo) for
   likely context. Look for `CLAUDE.md`, `AGENTS.md`, a `context/` folder,
   files whose names mention brand, positioning, ICP, persona, voice, or
   competitors, and any earlier `content-strategy-*.md` or `content-audit-*.md`
   this skill produced. List filenames only. Don't read contents yet.
2. **Ask one question.** Show what was found (or say nothing relevant was
   found) and offer four choices: use these files; point me at a different
   folder or file; paste the context as text; start with no context. Wait.
3. **Read only what the user approved.** A pasted block counts as the context
   document for this run. "No context" means the intake answer is the whole
   picture; say so in the output document.
4. **Earlier output is memory.** If the user approves a previous
   `content-strategy-*.md` or `content-audit-*.md`, offer to continue from it
   (audit a built strategy, refresh a hub, re-score) rather than start over.

Optional extra: `references/*-context.local.md` packs, if any exist on this
machine, are listed in step 2 alongside the scan results and follow the same
rule: nothing is read until the user picks it. They never ship with the skill.

## Entry gate

| How you got here | What to do |
|---|---|
| The user typed `/content-strategy` | Go to the context setup step, then Step 0. |
| This skill matched the conversation (the user said "content strategy", "blog isn't converting", etc.) | **Do not start working.** Offer first, using the text below, then wait. |

Offer text for the passive case:

> I have a content-strategy skill that fits this. It either builds a documented
> SEO-driven strategy from scratch (7 parts, then a quarterly content hub of
> about 12 connected pieces), or audits what you already publish against the
> same 7 parts and ranks the gaps. Want me to run it? Build, audit, or not now?

"Build" or "audit" proceeds to the context setup step, then Step 0, with the
mode pre-selected. "Not now"
ends the skill's involvement. Hand the conversation back and don't raise it
again unless the user does.

## Step 0: Intake (always)

Ask this, in one message, nothing else:

> Tell me about your content program today: what do you publish, for whom, and
> what is it supposed to do for the business?

Ask it even when context was approved and even when the user pre-selected a
mode. Then route:

- Nothing real yet, or "starting from scratch" → **Build flow**.
- A running program with several of the seven parts in place → **Audit flow**.
- Content exists (even a lot of it) but none of the seven parts is in place:
  no mission, no research, no outside publishing → recommend **Build** and say
  why: there is nothing structural to score yet. The user may still pick Audit.
- Unclear → ask which they want: a strategy built, or the current program audited.

## Data hooks (both flows)

If GA4 (`analytics-mcp`), Search Console (`gsc`), or DataForSEO tools are
loaded, offer once, at part 1, to pull: conversion rate split by landing page
type (blog vs service), top-linked pages, Domain Authority, phrase difficulty.
If they aren't loaded or the user declines, ask for the numbers. If the user
doesn't have them, record "unknown" once and reuse that answer wherever the
number comes up again; don't re-ask. In the document, say why a number is
unknown: "no analytics tools loaded this session" is different from "the user
doesn't track this". Never make the numbers a precondition.

When the user can name roles but not people or sites ("two HR podcasts", "a
trade site"), accept the role as a placeholder, record it, and make naming
them a week-one task in the hub. Don't stall the flow on names.

## Build flow

One question per message. Read the reference for a step before asking its
question. Record each decision as you go; they become the document.

| Step | Read | Ask |
|---|---|---|
| 1. Sales page core | `references/sales-page-checklist.md` | Which service page should generate leads, and what commercial-intent phrase should it rank for? What's the site's Domain Authority and the phrase's difficulty? Then: what does the page fail to answer or prove? |
| 2. Mission | `references/mission-statement.md` | Who exactly is the content for, what topics, and what do they get from it? Draft the one-sentence mission with them. |
| 3. Original research | `references/original-research.md` | What does your audience wish someone would measure? What data can you reach that competitors can't? |
| 4. Prospect questions | `references/prospect-questions.md` | What three questions came up in sales conversations last month? What do prospects get wrong about the offer? |
| 5. Visuals | `references/visuals.md` | Which existing or planned piece deserves a visual version? Who can produce it? |
| 6. Influencer collaboration | `references/influencer-collab.md` | Who does your audience already trust? Which of the five free formats fit this quarter? |
| 7. Guest posting | `references/guest-posting.md` | Which five sites would you most want to appear on? What could you pitch them this quarter? |

After step 7, read `references/content-hub-template.md` and assemble Quarter 1:
twelve connected pieces, each with a stated purpose, on a twelve-week calendar.

## Audit flow

1. Read `references/audit-rubric.md`. When scoring a part or writing its
   first fix, read that part's reference too (same files as the Build table).
2. For each of the seven parts, ask for evidence: URLs, examples, numbers. One
   part per message. Offer the data hooks at part 1 per the section above.
3. Score each part **present / partial / missing** against the rubric's
   observable criteria. Quote the evidence: a URL, a number, or the user's own
   sentence in quotation marks, labeled as which.
4. Compute the 1% test: how many of the four rare practices (documented
   mission, research-anchored, ongoing influencer collaboration, PR-focused)
   are true.
5. Rank the gaps by link-and-authority impact per the rubric, then adjust for
   what the user can realistically do this quarter.
6. Give one concrete first fix per gap.
7. Propose a next-quarter hub built only from the missing parts.

## Output contract

**Build document** sections, in order:

1. Content mission (one sentence, plus audience / topics / benefit spelled out)
2. Sales page target: phrase, current DA, difficulty, gap, rank fixes, convert fixes
3. Original research: question, method, sample, effort estimate, promotion plan
4. Prospect questions captured, each mapped to an article title and a sales use
5. Visual repurposing plan
6. Influencer collaboration plan: formats chosen, named people or roles
7. Guest posting plan: target sites, pitch angles
8. Quarter 1 content hub: twelve slots with purpose and links between pieces, on a calendar
9. Timeline expectation and what to measure

**Audit document** sections, in order:

1. Scorecard: seven parts, score, evidence
2. The 1% test result
3. Gaps ranked, with one first fix each
4. Next-quarter hub from the missing parts

Default file names: `content-strategy-[company].md` (build) or
`content-audit-[company].md` (audit), in the current directory. Confirm the
path with the user before writing. Run `/copy-deslop` on the finished file.

Every claim in the document ties back to something the user said or a tool
returned. Unknowns are labeled unknown, not estimated.

## Quick reference

| Part | Its job |
|---|---|
| Sales page | Rank for the buying phrase and convert the visitor |
| Mission | Keep every piece aimed at one audience and one promise |
| Original research | Earn links by being the primary source |
| Prospect questions | Move deals; give sales something to send |
| Visuals | Multiply reach of the best text; bait for guest posts |
| Influencer collaboration | Get seen by the people who make links |
| Guest posting | The most direct route to a link and a relationship |
| The hub | Make the twelve pieces reinforce each other every quarter |

## Common mistakes

- Starting with blog topics instead of the sales page. The page is the
  mousetrap; content is the cheese. Build the trap first.
- A mission everyone "knows" but nobody wrote down. Unwritten means undefined.
- A research idea too big to finish in a quarter. Scope to one headline finding.
- Guest posts that earn no link, or a link only in the bio when the research
  could have been cited in the body.
- Hub pieces that don't reference each other. The hub is a cluster, not a list.
- Reading context files because they were there. Found is not approved. Ask.
- Skipping the intake because context was loaded. Ask anyway.
- Starting work on a passive trigger. Offer, ask, wait.
- Filling unknown numbers with plausible ones. Label them unknown.
