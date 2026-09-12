# Judgment record

A JSON object has non-empty `corpus_revision` (the packaged revision), `skill` and
`models` (see Shared record fields), `artifact`, one-line `scope`, `workflow`,
`assumptions`, `plan`, and `cards`.
`workflow` has non-empty strings `generated`, `generator`, `completion_signal`, and
`self_review_points`, a list of non-empty strings (may be empty).

`plan` (required, rule `plan`) is an object with non-empty string `design` (two to
eight sentences describing the components and workflow), optional non-empty string
`source` (an existing design document path or path:lines), and a non-empty `requirements`
list, with no other keys. Omit `source` when the design is written from the scope and
conversation; record that origin in a `design-source` assumption.

Each requirement has exactly `id`, `statement`, `check` and `patterns`: ids are `V1`,
`V2`, and so on, contiguous in list order; statement and check are non-empty strings.
The check names what will run, what it reads, and pass and fail outcomes. `patterns`
is a list of applied card ids without duplicates; it may be empty for a check motivated
by the design alone. Every applied card must serve at least one requirement. Rejected
and undecided cards cannot appear in this list. Example requirement:

```json
{"id": "V1", "statement": "The returned integer equals the expected integer.", "check": "Run the regression assertions on the function return and expected values; equality passes, any mismatch fails.", "patterns": ["verification/comparator"]}
```

Each catalog card appears exactly once by `id`. Its `use_when` and `do_not_use_when`
lists copy every condition verbatim in catalog order, in objects with `condition`,
`verdict` (`holds`, `does-not-hold`, `unknown`) and string `evidence`.
Judge each condition against the card's intent; when the literal wording would decide
differently, say so in the evidence. Non-unknown verdicts require non-empty evidence. Every card has a non-empty `reason`.
For `unknown`, evidence is the reason the condition could not be judged. When no source
bears on it, write `No source in the evidence set addresses this condition.` Do not cite
an unrelated passage; a citation on an unknown verdict must bear on the condition.

- `apply`: at least one use_when holds and every exclusion does-not-hold.
- `reject`: any exclusion holds, or every use_when does-not-hold with none unknown.
- `undecided`: all other cases. Unknown exclusions block apply.

Rules: `structure`, `coverage`, `conditions`, `verdicts`, `decision-apply`,
`decision-reject`, `decision-undecided`, plus the shared rules `skill`, `models`,
`assumptions`, `measurements`, `artifact-identity`, `unavailable-sources`, `priority`
and `instantiation`, plus `resolution` and `plan`. Errors name card, rule and message; exit 3.
Success reports cards, apply, reject, undecided and unknown verdict counts; exit 0.

Design requires at least one `verification-path` assumption (rule `assumptions`).
Per-card optional string `instantiation` describes this artifact's observable signal
and determinism move (rule `instantiation`), rendered after Determinism move.
Optional record-level `priority` is an ordered list of applied card ids, each at most
once (rule `priority`); the Summary renders it as Recommended order.
An emitted scaffold fails `assumptions`, `structure`, `models` and `plan`: its verification-path
statement, workflow, model families, card reasons and design are unfilled, and its
requirements list is empty. Fill verdicts and
decisions too before validation.

Per-card optional `resolution` (rule `resolution`) is allowed only when `decision` is
`undecided`. It is an object with exactly `date` (valid calendar date `YYYY-MM-DD`),
`observation` (non-empty string describing what the build or run showed), `evidence`
(non-empty string locating that observation, with `path:N` citations), and `measurement`
(string matching an id in `measurements`, or null). Wrong keys or types, invalid dates,
non-undecided cards and unknown measurement ids fail that rule. The scaffold omits it.
The plan records what was judgeable at spec stage; a resolution records what a later
build showed beside the original verdict, so the reader sees both without rewriting
the plan. Resolution never changes verdicts, decisions or the decision rule.

## Shared record fields

- `skill` (required, rule `skill`): the identity of the package that judged the record,
  emitted by `scaffold_record.py` and never edited by hand: `name`, `version`,
  `catalog_sha256`, `principles_sha256`, and for the audit skill `checklist_sha256`.
  Validation requires it to equal the installed package exactly, so a record produced
  under another version or question set fails until it is re-judged, and a rendered
  document always states which question set produced its verdicts.
- `models` (required, rule `models`): object with non-empty strings `generator` and
  `verifier`, the model families involved (Principle 7). `verifier` is the model family
  producing this record. `generator` is the family that produced the artifact: `unknown`
  when not recorded anywhere, `none` when no model produced it (human-written code or a
  deterministic job). Both fields use a lower-case family name, such as
  `anthropic-claude`, `openai-gpt` or `google-gemini`, with an optional model after a
  slash, for example `anthropic-claude/opus-5`. Values remain free strings; never leave them blank.
- `assumptions` (required, rule `assumptions`): list of objects with non-empty string
  `topic` and `statement`. Topics are free text. Named topics: `verification-path`
  identifies which path judgments cover when multiple verification paths exist;
  `artifact-stage` identifies spec, prototype or running; `scope-expansion` quotes
  the operator's original words when scope is restated or expanded; `measurement-basis`
  distinguishes what the agent ran from what it only read; `principle-mapping` states
  how generator and verifier roles map onto an artifact that is itself a verifier or
  has no model in it.
- `measurements` (optional, rule `measurements`): list of objects with unique non-empty
  string `id`, non-empty string `command`, `kind` (`inspection` when the command only
  read the artifact or its metadata, `execution` when it ran the artifact), string-to-string
  object `env` (may be empty), integer `exit_code` (not boolean), string `artifact_revision`
  (may be empty), `log` (string path or null), and string `note` (may be empty). Cite
  measurements by id. An inspection shows what the artifact contains; only an execution
  shows what it does. Use one entry per command, or per group of same-kind commands
  with one purpose; a grouped entry states in `note` how many commands it covers.
- `artifact_identity` (optional, rule `artifact-identity`): object with `revision`
  (string or null) and `files`, a list of objects with string `path` and `sha256`. The renderer reports the revision, file count and list.
- `unavailable_sources` (optional, rule `unavailable-sources`): list of the exact
  fetch exit-4 objects: `{"unavailable": true, "source_url": "...", "reason": "offline"}`.
  Paste JSON here before validating, never into rendered output. The renderer places
  fenced JSON under `### Unavailable sources`. Optional fields may be absent.

Defects are judged against the nine principles, not the artifact's own requirements.
The absence of a record a principle asks for is a defect when the artifact provides no
way to produce that record. When the record would come from a stage that is not in the
evidence set (a test run, a CI report, a deployment), the status is
`insufficient-evidence`, naming the receipt that would settle it; the `artifact-stage`
assumption states which stage was examined so a reader can tell the two apart.
Severity carries how much a defect matters here. Applying a design card is a separate
applicability judgment.

An execution measurement is evidence of what the artifact does; an inspection
measurement is evidence of what the artifact contains. Neither is evidence that the
artifact records anything. Cite measurements by id and distinguish measurements from
records that the artifact itself preserves.

## Mechanical helpers

Run `scaffold_record.py --artifact TEXT --scope TEXT --output FILE|-` before judging.
It copies fields and judges nothing. Every script that takes `--output FILE` creates
the file's directory when it does not exist yet. FILE receives the record with a JSON count receipt
on stdout; `-` emits one JSON envelope containing `record` and `counts`.

Run `check_citations.py record.json [--root DIR ...] [--output FILE|-]` after validation.
It scans evidence, reason, statement, note and instantiation strings for `path:N` or
`path:N-M` (paths must contain a dot or slash). Every cited line range carries its path;
a bare range after a comma is prose and is not checked. When the record has a plan, it also checks
that every requirement id mentioned in those strings (`V2`, `V3`) exists in
`plan.requirements`; an unknown id is a failure with status `unknown-requirement`. A root is required whenever the record cites files.
Several roots may be given; the first
file match wins, so order them deliberately. Absolute paths are used as given. Each
citation is counted once as found, missing or out-of-bounds.
The JSON reports counts (found, missing, out-of-bounds, requirements, unknown-requirement),
non-found citations with their record entry, `roots` as given,
and `resolved` citations with their root (null for absolute paths), in first-seen order.
`repeated` lists citations appearing in at least three distinct record entries, sorted
by entry count descending then citation. Repeated citations are reported for the
operator's eye and are not a failure, because one line can bear on several conditions.
Exit 0 means
all found, exit 3 means some were not. This checks existence and bounds only, nothing
about meaning. It reads line counts, not artifact semantics. A failure requires repair
or an explanation in assumptions, followed by validation again.

## Partial example

Three selected cards below illustrate different evidence for individual conditions;
this excerpt is not a complete valid record. The package ships no complete record; the
publishing repository keeps worked fixtures under `skills/fixtures/`, outside the
installed skill. Preserve all conditions in actual records.

```json
{
  "cards": [
    {
      "id": "context-and-state/constitution",
      "use_when": [
        {
          "condition": "multiple agents or tools evaluate the same artifact",
          "verdict": "does-not-hold",
          "evidence": "artifact/workflow.md:3 describes the generated value and its caller."
        }
      ],
      "do_not_use_when": [
        {
          "condition": "the workflow is exploratory and no criteria are known yet",
          "verdict": "does-not-hold",
          "evidence": "artifact/check.py:1-4 shows the executable boundary for this condition."
        }
      ],
      "decision": "reject",
      "reason": "The small local harness has one executable check, no audit report consumer, no drifting prompt criteria and no comparison of failures across runs."
    },
    {
      "id": "context-and-state/guardrail-decorator",
      "use_when": [
        {
          "condition": "the framework supports lifecycle hooks at model, tool, retriever, or output boundaries",
          "verdict": "does-not-hold",
          "evidence": "artifact/workflow.md:3 describes the generated value and its caller."
        }
      ],
      "do_not_use_when": [
        {
          "condition": "the policy is genuinely subjective and a Judge Harness is the right verifier",
          "verdict": "does-not-hold",
          "evidence": "artifact/check.py:1-4 shows the executable boundary for this condition."
        }
      ],
      "decision": "reject",
      "reason": "No lifecycle hooks, policy enforcement or model tool boundary exists; the function receives ordinary local integers."
    },
    {
      "id": "context-and-state/causal-tag",
      "use_when": [
        {
          "condition": "the agent emits events into shared logs, traces, message buses, APIs, or side-effect targets",
          "verdict": "does-not-hold",
          "evidence": "artifact/workflow.md:3 describes the generated value and its caller."
        }
      ],
      "do_not_use_when": [
        {
          "condition": "the event surface is fully private to the test or run",
          "verdict": "holds",
          "evidence": "artifact/check.py:1-4 shows the executable boundary for this condition."
        }
      ],
      "decision": "reject",
      "reason": "No shared event surface or asynchronous work exists; each result is a private function return."
    }
  ]
}
```
