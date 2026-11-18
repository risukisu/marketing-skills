# Companions

Skills that work alongside this one. Offer each in one line, at the moment it fits, and install nothing without a yes. Third-party skills are community code: pin them to a commit you have read.

## taste-skill (design-taste-frontend)

- **What:** Leonxlnx/taste-skill (MIT), installed under the name `design-taste-frontend`. It builds company websites with a copy layer, history-aware dealing of palettes, type and heroes, browser checkers, and a finish gate.
- **When:** after the person picks a direction for a website and asks for it to be built. It covers websites only. Don't use it for reports, documents, dashboards or artifacts, where several of its house rules don't fit.
- **Detect:** `~/.claude/skills/design-taste-frontend/SKILL.md` exists, or the skill appears in the harness's list.
- **How:**
  - Invoke it with the chosen card as the brief.
  - Give it the card's colours through its client-colour route (`start.mjs brand`), and say the direction is fixed: its dealt palette and pairing don't replace the chosen tokens. It has no route for fixed faces, so expect to override its font pairing by hand.
  - Where its rules conflict with the chosen direction or the truth rule, the direction and the truth rule win. Examples: no image captions, one section per screen, assumed hours and prices on venue pages.
  - Tell it so in the brief.
- **Risk to state first:** once a build is armed (its `start.mjs deal` or `gate.mjs --start`), its Stop hook runs headless-browser checks whenever the session tries to stop. It can hold the session for up to about ten minutes per stop, over a few rounds. Ending the build with `gate.mjs --done "<what the person said>"` releases it.
  - It copies an asset kit of about 37 MB into the project.
  - Some of its scripts delete their own temporary files.
- **Never** run its dealing or gate commands during the proposal steps. Either one arms the gate.
- **Install:** clone the repo, check out a commit you have read (this skill was checked against `f6b7657`, 2026-11-17), and link or copy `skills/taste-skill` into the skills folder as `design-taste-frontend`. The hook's fallback path expects that exact folder name.

## Vercel agent skills

- **What:** vercel-labs/agent-skills. The repo states MIT in its README and some skill files, but has no root licence file.
- **When:** the build target is React, Next.js or Vercel. Signals: a `vercel.json` file, a `.vercel/` folder, `next` in `package.json`, or the person saying so. Offer after the pick, not before.
- **Offer:**
  - `web-design-guidelines`: a review of UI code against about a hundred web interface rules, for the QA pass. It fetches its rules from the `main` branch of vercel-labs/web-interface-guidelines on every run, so the rules can change between runs.
  - `vercel-react-best-practices`: React and Next.js performance rules for the build.
  - `vercel-react-view-transitions`: only when motion is in scope.
  - `vercel-composition-patterns`: optional, when the work becomes a component library.
- **Don't offer** `deploy-to-vercel` or `vercel-cli-with-tokens`. The first links projects and makes a public temporary deploy without asking. The second prints tokens from the environment and deletes environment variables with `-y`.
- **Install (PowerShell):**

  ```powershell
  $env:DISABLE_TELEMETRY = "1"
  npx skills add vercel-labs/agent-skills@<commit> --skill web-design-guidelines -a claude-code -g --copy
  ```

  On macOS or Linux: `DISABLE_TELEMETRY=1 npx skills add vercel-labs/agent-skills@<commit> --skill web-design-guidelines -a claude-code -g --copy`.

  Repeat with the other skill names. Pass the skill's frontmatter name, which differs from the folder name for some skills. For example, folder `react-best-practices` is installed as `vercel-react-best-practices`.

  The manual alternative is to copy `skills/<folder>` from a clone you have read into the skills folder, named after its frontmatter name.

## Emil Kowalski's skills

- **What:** emilkowalski/skills (MIT). Motion and interface craft. This skill's motion numbers and worst-case content test come from it.
- **When:**
  - Once a direction is chosen, `/prototype` (aiforui.dev/skills/prototype) builds working variants of a single component on named axes.
  - `/break-ui` stress-tests a build.
  - `/review-animations` and `/animate` help in the motion phase.
  - `/learn-taste` turns the person's picks into `DESIGN.md` rules.
- **Note:** several of these are user-invoked only. Tell the person the command rather than calling it.
- **Install:** `npx skills@latest add emilkowalski/skills`, or copy single folders from a clone you have read.

## Impeccable

- **What:** pbakaus/impeccable (Apache-2.0). This skill's identity lock, rut, candidate-world method, modes and checks are built on its ideas.
- **When:** if it is installed, `/impeccable critique` on the incumbent and `/impeccable polish` on the finished build are strong extra passes.
- **Risks to state before anyone installs it:**
  - Its hooks run outside the model's approval.
  - It downloads an engine binary.
  - It fetches directions from its online catalog when a new design starts, even with telemetry off.
  - Its live mode can fall back to running an agent CLI with permission checks off. Set `IMPECCABLE_LIVE_COPY_AGENT=chat` to prevent that.

## good-css

- **What:** vojtaholik/good-css (MIT). CSS practices. The eight rules in `craft-floor.md` are distilled from it.
- **When:** any CSS work. The full rules are readable without installing anything, at good-css.com (`/skills/good-css/SKILL.md`).

## Gentleface

- **What:** an MIT icon set with plain-URL access (`gentleface.com/icons.txt`, per-icon files) and an optional MCP server.
- **When:** a direction needs a line-icon family.
- **Note:** connecting its MCP server is the person's call.

## footer.design

- **What:** a curated gallery of website footers.
- **When:** browsing references for a footer.
- **Note:** no licence or terms are stated, so link to entries and never copy or embed its screenshots.

## Skills from the same library

These ship in the same skills library, when it is installed:

- `copy-deslop`: run it on every piece of copy.
- `frontend-design-anti-slop`: for building a chosen direction without a builder companion.
- `cinemagraph`: for animating a finished still.
- `beautify-github-readme`: when the surface is a README.
