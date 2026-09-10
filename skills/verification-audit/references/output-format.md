# Output format

Header: artifact, scope, corpus revision and tag, then the skill name and version, its
pinned hashes, the generator and verifier model families, then optional Artifact
identity with revision, file count and files. Assumptions is the first section, then
Measurements only when present, then Summary.

Section order:

1. Assumptions
2. Measurements
3. Summary
4. Defects
5. Checked and sound
6. Not applicable
7. Not checked
8. Insufficient evidence
9. Observed outside scope
10. Sources

Summary counts defects by severity and every status, and names unmapped defects.
All six findings sections are always present; empty sections say `None.`.
Mapped failure notes render when non-empty, including shared-cause notes.
Unmapped defects say: No routed card: outside the six mapped failures; see the failure note above.

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
