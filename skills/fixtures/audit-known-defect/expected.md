# Verification findings

Artifact: skills/fixtures/audit-known-defect/artifact

Scope: Check generator/verifier independence in the inventory summary workflow.

Corpus revision: `e632a86b2ca8fbb7f83b3130ba083784c7817667`

Corpus tag: `corpus/v1.0.0`

Skill: verification-audit 1.4.0

Skill pins: catalog `b1d737c5ea62e18fc276b8efe64d963e1326c7f93c8b2e639515ed2583ce2d3f`; principles `03033f7084e8fee60e5f7fff7249238af9f375942ad856d4cf485d22d68bf61a`; checklist `a21fcd0d80aebd1970dea6960e71c8d18da704f37b16d87c9d7c5a41ececcd80`

Generator model: unknown

Verifier model: fixture author, no model review

## Assumptions

None.

## Summary

Defects: 1. high: 1; medium: 0; low: 0.

- defect: 1
- sound: 0
- not-applicable: 1
- not-checked: 16
- insufficient-evidence: 0
- out-of-scope: 1

Unmapped defects:

None.

## Defects

### Principle 2

Who evaluates the generated output, and what evidence separates that evaluator from the generator? [Principles][p2]

Evidence: artifact/workflow.md:3-4 names the same generating agent and context for review; artifact/generate.py:5-10 reports completion from its own text without an independent source.

Severity: high

Failure: The agent reviews itself and misses obvious problems.

Failure note: The same self-review cause can affect multiple findings; this fixture records one defect.

Candidate cards from the failure map (a lookup, not an applicability judgment):

- judged applicable: [Blind Oracle][blind-oracle] ([pinned source][blind-oracle-src])
- candidate: [Cross-Family][cross-family] ([pinned source][cross-family-src])
- candidate: [Adversary][adversary] ([pinned source][adversary-src])
- candidate: [Admissibility Gate][admissibility-gate] ([pinned source][admissibility-gate-src])

## Checked and sound

None.

## Not applicable

### Principle 8

When independent reviewers disagree, where are their claims and evidence recorded separately? [Principles][p8]

Reason: artifact/workflow.md:3-4 names one generating agent reviewing its own output; no independent reviewers exist to disagree.

## Not checked

### Principle 1

What external observation, distinct from the generator saying done, records completion? [Principles][p1]

Reason: Not checked: this fixture isolates generator/verifier independence; no other check was performed.

### Principle 1

Which expected and observed values are recorded for each completion check? [Principles][p1]

Reason: Not checked: this fixture isolates generator/verifier independence; no other check was performed.

### Principle 2

Which generator context is withheld from the verifier, and where is that boundary recorded? [Principles][p2]

Reason: Not checked: this fixture isolates generator/verifier independence; no other check was performed.

### Principle 3

Which intermediate steps emit observable signals before the final completion decision? [Principles][p3]

Reason: Not checked: this fixture isolates generator/verifier independence; no other check was performed.

### Principle 3

Where are a failed checkpoint and the resulting stop or escalation recorded? [Principles][p3]

Reason: Not checked: this fixture isolates generator/verifier independence; no other check was performed.

### Principle 4

Which checks search for a counterexample to completion, with the observed result recorded? [Principles][p4]

Reason: Not checked: this fixture isolates generator/verifier independence; no other check was performed.

### Principle 4

What evidence, recorded in the artifact, shows that a failing artifact can be rejected by the verification procedure? [Principles][p4]

Reason: Not checked: this fixture isolates generator/verifier independence; no other check was performed.

### Principle 5

Where are the expected conditions and criterion identifiers specified before evaluation? [Principles][p5]

Reason: Not checked: this fixture isolates generator/verifier independence; no other check was performed.

### Principle 5

How does the artifact record the criteria version used for each verdict? [Principles][p5]

Reason: Not checked: this fixture isolates generator/verifier independence; no other check was performed.

### Principle 6

Which claims are checked by executable assertions or comparisons, and where are their results? [Principles][p6]

Reason: Not checked: this fixture isolates generator/verifier independence; no other check was performed.

### Principle 6

Which claims still depend on judgment, and what evidence bounds those claims? [Principles][p6]

Reason: Not checked: this fixture isolates generator/verifier independence; no other check was performed.

### Principle 7

When model review is used, what generator and verifier model families are recorded? [Principles][p7]

Reason: Not checked: this fixture isolates generator/verifier independence; no other check was performed.

### Principle 7

When model review is used, what evidence supports the selected verifier model family for this artifact and scope? [Principles][p7]

Reason: Not checked: this fixture isolates generator/verifier independence; no other check was performed.

### Principle 8

What explicit rule routes unresolved disagreement or stops further review? [Principles][p8]

Reason: Not checked: this fixture isolates generator/verifier independence; no other check was performed.

### Principle 9

What before-state or isolated baseline lets a check attribute its observation to this run? [Principles][p9]

Reason: Not checked: this fixture isolates generator/verifier independence; no other check was performed.

### Principle 9

Where are run identifiers, state changes and observed deltas recorded? [Principles][p9]

Reason: Not checked: this fixture isolates generator/verifier independence; no other check was performed.

## Insufficient evidence

None.

## Observed outside scope

### Observation

Does the workflow define a retention period?

Reason: artifact/workflow.md:1-4 describes review ownership but no retention period; retention is outside the independence scope.

## Sources

Corpus revision: `e632a86b2ca8fbb7f83b3130ba083784c7817667`.

Principles: [verificationdesign.com][principles] ([pinned source][principles-src]).

[principles]: https://verificationdesign.com/principles/
[principles-src]: https://raw.githubusercontent.com/verificationdesign/verificationdesign/e632a86b2ca8fbb7f83b3130ba083784c7817667/verification_design.md
[p2]: https://raw.githubusercontent.com/verificationdesign/verificationdesign/e632a86b2ca8fbb7f83b3130ba083784c7817667/verification_design.md#2-independence-between-generation-and-verification
[blind-oracle]: https://verificationdesign.com/patterns/verification/blind-oracle/
[blind-oracle-src]: https://raw.githubusercontent.com/verificationdesign/verificationdesign/e632a86b2ca8fbb7f83b3130ba083784c7817667/ai-design-patterns/cards/blind-oracle.md
[cross-family]: https://verificationdesign.com/patterns/orchestration/cross-family/
[cross-family-src]: https://raw.githubusercontent.com/verificationdesign/verificationdesign/e632a86b2ca8fbb7f83b3130ba083784c7817667/ai-design-patterns/cards/cross-family.md
[adversary]: https://verificationdesign.com/patterns/orchestration/adversary/
[adversary-src]: https://raw.githubusercontent.com/verificationdesign/verificationdesign/e632a86b2ca8fbb7f83b3130ba083784c7817667/ai-design-patterns/cards/adversary.md
[admissibility-gate]: https://verificationdesign.com/patterns/verification/admissibility-gate/
[admissibility-gate-src]: https://raw.githubusercontent.com/verificationdesign/verificationdesign/e632a86b2ca8fbb7f83b3130ba083784c7817667/ai-design-patterns/cards/admissibility-gate.md
[p8]: https://raw.githubusercontent.com/verificationdesign/verificationdesign/e632a86b2ca8fbb7f83b3130ba083784c7817667/verification_design.md#8-simulate-debate
[p1]: https://raw.githubusercontent.com/verificationdesign/verificationdesign/e632a86b2ca8fbb7f83b3130ba083784c7817667/verification_design.md#1-external-signals-over-self-review
[p3]: https://raw.githubusercontent.com/verificationdesign/verificationdesign/e632a86b2ca8fbb7f83b3130ba083784c7817667/verification_design.md#3-step-level-checkpoints
[p4]: https://raw.githubusercontent.com/verificationdesign/verificationdesign/e632a86b2ca8fbb7f83b3130ba083784c7817667/verification_design.md#4-adversarial-framing
[p5]: https://raw.githubusercontent.com/verificationdesign/verificationdesign/e632a86b2ca8fbb7f83b3130ba083784c7817667/verification_design.md#5-explicit-criteria
[p6]: https://raw.githubusercontent.com/verificationdesign/verificationdesign/e632a86b2ca8fbb7f83b3130ba083784c7817667/verification_design.md#6-executable-verification-is-king
[p7]: https://raw.githubusercontent.com/verificationdesign/verificationdesign/e632a86b2ca8fbb7f83b3130ba083784c7817667/verification_design.md#7-cross-family-beats-self-verification
[p9]: https://raw.githubusercontent.com/verificationdesign/verificationdesign/e632a86b2ca8fbb7f83b3130ba083784c7817667/verification_design.md#9-isolate-verification-from-ambient-state
