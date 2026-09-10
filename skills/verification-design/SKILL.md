---
name: verification-design
description: Design a verification plan for work being built, using the verificationdesign.com pattern catalog at a pinned revision. Needs a scope line. Do not run without an explicit request.
license: MIT
compatibility: Python 3.11 or later, standard library only. Explicit-only invocation verified on Claude Code 2.1.263 and 2.1.265 (.claude/skills) and Codex CLI 0.153.4 (.agents/skills, ~/.agents/skills) on 2026-09-08. Other hosts untested and may model-activate this skill.
disable-model-invocation: true
metadata:
  disable-model-invocation: "true"
  version: "1.2.0"
  corpus-revision: "e632a86b2ca8fbb7f83b3130ba083784c7817667"
  corpus-tag: "corpus/v1.0.0"
  catalog-sha256: "b1d737c5ea62e18fc276b8efe64d963e1326c7f93c8b2e639515ed2583ce2d3f"
  principles-sha256: "03033f7084e8fee60e5f7fff7249238af9f375942ad856d4cf485d22d68bf61a"
---

# Verification design

## Purpose

Design a verification plan from recorded applicability judgments and a pinned catalog. Scripts check the record and render the plan; the operator reviews the judgments.

## When not to use

Do not run without an explicit request for this skill. Do not proceed without a resolved scope. For an existing artifact that needs findings, use the audit skill only if the operator requests it.

The skill reads the artifact and takes no part in the host repository's workflow, seats, or messaging; scope resolves before anything else happens.

## Inputs

- Artifact: default is the current working tree. Override: a path or URL given as the
  invocation argument or named in the conversation. Never asked for.
- Scope: one line naming the part or behavior in question. Taken from the invocation
  argument text or from the conversation if the operator already said it. If neither
  supplies it, ask exactly one question and stop until answered. Never guess scope.
- Both resolved values are echoed at the top of the output.
- If resolved scope differs from the operator's words verbatim, record a `scope-expansion` assumption quoting the original words.

## Procedure

Run commands from this skill directory, with absolute paths for operator-visible records and outputs outside it. Python 3.11 or later is required. No command prompts interactively. Records and outputs go in a dated directory the operator can see, beside the artifact or where the operator says, never in system temp storage and never inside the skill directory.

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

4. Read `assets/catalog.json` and [judgment-record.md](references/judgment-record.md).
   Fill the scaffold: characterize what is generated, by whom, the completion signal,
   and self-review points. Declare the `verification-path` assumption before judging.
   Preserve every catalog condition verbatim and in order. Record each verdict and
   its artifact evidence. Unknown exclusions block apply; keep unknowns visible.
   This is a judgment step, not an executable inference from prose.
   Fill the record-level fields as well:
   - `models`: the model family producing this record as `verifier`, and the family that
     will produce the work as `generator`, or `unknown` when it is not decided or recorded.
   - `artifact_identity`: the artifact revision and a sha256 per file read, so a reader
     can tell which bytes were judged. Omit only when nothing readable was examined.
   - `measurements`: one entry per command run against the artifact, with its exit code,
     cited by id from evidence. A measurement shows what the artifact does; it is not
     evidence that the artifact records anything.
5. Validate; correct record errors and rerun until exit 0. If the packaged dependency
   fails, stop and report it without changing the pin.

   ```bash
   python3 scripts/validate_judgments.py /absolute/path/record.json
   ```

6. Check artifact citation existence and bounds. Require exit 0 or record an explanation
   in `assumptions`, then revalidate. This check does not assess evidence meaning.
   Paste any fetch exit-4 JSON objects into the record's `unavailable_sources` list
   before final validation and rendering.

   ```bash
   python3 scripts/check_citations.py /absolute/path/record.json --root /absolute/path/artifact
   ```

7. Render the validated record:

   ```bash
   python3 scripts/render_plan.py /absolute/path/record.json --output /absolute/path/plan.md
   ```

8. Complete the closing checklist. Validation does not verify substantive judgments.

Source text is optional. If a question needs prose beyond the structured catalog,
retrieve it only through this command (replace `principles` with a catalog card id
for card text):

```bash
python3 scripts/load_catalog.py fetch principles --offline
```

Omit `--offline` only when source retrieval is wanted and network is available.
When `load_catalog.py fetch` reports unavailable, continue on the structured fields
and paste the JSON into the record's `unavailable_sources` list. The renderer places it in the uncertainty section. State any resulting judgment uncertainty in the record.

## Available scripts

- `scripts/scaffold_record.py`: copy catalog conditions or checklist questions into an unfilled record, with a count receipt.
- `scripts/check_citations.py`: check artifact citation existence and line bounds only.
- `scripts/load_catalog.py`: verify the packaged snapshot, fetch pinned source text, or report drift without switching catalogs.
- `scripts/validate_judgments.py`: check coverage, evidence fields and applicability decisions.
- `scripts/render_plan.py`: validate and render a plan in catalog reading order.

## Output

Use [output-format.md](references/output-format.md) and [the template](assets/plan-template.md). Every script supports `--help`; stdout is JSON, including a `text` envelope for
source text or markdown when `--output -` is used. `--output FILE` writes the document
and prints a JSON destination receipt. Exit codes: 0 ok, 2 usage, 3 validation failed,
4 unavailable, 5 internal. Scripts refuse, with exit 2 and no write, an output path
that resolves to their input record or to a file inside the skill directory.

The rendered plan is the deliverable. A companion document is allowed only if its top states that it is not skill output and was not validated.

## Limitations

Offline means catalog-only operation: intent, conditions, determinism moves,
observable signals and the failure map remain available, but source prose does not.
Set `VERIFICATION_SKILLS_OFFLINE=1` or use `--offline` to prevent retrieval and drift
requests. Nothing is cached. An optional drift report never changes the loaded pin.
The validators check recorded judgments, not their truth or the completeness of the
underlying evidence. Substantive conclusions require operator review.

Explicit-only activation was observed on Claude Code 2.1.263 and 2.1.265 in `.claude/skills` and
Codex CLI 0.153.4 in `.agents/skills` and `~/.agents/skills` on 2026-09-08. Other hosts
are untested and may model-activate this skill. SKILL.md is an ordinary readable file;
invocation controls do not prevent a model from opening it as a file.

## Closing checklist

- Artifact and scope echoed; scope came from the operator, not a guess.
- Snapshot check and record validator exited 0; every required condition or question covered.
- Assumptions recorded, including verification path for design and any scope expansion.
- `models` names the verifier family and the generator family or `unknown`; `artifact_identity` and `measurements` cover what was read and run.
- Citation check exited 0 or its failures are explained in assumptions; record revalidated.
- Sources identify human URLs, pinned source URLs and the corpus revision.
- Unknown judgments and unavailable evidence remain visible.
- Output rendered to the requested file and substantive judgments left for operator review.
