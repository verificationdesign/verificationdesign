---
name: verification-design
description: "Write a verification plan for work that is being designed or built: what it is, numbered verification requirements, and the checks that serve them, each justified by an applicability judgment against the verificationdesign.com pattern catalog at a pinned revision. Not an audit of existing code. Needs a scope line. Do not run without an explicit request."
license: MIT
compatibility: Python 3.11 or later, standard library only. Explicit-only invocation verified on Claude Code 2.1.263, 2.1.265 and 2.1.267 (.claude/skills) and Codex CLI 0.153.4 (.agents/skills, ~/.agents/skills), 2026-09-08 and 2026-09-10. Other hosts untested and may model-activate this skill.
disable-model-invocation: true
metadata:
  disable-model-invocation: "true"
  version: "1.5.0"
  corpus-revision: "e632a86b2ca8fbb7f83b3130ba083784c7817667"
  corpus-tag: "corpus/v1.0.0"
  catalog-sha256: "b1d737c5ea62e18fc276b8efe64d963e1326c7f93c8b2e639515ed2583ce2d3f"
  principles-sha256: "03033f7084e8fee60e5f7fff7249238af9f375942ad856d4cf485d22d68bf61a"
---

# Verification design

## Purpose

Write a verification plan for the scoped work, leading with its design and numbered verification requirements, followed by the applicability judgments that justify the chosen patterns. This is neither an audit of existing code nor a mechanical inference from prose. Scripts check the record and render the plan; the operator reviews the design and judgments.

## When not to use

Do not run without an explicit request for this skill. Do not proceed without a resolved scope. For an existing artifact that needs findings, use the audit skill only if the operator requests it.

The skill reads the artifact and takes no part in the host repository's workflow, seats, or messaging; scope resolves before anything else happens.

## Inputs

- Artifact: default is the current working tree. Override: a path or URL given as the
  invocation argument or named in the conversation. Never asked for. The artifact may
  be absent or a description only; then write the design from the scope and conversation
  and record that in an assumption with topic `design-source`. With no artifact, every
  evidence string quotes the design written in this record; the assumption states that
  verdicts are conditioned on the author's own design and are not artifact evidence.
- Scope: one line naming the part or behavior in question. Taken from the invocation
  argument text or from the conversation if the operator already said it. If neither
  supplies it, ask exactly one question and stop until answered. Never guess scope.
- Both resolved values are echoed at the top of the output.
- If resolved scope differs from the operator's words verbatim, record a `scope-expansion` assumption quoting the original words.

## Procedure

Run commands from this skill directory, with absolute paths for operator-visible records and outputs outside it. Python 3.11 or later is required. No command prompts interactively. Records and outputs go in a dated directory the operator can see, beside the artifact or where the operator says, never in system temp storage and never inside the skill directory. Scripts create that directory when it does not exist.

1. Resolve artifact and scope by the rules above. No script runs until scope is resolved.
2. Verify the packaged dependency and show the interpreter version from `--check`:

   ```bash
   python3 scripts/load_catalog.py --check
   ```

3. Scaffold the record at an operator-visible path. The scaffold carries the `skill`
   identity (name, version and the pinned hashes) so the record states which condition
   set judged it; do not edit that object.

   ```bash
   python3 scripts/scaffold_record.py --artifact "resolved artifact" --scope "resolved scope" --output /absolute/path/record.json
   ```

4. Read `assets/catalog.json` and [judgment-record.md](references/judgment-record.md)
   first; the plan and the judgments both draw on them.

   Retrieve source text only through this command when prose beyond the structured catalog is needed:

   ```bash
   python3 scripts/load_catalog.py fetch principles --offline
   ```

5. Write `plan.design` (two to eight sentences describing the components and workflow)
   and numbered `plan.requirements`, each stating what must be true and naming the
   check, its inputs, and what pass and fail look like. Read an existing design document
   in the artifact when available and cite it in `plan.source`; otherwise write the
   design from the scope and conversation, omit `source`, and record a `design-source`
   assumption stating that origin. With no artifact, every evidence string quotes the
   design written in this record; state in `design-source` that verdicts are conditioned
   on the author's own design and are not artifact evidence.
6. Fill the scaffold: characterize what is generated, by whom, the completion signal,
   and self-review points. Declare the `verification-path` assumption before judging.
   Preserve every catalog condition verbatim and in order. Record each verdict and
   its artifact evidence. Unknown exclusions block apply; keep unknowns visible.
   For unknowns, explain why judgment is unavailable, write `No source in the evidence set addresses this condition.` when none does, and cite only text bearing on the condition.
   Record post-plan evidence in an undecided card's optional `resolution`, beside its original verdict.
   Every applied card must serve at least one requirement; list it in that requirement's `patterns`.
   This is a judgment step, not an executable inference from prose.
   Fill the record-level fields as well:
   - `models`: the model family producing this record as `verifier`, and the family that
     produced the artifact as `generator`, `unknown` when not recorded anywhere, or `none`
     when no model produced it. Use the family vocabulary in the record reference.
   - `artifact_identity`: the artifact revision and a sha256 per file read, so a reader
     can tell which bytes were judged. Omit only when nothing readable was examined.
   - `measurements`: one entry per command, or per group of same-kind commands with one
     purpose, run against the artifact; a grouped entry states its command count in `note`.
     Record its exit code and `kind`: `inspection` when the command only read the artifact, `execution`
     when it ran the artifact. Cite measurements by id from evidence. An execution shows
     what the artifact does; an inspection shows what it contains; neither is evidence
     that the artifact records anything.
7. Validate; correct record errors and rerun until exit 0. If the packaged dependency
   fails, stop and report it without changing the pin.

   ```bash
   python3 scripts/validate_judgments.py /absolute/path/record.json
   ```

8. Check artifact citation existence and bounds, and requirement-id references against
   the plan. Require exit 0 or record an explanation
   in `assumptions`, then revalidate. This check does not assess evidence meaning.
   A root is required whenever the record cites files; roots are directories.
   Several roots may be given; first file match wins, so order them deliberately.
   Paste any exit-4 JSON objects from the fetch command in step 4 into the record's
   `unavailable_sources` list before final validation and rendering.

   ```bash
   python3 scripts/check_citations.py /absolute/path/record.json --root /absolute/path/artifact-dir --root /absolute/path/evidence
   ```

9. Render the validated record:

   ```bash
   python3 scripts/render_plan.py /absolute/path/record.json --output /absolute/path/verification-plan.md
   ```

10. Complete the closing checklist. Validation does not verify substantive judgments.

Source text is optional; step 4 supplies the fetch command. Replace `principles`
with a catalog card id for card text.

Omit `--offline` only when source retrieval is wanted and network is available.
When `load_catalog.py fetch` reports unavailable, continue on the structured fields
and paste the JSON into the record's `unavailable_sources` list. The renderer places it in the uncertainty section. State any resulting judgment uncertainty in the record.

## Available scripts

- `scripts/scaffold_record.py`: copy catalog conditions or checklist questions into an unfilled record, with a count receipt.
- `scripts/check_citations.py`: check artifact citation existence, line bounds and requirement-id references only.
- `scripts/load_catalog.py`: verify the packaged snapshot, fetch pinned source text, or report drift without switching catalogs.
- `scripts/validate_judgments.py`: check coverage, evidence fields and applicability decisions.
- `scripts/render_plan.py`: validate and render a plan in catalog reading order.

## Output

Use [output-format.md](references/output-format.md) and [the template](assets/plan-template.md). Every command-line script supports `--help`; stdout is JSON, including a `text` envelope for
source text or markdown when `--output -` is used. `--output FILE` writes the document
and prints a JSON destination receipt. Exit codes: 0 ok, 2 usage, 3 validation failed,
4 unavailable, 5 internal. Scripts refuse, with exit 2 and no write, an output path
that resolves to their input record or to a file inside the skill directory.

The rendered verification plan is the deliverable; the record is its evidence and stays beside it.

## Limitations

Card evidence may cite requirement ids in prose (for example, `V3: the returned integer is compared by equality`); `check_citations.py` checks that each cited id exists in `plan.requirements` and that `path:line` citations resolve, nothing about whether the evidence supports the judgment. A record with no artifact passes the citation check with zero citations; that is expected, not evidence.

The installed package carries no tests or fixtures; those and `check_skills.py` live
only in the publishing repository and are not portable. An installed copy can check
its pins with `load_catalog.py --check` and its records with the validators. Compare
its files against the tagged repository tree to establish whether it matches a release;
nothing in the package performs that comparison.

Offline means catalog-only operation: intent, conditions, determinism moves,
observable signals and the failure map remain available, but source prose does not.
Set `VERIFICATION_SKILLS_OFFLINE=1` or use `--offline` to prevent retrieval and drift
requests. Nothing is cached. An optional drift report never changes the loaded pin.
The validators check recorded judgments, not their truth or the completeness of the
underlying evidence. Substantive conclusions require operator review.

Explicit-only activation was observed on Claude Code 2.1.263, 2.1.265 and 2.1.267 in
`.claude/skills` and Codex CLI 0.153.4 in `.agents/skills` and `~/.agents/skills` on
2026-09-08 and 2026-09-10. Other hosts are untested and may model-activate this skill. SKILL.md is an ordinary readable file;
invocation controls do not prevent a model from opening it as a file.

## Closing checklist

- Artifact and scope echoed; scope came from the operator, not a guess.
- Plan present: design written or sourced, every applied pattern serves a requirement.
- Snapshot check and record validator exited 0; every required condition or question covered.
- Assumptions recorded, including verification path for design and any scope expansion.
- `models` names the verifier family and, for `generator`, the family that produced the artifact,
  `unknown` when not recorded anywhere, or `none` when no model produced it (human-written
  code or a deterministic job). Both fields use lower-case family names such as
  `anthropic-claude`, `openai-gpt` or `google-gemini`, optionally followed by a model
  after a slash, for example `anthropic-claude/opus-5`.
- `artifact_identity` and `measurements` cover what was read and run. When there is no
  artifact, omit both and record that in a `measurement-basis` assumption.
- Citation check exited 0 or its failures are explained in assumptions; record revalidated.
- Sources identify human URLs, pinned source URLs and the corpus revision.
- Unknown judgments and unavailable evidence remain visible; post-plan evidence belongs in `resolution` on undecided cards.
- Output rendered to the requested file and substantive judgments left for operator review.
