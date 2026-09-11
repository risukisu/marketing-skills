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
  for (const c of competitors) {
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
      const shot = path.join(shotsDir, `${slug(c.name)}-home.png`);
      await shotPage.screenshot({ path: shot, fullPage: true });
      result.screenshots.home = shot;
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
            const cards = Array.from(document.querySelectorAll('[class*="ad-library-card"], article'))
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
