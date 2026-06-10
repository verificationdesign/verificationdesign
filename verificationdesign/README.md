# verificationdesign.com

Astro static site for verification design principles and patterns.

Pattern cards are read directly from `../ai-design-patterns/cards/` via a
custom content loader. The site never modifies the source cards.

## Local dev

    npm install
    npm run dev

Site serves at http://localhost:4321.

## Build

    npm run build

Output lands in `dist/`. Designed for Cloudflare Pages.

Recommended Cloudflare Pages settings:

- Root directory: `verificationdesign`
- Build command: `npm run build`
- Output directory: `dist`

## Lint pattern cards

    npm run lint:cards

Runs the manuscript-shape linter in `../ai-design-patterns/scripts/lint_patterns.py`.

## Accessibility smoke check

    npm run build
    npm run a11y

Runs `pa11y-ci` against generated HTML in `dist/`.

## Full local verification

    npm run verify

Runs build, Astro type checks, card lint, and the accessibility smoke check.

## Draft gating

By default, local builds render every valid card in `../ai-design-patterns/cards/`.
For a release preview, set `SITE_CARD_ALLOWLIST` to a comma-separated list of
approved card slugs:

    SITE_CARD_ALLOWLIST=constitution,executable-analog,comparator npm run build

The allowlist filters rendered pages, pattern indexes, references, and related
pattern links. It does not modify source cards.

## Internationalization posture

The site is English-only for launch, but repeated UI chrome lives in
`src/i18n/ui.ts`. Future translated routes should keep English canonical URLs
stable and add locale-prefixed alternates such as `/es/patterns/...`.

## Structure

    src/
      content/
        config.ts          collection schemas
        loaders/           custom content loaders (reads source cards)
      layouts/             BaseLayout, CardLayout
      components/          Header, Footer, CategoryGrid, Breadcrumb, CopyButton
      i18n/                UI strings and locale defaults
      lib/                 reference aggregation utilities
      pages/               routes
      styles/              global CSS
    public/                static assets
