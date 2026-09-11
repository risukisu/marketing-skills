// scan.mjs — optional deep tier for competitor-intel.
//
// NOTICE: This reads the public LinkedIn Ad Library. Automated collection may conflict with
// LinkedIn's Terms of Service. Use it on your own account's responsibility, keep the request
// volume low, and prefer manual review if your organization's policy requires it. The default
// tier of this skill does not touch LinkedIn at all.

import { chromium } from 'playwright';
import { mkdir, readFile } from 'node:fs/promises';
import path from 'node:path';

const argv = process.argv.slice(2);
const arg = (k, d = '') => {
  const i = argv.indexOf(`--${k}`);
  return i === -1 ? d : (argv[i + 1] ?? d);
};

const competitorsPath = arg('competitors');
const outDir = arg('out');
const locale = arg('locale', 'en-US');
if (!competitorsPath || !outDir) {
  console.error('usage: scan.mjs --competitors <path> --out <runDir> [--locale en-US]');
  process.exit(2);
}

const slug = (s) => s.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');

// slug() degenerates on non-ASCII competitor names — "Ströme" and "Str_me" collapse to
// the same thing, a fully non-Latin name collapses to "" — and two names that collapse
// together would silently overwrite each other's screenshot. Disambiguate by position in
// competitors.md, which is stable from run to run.
const usedShotNames = new Map();
const shotFileFor = (name, i) => {
  const base = slug(name) || `competitor-${i + 1}`;
  const n = (usedShotNames.get(base) || 0) + 1;
  usedShotNames.set(base, n);
  return n === 1 ? `${base}-home.png` : `${base}-${n}-home.png`;
};

// The ToS notice at the top of this file asks the user to keep request volume low.
// Honor it in code, not just in a comment: pause between Ad Library navigations.
const AD_DELAY_MS = 2500;
let adNavCount = 0;

const parseCompetitors = (raw) =>
  raw.split('\n')
    .map((l) => l.trim())
    .filter((l) => l.startsWith('-'))
    .map((l) => l.replace(/^-\s*/, '').split('|').map((p) => p.trim()))
    .filter((p) => p.length >= 2 && /^https?:\/\//.test(p[1]))
    .map(([name, url, li = '']) => ({ name, url, linkedin: li || name }));

const competitors = parseCompetitors(await readFile(competitorsPath, 'utf8'));
const shotsDir = path.join(outDir, 'screenshots');
await mkdir(shotsDir, { recursive: true });

// LinkedIn redirects unauthenticated Ad Library requests to one of these — treat any of them
// as "could not read the page," never as a legitimate zero-ad result.
const isLoginWall = (u) => /\/(login|checkpoint|authwall|uas\/login)/.test(u);

const browser = await chromium.launch();
const ctx = await browser.newContext({ locale, viewport: { width: 1440, height: 900 } });

try {
  for (const [i, c] of competitors.entries()) {
    const result = {
      name: c.name,
      screenshots: { home: '' },
      linkedinAds: { tier: 'deep', count: 0, ads: [] },
      errors: [],
    };

    // --- Screenshot ---
    const shotPage = await ctx.newPage();
    try {
      await shotPage.goto(c.url, { waitUntil: 'networkidle', timeout: 45000 });
      const shotFile = shotFileFor(c.name, i);
      await shotPage.screenshot({ path: path.join(shotsDir, shotFile), fullPage: true });
      // Record the path RELATIVE to the run directory, forward slashes. snapshot.json
      // gets committed: an absolute path leaks the local directory layout into the repo
      // and is dead on any other machine.
      result.screenshots.home = `screenshots/${shotFile}`;
    } catch (e) {
      result.errors.push({ url: c.url, status: 0, note: `screenshot failed: ${e.message}` });
    } finally {
      await shotPage.close().catch(() => {});
    }

    // --- LinkedIn Ad Library ---
    // RULE: absence of evidence is never reported as evidence of absence. A `count` may only be
    // written when the page affirmatively shows either ad cards or a recognizable "no ads"
    // empty state. Anything else — no response, a login wall, an HTTP error, or a page that
    // rendered but shows neither cards nor a recognizable empty state (e.g. a same-URL,
    // HTTP-200 client-side "sign in to see this" gate) — goes to errors[], never to count: 0.
    // Do not relax this to "assume zero when unsure" without re-reading the note below on why.
    const adPage = await ctx.newPage();
    try {
      const url = `https://www.linkedin.com/ad-library/search?companyName=${encodeURIComponent(c.linkedin)}`;
      if (adNavCount > 0) await adPage.waitForTimeout(AD_DELAY_MS);
      adNavCount++;
      const resp = await adPage.goto(url, { waitUntil: 'domcontentloaded', timeout: 45000 });

      if (!resp) {
        // No response object at all — Playwright couldn't confirm a load. Never treat this as
        // a confirmed empty read.
        result.errors.push({
          url: 'linkedin-ad-library',
          status: 0,
          note: 'no response received from navigation — could not confirm the page loaded',
        });
      } else {
        const status = resp.status();
        const finalUrl = adPage.url();

        if (isLoginWall(finalUrl)) {
          result.errors.push({
            url: 'linkedin-ad-library',
            status,
            note: 'redirected to a LinkedIn login/checkpoint wall — could not read the ad library',
          });
        } else if (status >= 400) {
          result.errors.push({ url: 'linkedin-ad-library', status, note: `blocked with ${status}` });
        } else {
          await adPage.waitForTimeout(3000);
          // NOTE: I was never able to reach a real, unblocked Ad Library results page during
          // development — every attempt was blocked upstream (403) before rendering. The
          // selectors below (for both cards and the "no ads" empty state) are therefore my
          // best guess, unverified against the real DOM. That's acceptable ONLY because the
          // fallback (the final `else`) is safe: if neither selector matches, we report an
          // error, not a zero. If you get a confirmed look at the real markup, tighten these
          // selectors — but never remove the fallback-to-error branch.
          const evidence = await adPage.evaluate(() => {
            // The `ad-library` class hint is REQUIRED. An earlier version also matched a
            // bare `article`, which fails OPEN: any HTTP-200 page rendering <article>
            // elements with more than 10 characters of text — an interstitial, a help
            // page, a marketing shell served in place of results — produced fake cards, a
            // fake non-zero count, and fake headlines that flow into new_ad_headlines and
            // get quoted directly in the briefing. A fabricated quotation attributed to a
            // competitor is worse than a false zero, and the fallback-to-error branch
            // below already turns an unrecognized DOM into an error rather than a guess,
            // so the `article` fallback bought coverage at the price of fabrication risk.
            //
            // `headline` and `body` are both slices of the same textContent, so the
            // headline is a LEADING EXCERPT of the body, not a distinct field: the real
            // markup has never been observed (see references/troubleshooting.md), so there
            // is no verified selector for a card's headline element. Consequence:
            // new_ad_headlines diffs 120-character text blobs, and what the briefing
            // quotes is an excerpt of an ad, not its headline.
            const cards = Array.from(document.querySelectorAll('[class*="ad-library-card"]'))
              .map((el) => {
                const t = (el.textContent || '').replace(/\s+/g, ' ').trim();
                return { headline: t.slice(0, 120), body: t.slice(0, 300), firstSeen: '' };
              })
              .filter((a) => a.headline.length > 10);

            const emptyStateEl = document.querySelector(
              '[class*="no-results"], [class*="empty-state"], [data-test-id*="empty"], [data-testid*="empty"]'
            );
            const bodyText = (document.body && document.body.textContent) || '';
            const emptyStateText = /no ads (were )?found|no results found|hasn.?t run any ads|doesn.?t have any active ads/i.test(
              bodyText
            );

            return { cards, hasEmptyState: !!emptyStateEl || emptyStateText };
          });

          if (evidence.cards.length > 0) {
            // `count` is every card on the page; `ads` is capped at 25. So for a
            // competitor running more than 25 ads, ad_count_delta can move with no
            // matching new_ad_headlines. Left as is on purpose — 25 ad excerpts is
            // already more than a briefing can usefully render — but it is a real
            // asymmetry between the two fields the diff reads.
            result.linkedinAds.ads = evidence.cards.slice(0, 25);
            result.linkedinAds.count = evidence.cards.length;
          } else if (evidence.hasEmptyState) {
            // Affirmative "no ads" empty state found — a genuine, confirmed zero.
            result.linkedinAds.count = 0;
            result.linkedinAds.ads = [];
          } else {
            // Neither ad cards nor a recognizable empty state — we don't know what we're
            // looking at (could be an inline sign-in gate rendered at HTTP 200). Do not guess.
            result.errors.push({
              url: 'linkedin-ad-library',
              status,
              note: 'results region could not be identified — neither ad cards nor a recognizable empty-state marker were found; not reporting a count',
            });
          }
        }
      }
    } catch (e) {
      result.errors.push({ url: 'linkedin-ad-library', status: 0, note: `ads failed: ${e.message}` });
    } finally {
      await adPage.close().catch(() => {});
    }

    console.log(JSON.stringify(result));
  }
} finally {
  await browser.close();
}
