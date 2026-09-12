# Changelog

## skills/v1.3.0 (2026-09-12)

Pins unchanged `corpus/v1.0.0`. Source: seven observation runs on 2026-09-12 (six audits
and designs on external and local targets plus a design run on the skills themselves),
recorded under the maintainer's local skill-runs directory. Records carry the new
`kind` measurement field and the re-pinned checklist, so v1.2.0 records do not validate
unchanged.

- Every script that takes `--output FILE` creates the file's directory. The scaffold no
  longer exits 5 when the dated run directory does not exist yet.
- Routing is documented as a lookup of the failure map, never an applicability
  judgment; the renderer labels routed cards `candidate:`. New optional `related_cards`
  on defects names the cards the auditor judges applicable (rule `routing`): drawn from
  the failure's candidates on a mapped defect, any catalog card on an unmapped one,
  rendered as `judged applicable:`. A new negative fixture rejects a related card
  outside the map.
- The routed file is the finished record; the procedure writes it as
  `record.routed.json`. `render_findings.py` accepts an unrouted record and routes it on
  the way, while a record that carries routing must still match the pinned map exactly.
- Sources always names the human Principles page and its pinned source, so an audit with
  nothing routed still satisfies the closing checklist.
- The absence rule is split: a record the principle asks for is a defect when the
  artifact has no way to produce it, and `insufficient-evidence` naming the settling
  receipt when it would come from a stage outside the evidence set. The `artifact-stage`
  assumption tells the two apart.
- `measurements` entries require `kind`: `inspection` or `execution`. The renderer puts
  each command in a fenced block under its bullet, so multi-line commands stay readable.
- `check_citations.py` checks requirement-id references (`V2`) against
  `plan.requirements` when the record has a plan, reporting `requirements` and
  `unknown-requirement` counts; an unknown id fails with exit 3.
- Principle 7's second checklist question now says `When model review is used` and
  `verifier model family`, so it reads as the model-review question it is.
  `checklist-sha256` re-pinned.
- The audit record reference states severity once: high, medium or low on a defect,
  null otherwise.
- The design procedure reads the catalog and record reference before writing the plan.
- Both procedures say that scripts create the output directory.

## skills/v1.2.0 (2026-09-10)

Pins unchanged `corpus/v1.0.0`. Source: the audit skill run against its own package on
2026-09-09 (twelve defects, six reproduced by the maintainer). New required record
fields mean v1.1.0 records do not validate unchanged.

- `plan` (required, design only): design prose, optional source, and numbered
  verification requirements, each naming the applied patterns that serve it; the
  renderer leads with Design and Verification requirements and every applied pattern
  states which requirements it serves. The companion-document rule is withdrawn.
- `skill` (required): name, version and pinned hashes of the package that judged the
  record, emitted by the scaffold and checked for an exact match by the validators. The
  audit skill now pins its question checklist with `metadata.checklist-sha256`, verified
  by `load_catalog.py` beside the catalog and Principles hashes; `--check` reports all of
  them. Rendered documents carry a Skill line and a Skill pins line.
- `models` (required): generator and verifier model families, `unknown` when not
  recorded, rendered in the header. The record now answers its own Principle 7 question.
- Output collision refused: every script with `--output` exits 2 and writes nothing when
  the destination resolves to its input record, to the scaffold's artifact, or to a file
  inside the skill directory.
- Both procedures route to `models`, `artifact_identity` and `measurements` in step 4
  and in the closing checklist; before, the fields existed only in the record reference.
- The record references no longer cite repository fixture paths the package does not
  ship; the audit reference carries two inline example entries instead.

- The audit no-fix rule is an accepted procedural limit, enforced by the operator's
  read; a fix proposal is a procedure failure, not a missing validator rule.
- Package verification remains repository-only: installed copies carry no tests or
  fixtures, check pins and records only, and require a tagged-tree comparison to
  establish release identity.
- Optional per-card `resolution` preserves post-plan evidence beside an undecided
  design verdict, validates its date and measurement id, and appears in Not verified
  and the Summary without changing the original decision, shown by the new
  `design-resolved` fixture.
- Unknown and insufficient-evidence judgments explain missing evidence without filler
  citations; the citation checker reports citations repeated across three or more
  entries for operator review without changing its exit code.
- Citation checking accepts several `--root` arguments in order, uses the first file
  match, and reports the given roots and each found citation's resolving root.

Compatibility line adds Claude Code 2.1.267 (four invocation probes rerun on 2026-09-10).
Blind tests of the five fixtures passed on Claude Code 2.1.267 and Codex CLI 0.153.4 against
this release. Antigravity CLI 1.2.0 ran both skills by explicit path invocation; its
invocation controls were not probed, so it is listed as observed, not verified.

## skills/v1.1.0 (2026-09-08)

Pins unchanged `corpus/v1.0.0`. Required `assumptions` means v1.0.0 records do not
validate unchanged; design requires a verification-path entry. Optional additions:
measurements, artifact_identity, unavailable_sources, design instantiation and priority.
Audit adds not-applicable and free out-of-scope observations, with shared-cause notes.

New scaffold and citation-check scripts copy fields and check citation bounds without
judging evidence. A Python 3.11 guard rejects unsupported runtimes before work and
`--check` reports the interpreter version. Principle 4's second checklist question now
explicitly asks for evidence recorded in the artifact; old audit records must also update
that copied question. Rendering adds summaries,
assumptions, measurements, six audit sections, reference-style Sources, reason/evidence
labels and bullet self-review points. Records and outputs belong in a visible dated
directory, never system temp storage or the skill directory.

## skills/v1.0.0 (2026-09-08)

Source: corpus/v1.0.0 at `e632a86b2ca8fbb7f83b3130ba083784c7817667`.
Initial verification-design and verification-audit skills, with explicit invocation
controls, packaged catalog snapshots, record validators, deterministic renderers,
failure routing and offline fixture and retrieval checks.
