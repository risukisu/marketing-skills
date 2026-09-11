# Inventory — provenance and licenses

Every skill in this repo, where it came from, and which license covers it. Original work is MIT
(root [`LICENSE`](./LICENSE)); vendored skills keep their upstream license, shipped as a `LICENSE`
or `LICENSE.txt` inside their own folder. [`NOTICE`](./NOTICE) maps folders to licenses.

Audited by reading every folder: license files, `SKILL.md` contents, references and scripts. First
pass 2026-07-23, kept current since.

**Layout:** `skills/<Category>/<skill>`, three categories (Writing, SEO, Marketing Ops). Skills reach
`~/.claude/skills` through links made by `install.ps1` / `install.sh`.

## The skills — 48

| Skill | Domain | Source | License evidence | Verdict | Notes |
|---|---|---|---|---|---|
| copy-deslop | Writing | Own | root MIT | MIT-clear | |
| copy-longform | Writing | Own | root MIT | MIT-clear | Renamed from `copyediting` 2026-07-21 |
| writing-assistant | Writing | Own | root MIT | MIT-clear | De-personalized 2026-08-18: work-voice routing + profiles moved to untracked `references/*.local.md`; voice-profile paths now `~`-generic. Renamed from `writing-sparring` 2026-07-21 |
| seo | SEO | AgriciDaniel/claude-seo v2.2.5 | MIT © 2026 AgriciDaniel (LICENSE.txt in folder) | MIT-clear | Upgraded 1.8.1 → 2.2.5 on 2026-09-05 from fork `$CLAUDE_SYSTEM/github_forks/AgriciDaniel-claude-seo` branch `local/2.2.5-hardening` (upstream tag + our prompt-injection scanner and agent security notes). Managed Python runtime lives outside the repo (LOCALAPPDATA). 18 sub-agents installed to `~/.claude/agents/` (not in this repo). Hooks not wired (manual install; upstream says plugin-only) |
| seo-audit | SEO | AgriciDaniel/claude-seo v2.2.5 | MIT | MIT-clear |  |
| seo-backlinks | SEO | AgriciDaniel/claude-seo v2.2.5 | MIT | MIT-clear |  |
| seo-cluster | SEO | AgriciDaniel/claude-seo v2.2.5 | MIT | MIT-clear | New in 2.x |
| seo-competitor-pages | SEO | AgriciDaniel/claude-seo v2.2.5 | MIT | MIT-clear |  |
| seo-content | SEO | AgriciDaniel/claude-seo v2.2.5 | MIT | MIT-clear |  |
| seo-content-brief | SEO | AgriciDaniel/claude-seo v2.2.5 | MIT | MIT-clear | New in 2.x |
| seo-drift | SEO | AgriciDaniel/claude-seo v2.2.5 | MIT | MIT-clear | New in 2.x |
| seo-ecommerce | SEO | AgriciDaniel/claude-seo v2.2.5 | MIT | MIT-clear | New in 2.x |
| seo-flow | SEO | AgriciDaniel/claude-seo v2.2.5 | MIT | MIT-clear | New in 2.x |
| seo-geo | SEO | AgriciDaniel/claude-seo v2.2.5 | MIT | MIT-clear |  |
| seo-google | SEO | AgriciDaniel/claude-seo v2.2.5 | MIT | MIT-clear |  |
| seo-hreflang | SEO | AgriciDaniel/claude-seo v2.2.5 | MIT | MIT-clear |  |
| seo-images | SEO | AgriciDaniel/claude-seo v2.2.5 | MIT | MIT-clear |  |
| seo-local | SEO | AgriciDaniel/claude-seo v2.2.5 | MIT | MIT-clear |  |
| seo-maps | SEO | AgriciDaniel/claude-seo v2.2.5 | MIT | MIT-clear |  |
| seo-page | SEO | AgriciDaniel/claude-seo v2.2.5 | MIT | MIT-clear |  |
| seo-plan | SEO | AgriciDaniel/claude-seo v2.2.5 | MIT | MIT-clear |  |
| seo-programmatic | SEO | AgriciDaniel/claude-seo v2.2.5 | MIT | MIT-clear |  |
| seo-schema | SEO | AgriciDaniel/claude-seo v2.2.5 | MIT | MIT-clear |  |
| seo-sitemap | SEO | AgriciDaniel/claude-seo v2.2.5 | MIT | MIT-clear |  |
| seo-sxo | SEO | AgriciDaniel/claude-seo v2.2.5 | MIT | MIT-clear | New in 2.x |
| seo-technical | SEO | AgriciDaniel/claude-seo v2.2.5 | MIT | MIT-clear |  |
| seo-ahrefs | SEO | AgriciDaniel/claude-seo v2.2.5 (extension: ahrefs) | MIT | MIT-clear | New in 2.x; needs the ahrefs MCP/CLI to do anything |
| seo-bing | SEO | AgriciDaniel/claude-seo v2.2.5 (extension: bing-webmaster) | MIT | MIT-clear | New in 2.x; needs the bing-webmaster MCP/CLI to do anything |
| seo-dataforseo | SEO | AgriciDaniel/claude-seo v2.2.5 (extension: dataforseo) | MIT | MIT-clear | ; needs the dataforseo MCP/CLI to do anything |
| seo-firecrawl | SEO | AgriciDaniel/claude-seo v2.2.5 (extension: firecrawl) | MIT | MIT-clear | ; needs the firecrawl MCP/CLI to do anything |
| seo-image-gen | SEO | AgriciDaniel/claude-seo v2.2.5 (extension: banana) | MIT | MIT-clear | ; needs the banana MCP/CLI to do anything |
| seo-profound | SEO | AgriciDaniel/claude-seo v2.2.5 (extension: profound) | MIT | MIT-clear | New in 2.x; needs the profound MCP/CLI to do anything |
| seo-seranking | SEO | AgriciDaniel/claude-seo v2.2.5 (extension: seranking) | MIT | MIT-clear | New in 2.x; needs the seranking MCP/CLI to do anything |
| seo-unlighthouse | SEO | AgriciDaniel/claude-seo v2.2.5 (extension: unlighthouse) | MIT | MIT-clear | New in 2.x; needs the unlighthouse MCP/CLI to do anything |
| seo-report | SEO | Own | root MIT | MIT-clear | De-personalized 2026-08-18: per-root output map moved to untracked `workspace.local.md`; portfolio mode written generically |
| linkedin-ads | Marketing Ops | Own, on the AdConversion methodology (credited) | root MIT | MIT-clear | Methodology credited inline; expression own. Company context packs moved to untracked `references/*-context.local.md` 2026-08-18 |
| product-launch | Marketing Ops | Own; framework credited to Luke Harries | root MIT | MIT-clear | Credit inline — re-verified 2026-08-18 |
| beautify-github-readme | Marketing Ops | oil-oil/beautify-github-readme | MIT © 2026 oil-oil (LICENSE in folder) | MIT-clear | Ingested 2026-08-20; scripts reviewed (local-only: SVG render + ffmpeg GIF, no network). Kept in scope by owner call 2026-08-31: a marketer's GitHub presence is marketing |
| content-strategy | Marketing Ops | Own; framework credited to Andy Crestodina (Orbit Media) | root MIT | MIT-clear | Built 2026-09-04. Original distillation, credit inline in SKILL.md + every reference; evals in `evals/`. Context is user-approved per run (scan launch dir → ask); optional untracked `references/*-context.local.md` packs |
| frontend-design-anti-slop | Marketing Ops | Own (also listed on skillcraft.cloud/marketplace) | root MIT | MIT-clear | Added 2026-09-05 from the SkillCraft staging copy (`projects/skills-trader/docs/skills-staging/`); interactive intake built in |
| cro | Marketing Ops | coreyhaines31/marketingskills v2.0.0 | MIT © 2025 Corey Haines (LICENSE in folder) | MIT-clear | Ported 2026-09-05: product-marketing-file lookup replaced by the per-run context setup step; related-skills list points at this library; credit inline. Conversion audit of pages and forms |
| customer-research | Marketing Ops | coreyhaines31/marketingskills v2.0.2 | MIT © 2025 Corey Haines (LICENSE in folder) | MIT-clear | Ported 2026-09-05: product-marketing-file lookup replaced by the per-run context setup step; related-skills list points at this library; credit inline. Three research modes: analyze assets, mine public signal, run interviews/surveys |
| lead-magnets | Marketing Ops | coreyhaines31/marketingskills v2.0.0 | MIT © 2025 Corey Haines (LICENSE in folder) | MIT-clear | Ported 2026-09-05: product-marketing-file lookup replaced by the per-run context setup step; related-skills list points at this library; credit inline. Plan, format, and distribute gated offers |
| marketing-council | Marketing Ops | coreyhaines31/marketingskills v1.0.0 | MIT © 2025 Corey Haines (LICENSE in folder) | MIT-clear | Ported 2026-09-05: product-marketing-file lookup replaced by the per-run context setup step; related-skills list points at this library; credit inline. Simulated advisor board, 12 dossiers in references/advisors; grounding rules keep it labeled as simulation |
| marketing-monthly | Marketing Ops | Own | root MIT | MIT-clear | Genericized 2026-09-11 from a day-job skill: company, CRM ids, GA4 property, templates, and output paths moved to an untracked `references/<client>-context.local.md` pack (template: `pipeline-analysis/references/context-pack.TEMPLATE.md`); metric definitions point at `pipeline-analysis/definitions.md` |
| campaign-report | Marketing Ops | Own | root MIT | MIT-clear | Genericized 2026-09-11 from a day-job skill; same pack convention. The publishing step runs only when the pack defines a target |
| pipeline-analysis | Marketing Ops | Own | root MIT | MIT-clear | Genericized 2026-09-11 from a day-job skill. `compute_funnel.py` (stdlib) takes `--config` / `--targets` / `--reason-map`; funnel pipelines, stage ids, ticket stages, and AM sources come from the client pack (`*.local.json`, untracked). Shipped `targets.json` is empty, `reason_map.json` is a starter; fixture ids are synthetic (9xxxxxxxx numbers and nil-pattern UUIDs, verified 2026-09-12 against the source portal — the 2026-09-11 ship carried real stage/pipeline ids by mistake, scrubbed from tree and history); 21 tests |
| competitor-intel | Marketing Ops | Own | root MIT | MIT-clear | Added 2026-09-11. Supersedes the `risukisu/ci-agent` prototype. Deep tier reads the public LinkedIn Ad Library — ToS notice in `scripts/deep/scan.mjs` |

**48 skills across 3 categories.**

## Not vendored: data connections

| Server | Source | License | Tested | Latest (2026-09-05) | Notes |
|---|---|---|---|---|---|
| analytics-mcp (GA4) | googleanalytics/google-analytics-mcp (PyPI `analytics-mcp`) | Apache-2.0 | 0.7.0 (upgraded 2026-09-06) | 0.7.0 | Google-official. Install and config in `docs/data-connections.md` |
| gsc (Search Console) | Suganthan-Mohanadasan/Suganthans-GSC-MCP | Apache-2.0 | v2.5.1 + local `GSC_TOKEN_PATH` patch (upgraded 2026-09-06) | v2.5.1 | Local clone at `$CLAUDE_SYSTEM/github_forks/Suganthans-GSC-MCP`, branch `local/2.5.1-token-path`; patch is one commit on top of upstream, not merged there |

## Deliberately not in this repo

| Skill | Why local | Since |
|---|---|---|
| docx, pptx, pdf, xlsx | Anthropic proprietary notice ("© 2025 Anthropic, PBC. All rights reserved.") — not redistributable | 2026-08-18 |
| doc-coauthoring | No license file, unconfirmed provenance | 2026-08-18 |
| internal-comms | Anthropic-authored (Apache-2.0); removed from the repo by owner decision | 2026-09-05 |
| save, sync, wip, resume | Not marketing — session/workspace tooling (Own, de-personalized 2026-08-18) | 2026-08-31 |
| obsidian-cli, obsidian-markdown, obsidian-bases, json-canvas | Not marketing — Obsidian tooling (kepano/obsidian-skills, MIT © Steph Ango, licenses verified 2026-08-18) | 2026-08-31 |
| frontend-design, canvas-design, theme-factory, web-artifacts-builder, webapp-testing, mcp-builder, skill-creator | Not marketing — Anthropic design/build set (Apache-2.0) | 2026-08-31 |
| llm-council | Not marketing — decision tooling (Own; Karpathy concept credited) | 2026-08-31 |
| defuddle | Not marketing — research utility (kepano, MIT; provenance corrected 2026-08-18) | 2026-08-31 |
| grilling, grill-with-docs, domain-modeling | Not marketing — planning tooling (mattpocock/skills, MIT © Matt Pocock); ingested 2026-08-31, never committed | 2026-08-31 |

## Untracked by Design (.gitignore)

| Path | Why |
|---|---|
| `seo/.deps/` | 7,749 vendored Python dependency files — reinstallable, own licenses, no reason to version |
| `linkedin-ads-workspace/` | Not a skill — a skill-creator eval workspace |
| All 🔒 LOCAL skill folders above | Proprietary / unlicensed / out of marketing scope |
| `*.local.md` (any depth) | Machine-local convention: day-job/company context packs, voice profiles, and the machine's `workspace.local.md` path map. Never ships; recreate per machine |

⚠ The untracked skills and `*.local.md` files have **no git backup**. The own-work ones
(save/sync/wip/resume, llm-council) and the day-job packs should eventually get a home in a
private repo (day-job packs from a day-job session, per root separation); the vendored ones
(Anthropic, kepano, mattpocock) are reinstallable from upstream.

## Provenance notes

- **No credentials anywhere.** Every API-key string is a placeholder or an env-var lookup.
- **No client names anywhere.** The day-job reference files that carried business data are
  untracked `*.local.md` — out of the repo entirely.
- **Hardcoded personal paths** — RESOLVED 2026-08-18 for all skills then tracked; the affected
  session skills have since left the repo anyway.
- **License split documented:** root `LICENSE` (MIT) covers own skills; `NOTICE` maps the two
  remaining vendored families (claude-seo MIT, internal-comms Apache-2.0, beautify MIT) to their
  per-folder `LICENSE.txt`.
- `essay-openings.md` (writing-assistant) names the owner and his writing voice — owner's call,
  no third-party issue.
