# Maintaining

The runbook for this repository: document index, research workflow, site workflow, and commands.

## Documents

- [`verification_design.md`](verification_design.md): principles for building agent workflows that verify work through executable external signals rather than self-review.
- [`ai-design-patterns/`](ai-design-patterns/): GoF-inspired pattern catalog for reusable agentic software patterns.
- [`verificationdesign/`](verificationdesign/): Astro static site for publishing verification design principles and pattern cards at `verificationdesign.com`.

## Local Structure

- `research/reviewed/`: reviewed source notes used before updating the canonical doc.
- `ai-design-patterns/cards/`: AI design pattern cards.
- `ai-design-patterns/scripts/lint_patterns.py`: pattern-card linter driven by `ai-design-patterns/constitution.json`.
- `verificationdesign/src/`: Astro source for the public website.
- `verificationdesign/src/content/loaders/cardsLoader.mjs`: site content loader that reads cards from `ai-design-patterns/cards/`.
- `verificationdesign/scripts/verify-site.sh`: local site verification wrapper.
- `research/scouts/`: arXiv scout query config; raw scout outputs stay local and untracked.
- `research/triage/`: first-pass candidate summaries and relevance judgments.
- `research/link-confirmations.txt`: manual confirmations for valid links that block automated checks.
- `scripts/verify.py`: local mechanical verifier.
- `scripts/scout.py`: arXiv discovery script; retrieval only, no judgment.
- `scripts/digest_triage.py`: compact reading digest from triage notes.
- `scripts/rank_triage.py`: anchor-calibrated triage ranking; requires human-tagged anchors.

## Research Workflow

1. Scout mechanically in `research/scouts/` when looking broadly.
2. Triage promising candidates in `research/triage/` using paraphrase and first-pass judgment.
3. Review a new source in `research/reviewed/` before updating the canonical doc.
4. Append dated updates to `verification_design.md`; do not overwrite prior research state.
5. Keep inline citations and the References table balanced.
6. Run `python3 scripts/verify.py`. A source update is not done after a `--skip-links` run; full verification includes link liveness.
7. Treat substantive characterization as a human review item, not a mechanically verified fact.

If a publisher blocks automated link checks but the link is manually confirmed valid, record it in `research/link-confirmations.txt`.

For `ai-design-patterns/`, run the local pattern linter when editing cards. It is expected to fail on cards that have not yet been migrated to the current schema.

## Website Workflow

`verificationdesign/` is the publishable website for this research layer. The site reads pattern cards directly from `ai-design-patterns/cards/`; do not fork or hand-copy card prose into the site.

Use `npm run dev` inside `verificationdesign/` for local UX work. Use browser automation, screenshots, and accessibility checks for UI changes when available. Treat visual approval by the model as insufficient; verify layout, navigation, and accessibility through external signals.

Before site work is considered done, run:

1. `npm run build`
2. `npm run check`
3. `npm run lint:cards`
4. `npm run a11y` when a browser can launch in the local environment

Deployment target is Cloudflare Pages with root directory `verificationdesign`, build command `npm run build`, and output directory `dist`.

## Commands

- `make help`: list top-level repo commands.
- `make check`: run full repo verification and full website verification.
- `make verify-local`: run repo mechanical checks without network link liveness.
- `make site`: run the website build, Astro check, card lint, and accessibility smoke check.
- `python3 scripts/verify.py`: run local mechanical checks.
- `python3 scripts/verify.py --include-scout-links`: also check links in scout artifacts.
- `python3 scripts/scout.py --dry-run`: print planned arXiv OAI-PMH requests.
- `python3 scripts/scout.py --start-date 2026-05-30 --end-date 2026-06-02`: run an exact arXiv scout window.
- `python3 scripts/digest_triage.py --input research/triage/example.md --outfile research/triage/digests/example-digest.md`: compact a triage note into a reading queue.
- `python3 scripts/rank_triage.py --anchors research/triage/anchors.md --validate-anchors`: validate ranking anchors.
- `python3 ai-design-patterns/scripts/lint_patterns.py`: lint migrated AI design pattern cards.
- `cd verificationdesign && npm run dev`: run the website locally.
- `cd verificationdesign && npm run verify`: build, type-check, lint cards, and run the accessibility smoke check.

`scripts/scout.py` harvests arXiv via the OAI-PMH `ListRecords` interface serially with a fixed 10 second delay between requests, stops immediately on `429`, backs off on `503` and timeouts, caps raw OAI pages per category, and exits non-zero rather than writing partial scout output after a request failure. OAI-PMH windows track metadata datestamps, not original submission dates; per-entry Created, Updated, and OAI datestamp fields let triage tell new submissions, re-versions, and metadata corrections apart.

## UX Verification Loop

For website UX work, use a design input as the acceptance contract. The intended loop is:

1. Start the site with `make site-dev`.
2. Use Playwright MCP, when available, to open the running site.
3. Capture desktop and mobile screenshots for the changed surfaces.
4. Mechanically compare the running page against the design input: layout, navigation, text overflow, interaction states, and accessibility-visible labels.
5. Apply focused fixes, then repeat the browser checks.
6. Stop when the requested task is done, or when all tasks in the design input are satisfied.

After the browser loop, run `make site` if the environment can launch a browser for `pa11y-ci`; otherwise run `make site-build site-check site-lint-cards` and report the skipped accessibility step.
