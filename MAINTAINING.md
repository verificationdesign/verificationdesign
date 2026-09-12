# Maintaining

The runbook for this repository: document index, research workflow, site workflow, and commands.

## Documents

- [`verification_design.md`](verification_design.md): principles for building agent workflows that verify work through executable external signals rather than self-review.
- [`ai-design-patterns/`](ai-design-patterns/): GoF-inspired pattern catalog for reusable agentic software patterns.
- [`verificationdesign/`](verificationdesign/): Astro static site for publishing verification design principles and pattern cards at `verificationdesign.com`.

## Local Structure

- `research/synthesis.md`: append-only evidence holding area organized by claim, pending maintainer fold.
- `research/reviewed/`: reviewed source notes used before updating the canonical doc.
- `ai-design-patterns/cards/`: AI design pattern cards.
- `ai-design-patterns/scripts/lint_patterns.py`: pattern-card linter driven by `ai-design-patterns/constitution.json`.
- `verificationdesign/src/`: Astro source for the public website.
- `verificationdesign/src/content/loaders/cardsLoader.mjs`: site content loader that reads cards from `ai-design-patterns/cards/`.
- `verificationdesign/scripts/verify-site.sh`: local site verification wrapper.
- `research/scouts/`: arXiv scout query config; raw scout outputs stay local and untracked.
- `research/triage/`: first-pass candidate summaries and relevance judgments.
- `research/link-confirmations.txt`: manual confirmations for valid links that block automated checks.
- `research_tools/`: tested package behind the research pipeline; `python3 -m research_tools verify` is the local mechanical verifier.
- `research_tools/scout.py`: arXiv discovery script; retrieval only, no judgment.
- `research_tools/digest.py`: compact reading digest from triage notes.

## Research Workflow

1. Scout mechanically in `research/scouts/` when looking broadly.
2. Triage promising candidates in `research/triage/` using paraphrase and first-pass judgment.
3. Review a new source in `research/reviewed/` before updating the canonical doc.
4. File new evidence under a claim in `research/synthesis.md`; fold into `verification_design.md` only under the fold-in bar.
5. Keep inline citations and the References table balanced.
6. Run `python3 -m research_tools verify`. A source update is not done after a `--skip-links` run; full verification includes link liveness.
7. Treat substantive characterization as a human review item, not a mechanically verified fact.

If a publisher blocks automated link checks but the link is manually confirmed valid, record it in `research/link-confirmations.txt`.

For `ai-design-patterns/`, run the local pattern linter when editing cards. It is expected to fail on cards that have not yet been migrated to the current schema.

## Website Workflow

`verificationdesign/` is the publishable website for this research layer. The site reads pattern cards directly from `ai-design-patterns/cards/`; do not fork or hand-copy card prose into the site.

Use `npm run dev` inside `verificationdesign/` for local UX work. Use browser automation, screenshots, and accessibility checks for UI changes when available. Treat visual approval by the model as insufficient; verify layout, navigation, and accessibility through external signals.

Agent-readable markdown twins, `llms.txt`, `llms-full.txt`, and `catalog.json` are generated into `verificationdesign/dist/` after the Astro build. Run `npm run build:twins` to generate them and `npm run check:twins` to verify them. These artifacts are derived from `verification_design.md`, the pattern-card sources, and site metadata: never hand-edit them. `verificationdesign/src/lib/failure-map.mjs` is the single source for failure routing in the HTML page and generated artifacts. The development server does not serve generated artifacts; they are available only after the post-build generator runs. After deployment, run `npm run smoke:live` to check the live edge. Run `npm run measure:cards` against a running preview after any change to `CategoryGrid.astro` or the card CSS; optional screenshots belong in the gitignored `verificationdesign/local/` directory.

Before site work is considered done, run:

1. `npm run build`
2. `npm run check`
3. `npm run lint:cards`
4. `npm run a11y` when a browser can launch in the local environment

Deployment target is Cloudflare Pages with root directory `verificationdesign`, build command `npm run build`, and output directory `dist`.

## Skills package

`skills/` contains self-contained verification-design and verification-audit Agent
Skills, each with a packaged catalog, scripts and references; repo-side fixtures
exercise validation, routing and rendering. Python 3.11 or later is required.
Install and invocation details are in [skills/README.md](skills/README.md).

Re-pin as a deliberate release: tag the chosen corpus commit with `corpus/vX.Y.Z`.
At that commit, run `GITHUB_SHA=<pin> node scripts/build-md-twins.mjs` from
`verificationdesign/` after the site build. Copy the emitted `dist/catalog.json`
byte for byte into both skills. Update the five metadata fields in both SKILL.md
files: version, corpus-revision, corpus-tag, catalog-sha256 and principles-sha256.
The catalog hash is over file bytes; source hashes normalize UTF-8 CRLF to LF,
strip trailing newlines and append exactly one LF. Bump the skills version (at least
minor for a re-pin), refresh affected records and expected outputs, update CHANGELOG,
and tag the reviewed skills release with `skills/vX.Y.Z`. The maintainer owns tags
and release decisions.

Run `python3 scripts/check_skills.py` for hermetic pin, fixture and loopback HTTP
tests; `--links` adds live URL and source-hash checks, and `--skills-ref` invokes the
pinned reference validator using uvx on a temporary copy with only the top-level
invocation flag removed. The last two checks require network and run locally, not
in CI. `make skills` and `make verify-local` run the hermetic checker; `make verify`
also runs live checks. A sandbox that refuses a loopback bind cannot pass the
retrieval tests; run them on the maintainer's host and report the failure explicitly.

## Commands

- `make help`: list top-level repo commands.
- `make check`: run full repo verification and full website verification.
- `make verify-local`: run repo mechanical checks without network link liveness.
- `make site`: run the website build, Astro check, card lint, and accessibility smoke check.
- `python3 -m research_tools verify`: run local mechanical checks.
- `python3 -m research_tools verify --include-scout-links`: also check links in scout artifacts.
- `python3 -m research_tools scout --dry-run`: print planned arXiv OAI-PMH requests.
- `python3 -m research_tools scout --start-date 2026-05-30 --end-date 2026-06-02`: run an exact arXiv scout window.
- `python3 -m research_tools digest --input research/triage/2026-08-15-scout-allocation.md --outfile research/triage/digests/2026-08-15-scout-allocation-digest.md`: compact a triage note into a reading queue. Digests under `research/triage/digests/` are generated by this command.
- `python3 ai-design-patterns/scripts/lint_patterns.py`: lint migrated AI design pattern cards.
- `cd verificationdesign && npm run dev`: run the website locally.
- `cd verificationdesign && npm run build:twins`: generate markdown twins and agent discovery files after an Astro build.
- `cd verificationdesign && npm run check:twins`: independently verify generated markdown twins and discovery files.
- `cd verificationdesign && npm run verify`: build, type-check, lint cards, and run the accessibility smoke check.

`python3 -m research_tools scout` harvests arXiv via the OAI-PMH `ListRecords` interface serially with a fixed 10 second delay between requests, stops immediately on `429`, backs off on `503`, timeouts and dropped connections (Retry-After honored up to 300 seconds), caps raw OAI pages per category, marks a category whose read stopped at `--max-per-category`, and exits non-zero rather than writing partial scout output after a request failure. OAI-PMH windows track metadata datestamps, not original submission dates; per-entry Created, Updated, and OAI datestamp fields let triage tell new submissions, re-versions, and metadata corrections apart.

## UX Verification Loop

For website UX work, use a design input as the acceptance contract. The intended loop is:

1. Start the site with `make site-dev`.
2. Use Playwright MCP, when available, to open the running site.
3. Capture desktop and mobile screenshots for the changed surfaces.
4. Mechanically compare the running page against the design input: layout, navigation, text overflow, interaction states, and accessibility-visible labels.
5. Apply focused fixes, then repeat the browser checks.
6. Stop when the requested task is done, or when all tasks in the design input are satisfied.

After the browser loop, run `make site` if the environment can launch a browser for `pa11y-ci`; otherwise run `make site-build site-check site-lint-cards` and report the skipped accessibility step.
