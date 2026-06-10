# AGENTS.md: verificationdesign.com

Guidance for agents working inside the Astro website. Also read the repo-level `../AGENTS.md` before making substantive changes.

## What This Site Is

`verificationdesign/` is the static website for `verificationdesign.com`. It publishes the verification design principles and the AI design pattern cards from the parent research repo.

The site is an interface over the research material, not a second source of truth.

## Content Boundary

- Pattern-card source lives in `../ai-design-patterns/cards/`.
- The custom content loader reads those cards directly. Do not copy card prose into site pages.
- Canonical verification principles live in `../verification_design.md`.
- Keep empirical claims tied to the cited source material in the parent repo.
- Do not add offensive or dual-use examples beyond high-level methodology and mitigation framing.

## Local Commands

- Install dependencies: `npm install`
- Dev server: `npm run dev`
- Build: `npm run build`
- Astro check: `npm run check`
- Card lint: `npm run lint:cards`
- Accessibility smoke check: `npm run a11y`
- Full verification: `npm run verify`

`npm run verify` runs build, Astro checks, card lint, and the accessibility smoke check. If the accessibility step cannot launch a browser in the current environment, report that as an unverified item.

## UX Work

Use browser automation for UX changes when available. Prefer Playwright MCP or equivalent browser tooling for:

- Desktop and mobile viewport screenshots.
- Navigation and interaction checks.
- Text overflow and overlap checks.
- Accessibility smoke checks.
- Confirming that pattern pages render from source cards.

Do not rely on model-only visual review for final approval.

For design-driven changes, use this loop:

1. Treat the design input as the acceptance contract.
2. Start the site with `make site-dev` from the repo root or `npm run dev` here.
3. Use Playwright MCP to inspect the running page.
4. Capture desktop and mobile screenshots for changed surfaces.
5. Check layout, navigation, interaction states, text overflow, and accessibility-visible labels against the design input.
6. Apply focused fixes and repeat browser validation.
7. Stop when the requested task is done or all tasks in the design input are satisfied.

## Build And Deploy

Cloudflare Pages settings:

- Root directory: `verificationdesign`
- Build command: `npm run build`
- Output directory: `dist`

Generated artifacts should stay out of git: `node_modules/`, `dist/`, `.astro/`, logs, and local env files.
