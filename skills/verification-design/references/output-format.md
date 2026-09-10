# Output format

Header: artifact, scope, corpus revision and tag, then the skill name and version, its
pinned hashes, the generator and verifier model families, then optional Artifact
identity with revision, file count and files. Design and Verification requirements lead;
Assumptions, optional Measurements and Summary follow.

Section order:

1. Design
2. Verification requirements
3. Assumptions
4. Measurements (when present)
5. Summary
6. Workflow characterization
7. Patterns applied
8. Patterns rejected
9. Not verified
10. Sources

Design renders `plan.design`, followed by `Source: <source>` when present.
Each requirement has a `### V1: <statement>` heading, its check paragraph, and
`Patterns: ` with reference-style card citations in requirement order, or `Patterns: none`.
Each applied entry has `Decision: apply` followed directly by `Serves: V1, V3`, listing
its requirement ids in id order.

Summary counts apply, reject, undecided and unknown verdicts, followed by `Requirements: N`; Operator decisions names
each undecided card and its unknown conditions. Recommended order appears when priority
is present. An undecided card with a resolution ends its Operator decisions bullet
with `Resolution recorded YYYY-MM-DD.` Self-review points use bullets. Instantiation
follows Determinism move.

In Not verified only, after unknown-condition bullets and before any Determinism move
or Instantiation, render `Resolution (YYYY-MM-DD): <observation> Evidence: <evidence>`
when present, appending ` Measurement: <id>` when measurement is a string. The Decision
line is unchanged.

Evidence labels apply to sound and defect entries and holding or not-holding conditions.
Reason labels apply to not-checked, not-applicable, insufficient-evidence, out-of-scope
and unknown verdicts. Do not double a final full stop. Assumptions are bullets as
`topic: statement`; each measurement bullet begins with its id and includes all fields.
Unavailable-source objects render as fenced JSON inside the uncertainty section.

Use reference-style card citations `[Title][slug] ([pinned source][slug-src])`.
Checklist Principles citations become `[Principles][pN]` without changing the record.
Sources contains each used card and principle-anchor definition once and one corpus
revision line; the header also retains its revision and tag. Output is deterministic
and byte-stable. Validation checks structure, not substantive truth.
