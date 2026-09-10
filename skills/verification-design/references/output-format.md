# Output format

Header: artifact, scope, corpus revision and tag, then the skill name and version, its
pinned hashes, the generator and verifier model families, then optional Artifact
identity with revision, file count and files. Assumptions is the first section, then
Measurements only when present, then Summary.

Section order:

1. Assumptions
2. Measurements
3. Summary
4. Workflow characterization
5. Patterns applied
6. Patterns rejected
7. Not verified
8. Sources

Summary counts apply, reject, undecided and unknown verdicts; Operator decisions names
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
