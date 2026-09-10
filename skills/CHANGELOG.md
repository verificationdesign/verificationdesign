# Changelog

## skills/v1.2.0 (unreleased)

Pins unchanged `corpus/v1.0.0`. Source: the audit skill run against its own package on
2026-09-09 (twelve defects, six reproduced by the maintainer). Two new required record
fields mean v1.1.0 records do not validate unchanged.

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

Compatibility line unchanged pending host reruns; the hosts named were tested on v1.1.0.

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
