---
name: verification-audit
description: Audit an existing artifact against the nine verification principles and route each defect to catalog cards. Needs a scope line. Do not run without an explicit request.
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
  checklist-sha256: "a21fcd0d80aebd1970dea6960e71c8d18da704f37b16d87c9d7c5a41ececcd80"
---

# Verification audit

## Purpose

Audit an existing artifact using nine principles and route recorded defects through a pinned catalog. Scripts validate coverage, evidence fields and routing; the operator assesses substance.

## When not to use

Do not run without an explicit request for this skill. Do not proceed without a resolved scope. This skill reports findings and never proposes fixes. Planning new work belongs to a separately requested design skill.

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

Run commands from this skill directory, with absolute paths for operator-visible records and outputs outside it. Python 3.11 or later is required. No command prompts interactively. Records and outputs go in a dated directory the operator can see, beside the artifact or where the operator says, never in system temp storage and never inside the skill directory. Scripts create that directory when it does not exist.

1. Resolve artifact and scope by the rules above. No script runs until scope is resolved.
2. Verify the packaged dependency and show the interpreter version from `--check`:

   ```bash
   python3 scripts/load_catalog.py --check
   ```

3. Scaffold `record.draft.json` at an operator-visible path. The scaffold carries the `skill`
   identity (name, version and the pinned hashes) so the record states which question
   set judged it; do not edit that object.

   ```bash
   python3 scripts/scaffold_record.py --artifact "resolved artifact" --scope "resolved scope" --output /absolute/path/record.draft.json
   ```

4. Read `assets/catalog.json`, [principles-checklist.md](references/principles-checklist.md)
   and [findings-record.md](references/findings-record.md).

   Retrieve source text only through this command when prose beyond the structured catalog is needed:

   ```bash
   python3 scripts/load_catalog.py fetch principles --offline
   ```

   Fill every scaffold question in `record.draft.json`
   against the artifact, with evidence for sound and defect judgments and reasons for
   the other statuses. An unmapped defect needs a non-empty `failure_note`.
   Free defects use original questions. Record uncertainty rather
   than inventing a defect; scripts do not make these judgments. A record the principle
   asks for is a defect when the artifact has no way to produce it; when it would come
   from a stage outside the evidence set (a run, a CI report), record
   `insufficient-evidence` and name the evidence that would settle it, inspecting
   accessible in-scope source before recording that status.
   Use `not-applicable` with a reason when a question cannot apply to the artifact and scope.
   Use `out-of-scope` free observations for things fresh eyes noticed that the scope excludes, never as defects.
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
5. Validate; correct record errors and rerun until exit 0. If the packaged dependency
   fails, stop and report it without changing the pin.

   ```bash
   python3 scripts/validate_findings.py /absolute/path/record.draft.json
   ```

6. Check artifact citation existence and bounds. Require exit 0 or record an explanation
   in `assumptions`, then revalidate. This check does not assess evidence meaning.
   A root is required whenever the record cites files; roots are directories.
   Several roots may be given; first file match wins, so order them deliberately.
   Paste any exit-4 JSON objects from the fetch command in step 4 into the record's
   `unavailable_sources` list before final validation and rendering.

   ```bash
   python3 scripts/check_citations.py /absolute/path/record.draft.json --root /absolute/path/artifact-dir --root /absolute/path/evidence
   ```

7. Route validated defects through the packaged failure map. Routing is a lookup: it
   attaches every card the map lists for the failure string as a candidate and makes no
   applicability judgment. Before routing, name in `related_cards` the candidates you
   judge applicable, or any card for an unmapped defect. The routed `record.json` is the finished
   record from here on; cite it, not `record.draft.json`.

   ```bash
   python3 scripts/route_failures.py /absolute/path/record.draft.json --output /absolute/path/record.json
   ```

8. Render the findings from the routed record (an unrouted record is routed on the way):

   ```bash
   python3 scripts/render_findings.py /absolute/path/record.json --output /absolute/path/findings.md
   ```

9. Complete the closing checklist. No fix proposals anywhere in the output.

Source text is optional; step 4 supplies the fetch command. Replace `principles`
with a catalog card id for card text.

Omit `--offline` only when source retrieval is wanted and network is available.
When `load_catalog.py fetch` reports unavailable, continue on the structured fields
and paste the JSON into the record's `unavailable_sources` list. The renderer places it in the uncertainty section. State any resulting judgment uncertainty in the record.

## Available scripts

- `scripts/scaffold_record.py`: copy catalog conditions or checklist questions into an unfilled record, with a count receipt.
- `scripts/check_citations.py`: check artifact citation existence and line bounds only.
- `scripts/load_catalog.py`: verify the packaged snapshot, fetch pinned source text, or report drift without switching catalogs.
- `scripts/validate_findings.py`: check checklist coverage, evidence and defect fields.
- `scripts/route_failures.py`: attach the failure map's candidate cards to recorded defects; a lookup, not a judgment.
- `scripts/render_findings.py`: validate routing and render six findings sections.

## Output

Use [output-format.md](references/output-format.md) and [the template](assets/findings-template.md). Every command-line script supports `--help`; stdout is JSON, including a `text` envelope for
source text or markdown when `--output -` is used. `--output FILE` writes the document
and prints a JSON destination receipt. Exit codes: 0 ok, 2 usage, 3 validation failed,
4 unavailable, 5 internal. Scripts refuse, with exit 2 and no write, an output path
that resolves to their input record or to a file inside the skill directory.

## Limitations

The installed package carries no tests or fixtures; those and `check_skills.py` live
only in the publishing repository and are not portable. An installed copy can check
its pins with `load_catalog.py --check` and its records with the validators. Compare
its files against the tagged repository tree to establish whether it matches a release;
nothing in the package performs that comparison.

The no-fix rule is enforced by the procedure and the operator's read, not by scripts.
A mechanical scan for fix language was considered too weak to justify a false sense
of enforcement. A fix proposal in a rendered document is a procedure failure, not
a validator gap.

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
- The routed `record.json` is the file cited as the record; `related_cards` names judged cards where routing offered candidates,
  or is absent when no card applies. An unmapped defect with a `failure_note` is a complete answer.
- Sources identify human URLs, pinned source URLs and the corpus revision.
- Every `insufficient-evidence` entry names the missing evidence and explains why inspected sources do not settle the question.
- Unknown judgments and unavailable evidence remain visible.
- Output rendered to the requested file and substantive judgments left for operator review.
- Defects, Checked and sound, Not applicable, Not checked, Insufficient evidence, and Observed outside scope sections present; no fix proposals.
