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
    const adPage = await ctx.newPage();
    try {
      const url = `https://www.linkedin.com/ad-library/search?companyName=${encodeURIComponent(c.linkedin)}`;
      const resp = await adPage.goto(url, { waitUntil: 'domcontentloaded', timeout: 45000 });
      const status = resp ? resp.status() : 0;
      const finalUrl = adPage.url();

      if (isLoginWall(finalUrl)) {
        result.errors.push({
          url: 'linkedin-ad-library',
          status,
          note: 'redirected to a LinkedIn login/checkpoint wall — could not read the ad library',
        });
      } else if (status && status >= 400) {
        result.errors.push({ url: 'linkedin-ad-library', status, note: `blocked with ${status}` });
      } else {
        await adPage.waitForTimeout(3000);
        const ads = await adPage.evaluate(() =>
          Array.from(document.querySelectorAll('[class*="ad-library-card"], article'))
            .slice(0, 25)
            .map((el) => {
              const t = (el.textContent || '').replace(/\s+/g, ' ').trim();
              return { headline: t.slice(0, 120), body: t.slice(0, 300), firstSeen: '' };
            })
            .filter((a) => a.headline.length > 10)
        );
        result.linkedinAds.ads = ads;
        result.linkedinAds.count = ads.length;
        // A count of 0 here is a legitimate pass: the page loaded (no login wall, no error
        // status) and the selector simply found nothing — a company with no active ads.
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
