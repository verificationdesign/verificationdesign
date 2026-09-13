# Changelog

## skills/v1.5.0 (2026-09-13)

Pins unchanged `corpus/v1.0.0`. Source: the two 2026-09-12 v1.4.0 like-for-like
observation batches (Codex and Claude Code) and their cross-family reviews, recorded
in the maintainer's local skills backlog. v1.4.0 records validate after changing only
`skill.version` to 1.5.0; cause grouping is optional and adds no required field.

- Inspect accessible in-scope source before declaring evidence unavailable; every
  insufficient-evidence entry explains what is missing and why inspected source does
  not settle the question. Readable source does not force a verdict.
- Five artifact examples distinguish defects from insufficient evidence about
  records the principles ask for, without proposing fixes.
- Both procedures place the optional source fetch command in step 4 and refer
  back to it when recording unavailable-source JSON.
- The audit procedure scaffolds and fills `record.draft.json`, routes it into
  the finished `record.json`, and renders from that record.
- Optional audit `cause_groups` objects carry a cause description and at least two
  defect check indices. Validation checks structure and warns on byte-identical defect
  evidence without inferring a cause. The Summary reports author-assigned groups and
  ungrouped defect rows separately; every checklist answer retains its own judgment.
- Citation paths accept parentheses, including `(custom)/file.md:3`.
- Citation checking scans requirement `check` and workflow `self_review_points`
  strings, including their requirement-id references.
- Audit free observations retain record order within their principle; checklist
  rows retain checklist order. Plan summaries count applied cards with unknown conditions.
- Resolution notices follow exactly one period after the condition text.

All five expected renders were regenerated. `audit-known-defect/expected.md` and
`audit-missing-evidence/expected.md` change for the skill version and P5 summary;
S3 preserves their existing row order. `design-sound/expected.md` and
`design-applicability-violation/expected.md` change for the skill version and S3 summary.
`design-resolved/expected.md` changes for the skill version, S3 summary and S4 separator.

## skills/v1.4.0 (2026-09-12)

Pins unchanged `corpus/v1.0.0`. Source: the 2026-09-12 Claude Code observation batch,
recorded in the maintainer's local skill-runs summary. Record fields are unchanged,
but v1.3.0 records do not validate unchanged: updating `skill.version` to 1.4.0 is
the only change needed.

- Offline fetch exit 4 writes only the unavailable JSON object to stdout, with no
  reason line on stderr.
- Unavailable-source JSON renders under `### Unavailable sources`.
- Citation checking permits omitted roots when there are no file citations and
  returns usage exit 2 when file citations need a root.
- The audit reference states the `failure_note` rule once, and the procedure names
  the requirement for unmapped defects.
- The absence rule distinguishes document omissions from values only a run can show;
  `artifact-stage` records the reading applied.
- The `principle-mapping` assumption explains generator and verifier roles for
  artifacts that are verifiers or have no model.
- Model provenance distinguishes `unknown` from `none` and uses lower-case family
  names with optional slash-separated model names; fields remain free strings.
- Measurements may group same-kind commands by purpose with a command count in
  `note`. Artifact-free records omit identity and measurements and state that basis.
- The audit closing checklist permits absent `related_cards` when no card applies;
  an unmapped defect with a failure note is complete.
- Every cited line range carries its path; bare comma-separated ranges are prose.
- Citation examples use directory roots and name the offline fetch command that
  emits unavailable-source objects.
- Artifact-free design evidence quotes the author's design and declares that
  condition in `design-source`; card intent governs condition judgments.
- Output references name the renderer's Unavailable sources heading.

Blind tests of the five fixtures passed on Claude Code 2.1.270 and Codex CLI 0.153.4 against
this release on 2026-09-13, with a second phase for design-resolved supplying the later
build so the resolution requirement was exercised; the maintainer adjudicated each output
against the fixture's required result. Invocation-control probes were not rerun on Claude
Code 2.1.270, so the compatibility line is unchanged. v1.3.0 was tagged without a blind
fixture rerun; the v1.4.0 blind results were run against v1.4.0 only and do not establish
v1.3.0 behavior.

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
