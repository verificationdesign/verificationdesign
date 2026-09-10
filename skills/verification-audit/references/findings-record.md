# Findings record

A JSON object has `corpus_revision` equal to the packaged revision, `skill` and `models`
(see Shared record fields), non-empty `artifact`, one-line non-empty `scope`,
`assumptions` (may be empty), and `checks`.
Every checklist bullet appears exactly once as its whole text (including citation,
excluding `- `) in `question`, with its integer `principle` (1 to 9).

Every entry has non-empty string `evidence`, `status`, and `severity`:

- `sound`: checked behavior with evidence; severity null.
- `defect`: in-scope artifact evidence, failure equal to a mapped failure or `unmapped`,
  severity high, medium or low. Unmapped requires non-empty `failure_note`.
- `not-applicable`: the question cannot apply to this artifact and scope, for example
  no model review or no second reviewer exists. Evidence is the reason. Severity null,
  no failure and no routing.
- `not-checked`: evidence explains why no check was performed; severity null.
- `insufficient-evidence`: evidence names what is missing and what would settle it;
  severity null.
- `out-of-scope`: `free: true`, principle 1 to 9 or null, original question, evidence
  describing an observation outside the scope. Severity null, no failure and no routing.
  This section is for things fresh eyes noticed and the scope excludes. A defect belongs
  in Defects only if it is in scope. These observations never count as defects or replace
  checklist coverage.

For `insufficient-evidence`, explain why judgment is unavailable, write `No source in the evidence set addresses this condition.` when none does, and cite only text bearing on the condition.

Additional in-scope defects use `free: true`, principle 1 to 9 and an original question.
Free entries never substitute for checklist questions. Non-defects may use null failure
and empty failure_note; not-applicable and out-of-scope require these absent or empty
and cannot carry cards or routed fields. No fix proposals anywhere.

The no-fix rule is enforced by the procedure and the operator's read, not by scripts.
A mechanical scan for fix language was considered too weak to justify a false sense
of enforcement. A fix proposal in a rendered document is a procedure failure, not
a validator gap.

`failure_note` is an optional string on mapped defects, rendered whenever non-empty.
Use it to say several defects share one cause. The six mapped failures are routing aids,
not an exhaustive taxonomy. The router computes cards and routed only for defects;
the renderer rejects incorrect routing.

Rules: `structure`, `coverage` (including free out-of-scope restrictions), `status`
(the six statuses above), `evidence`, `failure`, `severity`, `routing`, plus the shared
rules `skill`, `models`, `assumptions`, `measurements`, `artifact-identity` and
`unavailable-sources`. Errors report card (null), check index, rule and message; exit 3.
Success reports checks, defects, counts per status and defects by severity; exit 0.
An emitted scaffold fails `status`, `evidence` and `models`, never passing as a finished audit.

## Shared record fields

- `skill` (required, rule `skill`): the identity of the package that judged the record,
  emitted by `scaffold_record.py` and never edited by hand: `name`, `version`,
  `catalog_sha256`, `principles_sha256`, and for the audit skill `checklist_sha256`.
  Validation requires it to equal the installed package exactly, so a record produced
  under another version or question set fails until it is re-judged, and a rendered
  document always states which question set produced its verdicts.
- `models` (required, rule `models`): object with non-empty strings `generator` and
  `verifier`, the model families involved (Principle 7). `verifier` is the model family
  producing this record. `generator` is the family that produced, or will produce, the
  artifact. Write `unknown` when a family is not recorded anywhere; never leave it blank.
- `assumptions` (required, rule `assumptions`): list of objects with non-empty string
  `topic` and `statement`. Topics are free text. Named topics: `verification-path`
  identifies which path judgments cover when multiple verification paths exist;
  `artifact-stage` identifies spec, prototype or running; `scope-expansion` quotes
  the operator's original words when scope is restated or expanded; `measurement-basis`
  distinguishes what the agent ran from what it only read.
- `measurements` (optional, rule `measurements`): list of objects with unique non-empty
  string `id`, non-empty string `command`, string-to-string object `env` (may be empty),
  integer `exit_code` (not boolean), string `artifact_revision` (may be empty),
  `log` (string path or null), and string `note` (may be empty). Cite measurements by id.
- `artifact_identity` (optional, rule `artifact-identity`): object with `revision`
  (string or null) and `files`, a list of objects with string `path` and `sha256`. The renderer reports the revision, file count and list.
- `unavailable_sources` (optional, rule `unavailable-sources`): list of the exact
  fetch exit-4 objects: `{"unavailable": true, "source_url": "...", "reason": "offline"}`.
  Paste JSON here before validating, never into rendered output. The renderer places
  fenced JSON in the uncertainty section. Optional fields may be absent.

Defects are judged against the nine principles, not the artifact's own requirements.
The absence of a record a principle asks for is a defect; severity carries how much
it matters here. Applying a design card is a separate applicability judgment.

A measurement the agent ran is evidence of what the artifact does. It is not evidence
that the artifact records anything. Cite measurements by id and distinguish measured
behavior from records that the artifact itself preserves.

## Mechanical helpers

Run `scaffold_record.py --artifact TEXT --scope TEXT --output FILE|-` before judging.
It copies fields and judges nothing. FILE receives the record with a JSON count receipt
on stdout; `-` emits one JSON envelope containing `record` and `counts`.

Run `check_citations.py record.json --root DIR [--root DIR ...] [--output FILE|-]` after validation.
It scans evidence, reason, statement, note and instantiation strings for `path:N` or
`path:N-M` (paths must contain a dot or slash). Several roots may be given; the first
file match wins, so order them deliberately. Absolute paths are used as given. Each
citation is counted once as found, missing or out-of-bounds.
The JSON reports counts, non-found citations with their record entry, `roots` as given,
and `resolved` citations with their root (null for absolute paths), in first-seen order.
`repeated` lists citations appearing in at least three distinct record entries, sorted
by entry count descending then citation. Repeated citations are reported for the
operator's eye and are not a failure, because one line can bear on several conditions.
Exit 0 means
all found, exit 3 means some were not. This checks existence and bounds only, nothing
about meaning. It reads line counts, not artifact semantics. A failure requires repair
or an explanation in assumptions, followed by validation again.

## Example entries

The package ships no complete record; the publishing repository keeps worked fixtures
under `skills/fixtures/`, outside the installed skill. Two entries show the shape. Every
other checklist question needs an entry of the same form, and `skill` comes from the
scaffold unchanged.

```json
{
  "principle": 2,
  "question": "Who evaluates the generated output, and what evidence separates that evaluator from the generator? [Principles](<pinned principles url>#2-independence-between-generation-and-verification)",
  "status": "defect",
  "evidence": "artifact/workflow.md:12-14: the same agent that writes the summary marks it approved; no second evaluator appears anywhere in the artifact.",
  "failure": "The agent reviews itself and misses obvious problems.",
  "failure_note": "",
  "severity": "high"
}
```

```json
{
  "principle": 6,
  "question": "Which claims are checked by executable assertions or comparisons, and where are their results? [Principles](<pinned principles url>#6-executable-verification-is-king)",
  "status": "sound",
  "evidence": "artifact/generate.py:40-52 asserts the row count against the manifest; measurement m1 ran it with exit 0.",
  "failure": null,
  "failure_note": "",
  "severity": null
}
```

The `failure` string on a defect must be one of the six strings in `catalog.failures`
or `unmapped`; the `question` must be a checklist bullet verbatim, including its real
pinned citation.
