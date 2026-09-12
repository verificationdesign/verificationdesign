# AGENTS.md: Research Notes

Guidance for any agent (Claude Code, Codex) working in this repo. Read fully before acting.

## What this repo is

A personal research-notes layer: sourced, annotated thinking on agentic AI verification, evaluation methodology, and design patterns for checking agent work. It is the middle layer between **code** (products live in their own repos) and **formal papers** (own pipeline). Living reference docs, public-benefit methodology, not a product.

## Scope boundary: read first

**In scope:** general methodology, design principles, annotated bibliographies, evaluation/verification technique, and patterns for executable checks of agent behavior.

**Never add here:**
- Product-specific design tied to a separate codebase; it stays in that repo.
- Offensive or dual-use material: working exploits, weaponized jailbreak payloads, turnkey attack automation. This repo is **methodology only**. If a doc must mention a misuse or failure class, describe it at the level needed to motivate verification or mitigation, never as copy-pasteable instructions.
- Formal paper drafts: link to them, don't mirror them.

When unsure whether something is dual-use, leave it out and ask the human. Default to exclusion.

## Delegation discipline (architect and worker)

Claude Code is the architect: plan, design, review, sign off, and direct the Codex worker via dispatch. The architect does not hand-write substrate changes (docs, scripts, site code) in the loop; that is the worker's lane. The architect owns plan docs, review, merge, and sign-off.

- **Default to dispatch.** Delegation is the norm, not the exception. It keeps the cycle cross-model by design (one model implements, another reviews), and the architect can run workers in parallel or keep planning while implementation is in flight.
- **Skip the governed cycle only for small tasks**: a one-line fix, a typo, a trivial config tweak. If a change needs design judgment or touches more than a couple of files, dispatch it. When unsure, dispatch.
- Verification discipline applies regardless of who wrote the change: the architect still runs the mechanical checks on worker output before sign-off.
- Workers do not run `npm run a11y`. The worker sandbox cannot launch a browser, and each attempt crashes Chrome for Testing and leaves crash reports on the host. The architect runs the a11y check on worker output.

## Structure

- `README.md`: public-facing front door; what the project is and how it enforces its own rules.
- `MAINTAINING.md`: the runbook; doc index, research workflow, site workflow, and commands.
- `verification_design.md`: canonical source document for verification design principles.
- `ai-design-patterns/`: GoF-inspired pattern catalog for reusable agentic software patterns.
- `ai-design-patterns/cards/`: pattern cards; migrated cards should pass the pattern linter.
- `ai-design-patterns/constitution.json`: editorial constitution for the pattern catalog.
- `ai-design-patterns/scripts/lint_patterns.py`: mechanical linter for pattern-card structure.
- `verificationdesign/`: Astro static site for publishing the principles and pattern cards at `verificationdesign.com`.
- `verificationdesign/src/content/loaders/cardsLoader.mjs`: custom loader that reads cards from `ai-design-patterns/cards/`; the website should not fork source card prose.
- `verificationdesign/scripts/verify-site.sh`: local wrapper for website verification.
- `research/synthesis.md`: append-only evidence holding area organized by claim, pending maintainer fold.
- `research/reviewed/`: short source review notes created before canonical doc updates.
- `research/scouts/`: scout configuration; raw scout outputs stay local and untracked (sources that matter are promoted through triage and review).
- `research/triage/`: first-pass judgment notes for scout candidates before full source review.
- `research/link-confirmations.txt`: dated manual confirmations for valid scholarly links that block automated checks.
- `research_tools/`: the tested, stdlib-only package behind the research pipeline; run as `python3 -m research_tools <verify|scout|digest>`. `verify` runs mechanical checks. `scout` performs arXiv OAI-PMH discovery, retrieval only. `digest` produces a compact reading digest from triage notes.
- `research/scouts/config.json`: the project profile for all topic-specific data: arXiv categories, keyword groups, anchor phrases, expand-on seeds, principle titles, canonical doc paths, and digest heuristics. The package code carries no topic text.
- `tests/`: unittest suite with captured fixtures; run with `make test`, also run by `make verify-local` and CI.

## Document conventions

- Every empirical/research claim carries an inline source citation (e.g. `[arXiv:2309.11495]`) **and** a matching row in that doc's References table.
- **Holding area, then fold.** New evidence accumulates in `research/synthesis.md` under claims and is append-only there. It reaches `verification_design.md` only when the maintainer folds it under the fold-in bar, by changing principle prose or the folded `Research` callouts. Do not add dated update notes to `verification_design.md`.
- **Stable numbering.** Principle/section numbers never shift. Append; do not renumber.
- Date every update note (ISO 8601, e.g. `2026-05-29`).
- Do not use em dashes in repo prose. Use a colon, semicolon, comma, parentheses, or a new sentence. Preserve original punctuation in verbatim quotes and source excerpts.
- Git history is the versioning. No manual `v2` filenames, no copied snapshots.
- Do not commit mirrored book PDFs or publisher PDFs unless redistribution is clearly permitted. Keep local reference copies out of git.

## Pattern catalog discipline

`ai-design-patterns/` is allowed to be more exploratory than `verification_design.md`, but it still follows the repo's verification habits.

- Pattern cards should be practical, Python-oriented, and built around a paired Pattern / Antipattern example.
- Pattern code blocks must be stdlib-only: no third-party imports. The card-code runner (`run_card_code.py`) executes each Pattern block under a standalone `python3.13` that has no third-party packages installed, so a missing import is reported as DEP and fails the runner gate. Examples must run as pasted with the standard library alone (use `dataclasses` and manual validation rather than pydantic, etc.). The Antipattern block is not executed and may use illustrative undefined names.
- Migrated cards should include `Determinism Move` and `Observable Signal` sections.
- Empirical claims still need evidence. Speculative pattern language should be presented as design judgment, not research fact.
- Run `python3 ai-design-patterns/scripts/lint_patterns.py` when editing pattern cards. It is expected to fail on cards that have not yet been migrated to the new schema; do not treat those failures as blocking unrelated work.
- The pattern linter is intentionally separate from `python3 -m research_tools verify` until all cards are migrated.

## Website discipline

`verificationdesign/` is a publishable site, but it is still part of this research-notes repo. Keep it synchronized with the canonical docs and pattern cards rather than creating a separate content source.

- Source cards live in `ai-design-patterns/cards/`; the site loads them read-only.
- Agent-readable markdown twins, `llms.txt`, `llms-full.txt`, and `catalog.json` are post-build artifacts generated by `verificationdesign/scripts/build-md-twins.mjs` and verified independently by `verificationdesign/scripts/check-md-twins.mjs`; never hand-edit them.
- Keep generated site artifacts out of git: `node_modules/`, `dist/`, `.astro/`, logs, and local env files.
- For UX work, prefer browser automation with screenshots, viewport checks, and accessibility checks. Model visual judgment alone is not enough.
- If Playwright MCP is available, use it for site navigation, screenshots, and interaction checks before finalizing UI changes.
- Do not add marketing claims that outpace the research source material. The site can explain the project and organize the material, but empirical claims still need citations in the source docs.
- Site prose continuity: before publishing new prose, run a continuity pass against the destination page and its neighbors for voice, register, tone, and terminology. The prose pages speak in a collective, declarative register; the About page is the one designated first-person page. Material sourced from interviews or conversation is normalized (grammatical person, excess wording, transitions) to the destination register before implementation, then reviewed by the maintainer. `npm run lint:voice` enforces the first-person boundary mechanically; it is part of `npm run verify` and CI.
- Pushing to main deploys via CI. Push only on the maintainer's explicit instruction, given after the maintainer has inspected the rendered change. Reviewer sign-off, including an external design or review verdict, does not substitute for that instruction.
- For Cloudflare Pages, use root directory `verificationdesign`, build command `npm run build`, and output directory `dist`.

When editing the site, run the strongest available subset of:

1. `cd verificationdesign && npm run build`
2. `cd verificationdesign && npm run check`
3. `cd verificationdesign && npm run lint:cards`
4. `cd verificationdesign && npm run a11y`

If `npm run a11y` cannot launch a browser in the current environment, report that explicitly rather than treating the site as fully verified.

For design-driven UX work, treat the design input as the acceptance contract. Start the site, use Playwright MCP when available to inspect the running page, collect desktop and mobile screenshots, check navigation and interaction states, check text overflow and accessibility-visible labels, then apply focused fixes and repeat. Stop only when the requested task is done or every task in the design input is satisfied.

## Verification discipline (the maintainer contract)

Derived from `verification_design.md`; this repo follows its own principles.

- **External signals over self-review.** Verify mechanically. Never approve an update because it "looks good"; reading-and-opining is the LLM-as-judge anti-pattern this doc warns against.
- Before any update is considered done, run `python3 -m research_tools verify` and pass **all** of:
  1. **Link liveness**: every canonical/reviewed URL or arXiv ID resolves (HTTP 200), or has a dated manual confirmation for publisher blocking.
  2. **Citation ⇄ reference balance**: every inline citation has a References row and vice versa; zero orphans in either direction.
  3. **Append-not-overwrite** on `research/synthesis.md`: `git diff` shows claim records only added, never deleted; a `Status:` line may change. `verification_design.md` prose is curated and mutable; substantive changes are protected by review, not by this gate. Use `--base-ref` or `VERIFY_BASE_REF` for multi-commit review.
  4. **Format / anchor lint**: markdown lints clean; internal `#anchors` resolve; numbering contiguous.
  5. **Provenance**: each update note names its source.
- CI gates deploy on the hermetic subset: `python3 -m research_tools verify --skip-links`, the pattern and card-code linters, and the site build/check/lint/a11y steps. Full `python3 -m research_tools verify`, including link liveness, must pass locally before any push because CI runner IPs are blocked by publishers/arXiv and cannot run link liveness reliably.
- Package tests are part of the hermetic gate. A change to `research_tools/` is not done until `make test` passes on Python 3.11 and 3.13, and a behavior change carries a test.
- **Substance is not mechanically verifiable.** Whether a finding is *correctly characterized* is a judgment call. Do **not** self-review it. Flag substantive claims for human or cross-family-model review, assemble the diff, and stop; do not auto-approve or auto-merge.
- **Grade strictly.** Print observed values for *all* checks, not only failures. Treat a zero-failure report with suspicion. Never explain away or reinterpret a failure to make it pass.

## Source review discipline

Before updating the canonical doc from a new source, create a short note in `research/reviewed/` using the local template. Assign an evidence grade as structured judgment, not mechanical truth:

- **A**: replicated, peer-reviewed, directly relevant.
- **B**: strong method and directly relevant, but limited replication or still emerging.
- **C**: plausible early evidence, preprint, narrow benchmark, or limited model/task coverage.
- **D**: background, analogy, opinion, or weak empirical support.

Also record grade confidence (`low`, `medium`, `high`), limitations, and claims needing human review. The verifier may check that these fields exist; it must not decide whether the grade is correct.

Do not mirror full papers or publisher PDFs in this repo unless their license clearly permits redistribution. If a valid scholarly link blocks automated checks, add a dated manual confirmation to `research/link-confirmations.txt` instead.

Scout outputs in `research/scouts/` are discovery artifacts, not reviewed evidence. `python3 -m research_tools scout --ledger` is allowed as optional arXiv-ID deduplication for retrieval runs; it is not a provenance ledger for canonical prose.

Triage notes in `research/triage/` are the judgment layer between scouts and reviewed notes. They may paraphrase abstracts and list possible key findings, but they are not source reviews and should not be cited from the canonical doc.

Canonical citations added after the reviewed-note workflow must have a matching source in `research/reviewed/`. `research/reviewed/LEGACY-CITATIONS.md` is only a transition index for citations that predate this workflow; do not add new citations there.

**Fold-in bar.** A reviewed note records the read and the judgment. Folding the finding into the canonical doc is a separate maintainer decision, and this bar is the default decision rule. It is judgment guidance, not a mechanical score; the verifier must not enforce it.

- Claim type sets the bar. Negative or existence findings can fold from one well-documented demonstration, scoped to the tested setting. Effectiveness or generality findings need independent corroboration before folding.
- Independent corroboration means a different method, dataset, or group, not a second correlated preprint from the same benchmarks and zeitgeist.
- A checkable mechanism lowers the bar. If the finding follows from a mechanism that can be independently verified or reproduced, ideally executably, the paper is measurement rather than the sole load-bearing evidence. Purely empirical numbers keep the bar high.
- Corroboration of an already-folded callout counts as the second source. Fold it as a dated note that names the callout it strengthens.
- Warnings may fold earlier than endorsements. Under-warning costs more than under-endorsing, so "test for X before trusting it" callouts carry a lower bar than "X works" callouts.
- Separate reproducibility signals from authority signals. Released code, data, or models are reproducibility facts that may bear on the evidence grade because they affect whether the evidence can be checked. Author seniority, dataset-creator overlap, and institutional prestige are authority facts: record them as verifiable facts and let them tune grade confidence, but they do not move the evidence grade or substitute for corroboration.
- When the bar is ambiguous, hold and watch. The note layer loses nothing, and the hold decision is recorded in the note's Suggested Update section.

**Expand-on.** Expand-on is a reviewed note's discovery posture, separate from the fold decision.
Hold-and-watch is passive: record the read and wait for corroboration to surface through ordinary scouting.
Expand-on is active: the note names seed topics, and those topics are registered in `research/scouts/config.json`
under the `expand_on` block so the next harvest actively hunts associated and corroborating work.
It is orthogonal to fold or hold. A held note can be expand-on to seek the corroboration the fold-in bar wants before folding,
and a folded note can be expand-on to seek further corroboration of a callout, which the fold-in bar already counts as a second source toward a strengthening note.
Record the disposition and seed topics in the note's Suggested Update, and add the matching `expand_on` entry to the scout config.
The verifier does not enforce this; it is a discovery practice, not a mechanical gate.

## Right-sizing

This is a local notes repo, not a security harness. Keep verification a lightweight script. Do **not** build isolation / TTL / ledger-grade apparatus for prose. Match verification weight to stakes.

## Commands

- Verify: `python3 -m research_tools verify`
- Verify including scout artifact links: `python3 -m research_tools verify --include-scout-links`
- Scout: `python3 -m research_tools scout --dry-run`
- Scout exact window: `python3 -m research_tools scout --start-date 2026-05-30 --end-date 2026-06-02`
- Pattern lint: `python3 ai-design-patterns/scripts/lint_patterns.py`
- Card-code runner: `python3 ai-design-patterns/scripts/run_card_code.py` (executes each card's Pattern block under python3.13; fails if it does not run or no assertion executes; pass a card name to scope)
- Triage digest: `python3 -m research_tools digest --input research/triage/2026-08-15-scout-allocation.md --outfile research/triage/digests/2026-08-15-scout-allocation-digest.md`. Digests under `research/triage/digests/` are generated by this command.
- Site dev: `cd verificationdesign && npm run dev`
- Site markdown twins: `cd verificationdesign && npm run build:twins && npm run check:twins`
- Site verify: `cd verificationdesign && npm run verify`
- Live site smoke test: `cd verificationdesign && npm run smoke:live`
- Top-level check: `make check`
- Local no-network check: `make verify-local`

The package scout (`python3 -m research_tools scout`) must stay polite to arXiv: harvest via OAI-PMH serially with a fixed 10 second delay, cap raw OAI pages per category, stop immediately on rate limits, honor retry backoff for server errors and timeouts, and treat request failures as a failed run rather than a "no candidates" result. OAI-PMH windows track metadata datestamps, not original submission dates; a record can appear because it was newly submitted, re-versioned, or had its metadata corrected. Triage uses the per-entry Created, Updated, and OAI datestamp fields to tell those cases apart.
