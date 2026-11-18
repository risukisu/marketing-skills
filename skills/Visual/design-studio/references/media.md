# Media: frames and rules per medium

Every direction is shown in the frame it will ship in. A report shown as a website hero gets judged on the wrong things.

| Medium | Mode | Mock frame | What the mock must show | Notes |
|---|---|---|---|---|
| Landing page, marketing site | Persuade | 1440 × 900 and 390 × 844 | The first viewport, then the next screen. The real offer and the real main action, in working form. | The first viewport is the thesis, not a header. The closing section and footer get designed too. footer.design is a gallery to browse for footers, not a source to copy. |
| Portfolio, gallery, showcase | Experience | 1440 × 900 and 390 × 844 | The work leading from the first viewport, plus one project or detail view. | The interface recedes. Use real work samples, never stock. |
| Web app, dashboard, tool | Operate | 1440 × 900 working screen | One real task screen with realistic data, including a loaded state, an empty state and one error. | The direction lends its faces, colours, density and a single signature move. Navigation and controls stay conventional. Use realistic worst-case data (see craft-floor). |
| HTML artifact (claude.ai) | By content | The artifact's own viewport, light and dark | The page as published, in both themes. | Load the harness's artifact design guidance when available. Its page contract (title, theming selectors, allowed script sources, size limit) wins. |
| Report (HTML or PDF) | Read | A4 or Letter page at print size, plus a screen view | The cover or title block with the key finding, and one interior page with a table, plus a chart when the content has a series to chart. | Never invent a series to fill the frame; a table carries a few totals better. Numbers right-aligned in `tabular-nums`. Charts go through a dataviz skill when one exists. Add a print stylesheet (see print notes). The reading column stays calm. |
| Document (DOCX, PDF) | Read | A4 or Letter page in HTML at print size | The cover and one interior spread: headings, body, a table, a callout. | Body 10 to 12 pt, margins at least 18 mm (*house defaults*). Build through the document skill after the pick. Name only faces that are available offline or embeddable. |
| Slide deck | Persuade or Read | 1920 × 1080 (16:9) | The title slide, one content slide, one data slide. | Body type at least 24 pt, one idea per slide. Build through the slide skill after the pick. |
| Email | Persuade | 600 px single column | Header, main message, one call to action. | Inline-safe CSS, tables for layout, no web fonts assumed. |
| Component or section | Inherits | In place, inside the existing page | The component in its real context, in all its states. | The surrounding identity is fixed. Directions vary structure, density and interaction (see SKILL.md, the directions). |

## Print notes

For anything that will be printed or exported to PDF, print-preview each mock and look at the pages. The test renders kept hitting these:

- Entrance animations and transitions still running, or frozen half-drawn, in print. Turn them off in `@media print`.
- Titles placed over images or maps that end up hidden behind them in print.
- Web buttons printed as buttons. In print, a call to action becomes its URL or address, written once.
- Fixed-width figure columns that overflow when the figures are large.
- A contents list pushed above the content on phones, so the key finding falls below the first screen.

## Rendering notes

- Load fonts from Google Fonts or a free foundry in mocks, and check that they cover the content's scripts.
- Mocks are throwaway HTML and CSS in one file each. They should still follow `craft-floor.md`, because a sloppy mock gets judged as a sloppy direction.
- Check every mock at 390 px for horizontal scroll and for long names or headings cut off at the edge.
- Screenshot at the sizes in the table when a browser tool is available. For Operate mocks, also screenshot the empty and error states.
- Block analytics and tracking scripts in any browser you drive against a local build of a real site, so test visits don't land in its statistics.
