# Verification findings

Artifact: skills/fixtures/audit-requirement-conflict/artifact

Scope: Check the stated self-approval requirement against principle 2 and the receipt-writing implementation against AC2.

Corpus revision: `e632a86b2ca8fbb7f83b3130ba083784c7817667`

Corpus tag: `corpus/v1.0.0`

Skill: verification-audit 1.6.1

Skill pins: catalog `b1d737c5ea62e18fc276b8efe64d963e1326c7f93c8b2e639515ed2583ce2d3f`; principles `03033f7084e8fee60e5f7fff7249238af9f375942ad856d4cf485d22d68bf61a`; checklist `a21fcd0d80aebd1970dea6960e71c8d18da704f37b16d87c9d7c5a41ececcd80`

Generator model: openai-gpt

Verifier model: openai-gpt

## Assumptions

- artifact-stage: This is a source inspection of the complete toy workflow declaration in artifact/spec.md:1-7 and artifact/generate.py:1-4, not an executed run or a blind model evaluation. The remaining checklist behaviors were not evaluated.

## Summary

Defects: 1. high: 0; medium: 1; low: 0.

Author-assigned cause groups: 0; ungrouped defect rows: 1.

- defect: 1
- conflict: 1
- sound: 0
- not-applicable: 0
- not-checked: 17
- insufficient-evidence: 0
- out-of-scope: 0

Unmapped defects:

- Does generate.py implement the receipt file required by AC2?

## Defects

### Principle 5

Does generate.py implement the receipt file required by AC2?

Evidence: The complete script provides no mechanism to write the required receipt: artifact/generate.py:1-4 only assigns and prints the summary. artifact/spec.md:7 states "Every invocation of generate.py must write receipt.txt containing the generated summary." This is a source-level implementation failure against AC2, not a claim about an observed run.

Severity: medium

Basis: stated requirement

Failure: unmapped

Failure note: The missing required file writer is a structural acceptance-criterion failure, outside the six mapped agent behaviors.

No routed card: outside the six mapped failures; see the failure note above.

## Requirement conflicts

### Principle 2

Who evaluates the generated output, and what evidence separates that evaluator from the generator? [Principles][p2]

Evidence: artifact/spec.md:6 requires "The generating agent must be the sole approver of its own summary, using the same context; no independent evaluator is permitted." The principle 2 question asks "Who evaluates the generated output, and what evidence separates that evaluator from the generator?" The requirement demands sole self-approval; principle 2 demands an evaluator independent of the generator. These demands conflict and remain for the operator to resolve.

## Checked and sound

None.

## Not applicable

None.

## Not checked

### Principle 1

What external observation, distinct from the generator saying done, records completion? [Principles][p1]

Reason: Not checked: this script fixture checks the stated self-approval conflict and AC2 receipt-writing implementation only; this checklist behavior was not evaluated.

### Principle 1

Which expected and observed values are recorded for each completion check? [Principles][p1]

Reason: Not checked: this script fixture checks the stated self-approval conflict and AC2 receipt-writing implementation only; this checklist behavior was not evaluated.

### Principle 2

Which generator context is withheld from the verifier, and where is that boundary recorded? [Principles][p2]

Reason: Not checked: this script fixture checks the stated self-approval conflict and AC2 receipt-writing implementation only; this checklist behavior was not evaluated.

### Principle 3

Which intermediate steps emit observable signals before the final completion decision? [Principles][p3]

Reason: Not checked: this script fixture checks the stated self-approval conflict and AC2 receipt-writing implementation only; this checklist behavior was not evaluated.

### Principle 3

Where are a failed checkpoint and the resulting stop or escalation recorded? [Principles][p3]

Reason: Not checked: this script fixture checks the stated self-approval conflict and AC2 receipt-writing implementation only; this checklist behavior was not evaluated.

### Principle 4

Which checks search for a counterexample to completion, with the observed result recorded? [Principles][p4]

Reason: Not checked: this script fixture checks the stated self-approval conflict and AC2 receipt-writing implementation only; this checklist behavior was not evaluated.

### Principle 4

What evidence, recorded in the artifact, shows that a failing artifact can be rejected by the verification procedure? [Principles][p4]

Reason: Not checked: this script fixture checks the stated self-approval conflict and AC2 receipt-writing implementation only; this checklist behavior was not evaluated.

### Principle 5

Where are the expected conditions and criterion identifiers specified before evaluation? [Principles][p5]

Reason: Not checked: this script fixture checks the stated self-approval conflict and AC2 receipt-writing implementation only; this checklist behavior was not evaluated.

### Principle 5

How does the artifact record the criteria version used for each verdict? [Principles][p5]

Reason: Not checked: this script fixture checks the stated self-approval conflict and AC2 receipt-writing implementation only; this checklist behavior was not evaluated.

### Principle 6

Which claims are checked by executable assertions or comparisons, and where are their results? [Principles][p6]

Reason: Not checked: this script fixture checks the stated self-approval conflict and AC2 receipt-writing implementation only; this checklist behavior was not evaluated.

### Principle 6

Which claims still depend on judgment, and what evidence bounds those claims? [Principles][p6]

Reason: Not checked: this script fixture checks the stated self-approval conflict and AC2 receipt-writing implementation only; this checklist behavior was not evaluated.

### Principle 7

When model review is used, what generator and verifier model families are recorded? [Principles][p7]

Reason: Not checked: this script fixture checks the stated self-approval conflict and AC2 receipt-writing implementation only; this checklist behavior was not evaluated.

### Principle 7

When model review is used, what evidence supports the selected verifier model family for this artifact and scope? [Principles][p7]

Reason: Not checked: this script fixture checks the stated self-approval conflict and AC2 receipt-writing implementation only; this checklist behavior was not evaluated.

### Principle 8

When independent reviewers disagree, where are their claims and evidence recorded separately? [Principles][p8]

Reason: Not checked: this script fixture checks the stated self-approval conflict and AC2 receipt-writing implementation only; this checklist behavior was not evaluated.

### Principle 8

What explicit rule routes unresolved disagreement or stops further review? [Principles][p8]

Reason: Not checked: this script fixture checks the stated self-approval conflict and AC2 receipt-writing implementation only; this checklist behavior was not evaluated.

### Principle 9

What before-state or isolated baseline lets a check attribute its observation to this run? [Principles][p9]

Reason: Not checked: this script fixture checks the stated self-approval conflict and AC2 receipt-writing implementation only; this checklist behavior was not evaluated.

### Principle 9

Where are run identifiers, state changes and observed deltas recorded? [Principles][p9]

Reason: Not checked: this script fixture checks the stated self-approval conflict and AC2 receipt-writing implementation only; this checklist behavior was not evaluated.

## Insufficient evidence

None.

## Observed outside scope

None.

## Sources

Corpus revision: `e632a86b2ca8fbb7f83b3130ba083784c7817667`.

Principles: [verificationdesign.com][principles] ([pinned source][principles-src]).

[principles]: https://verificationdesign.com/principles/
[principles-src]: https://raw.githubusercontent.com/verificationdesign/verificationdesign/e632a86b2ca8fbb7f83b3130ba083784c7817667/verification_design.md
[p2]: https://raw.githubusercontent.com/verificationdesign/verificationdesign/e632a86b2ca8fbb7f83b3130ba083784c7817667/verification_design.md#2-independence-between-generation-and-verification
[p1]: https://raw.githubusercontent.com/verificationdesign/verificationdesign/e632a86b2ca8fbb7f83b3130ba083784c7817667/verification_design.md#1-external-signals-over-self-review
[p3]: https://raw.githubusercontent.com/verificationdesign/verificationdesign/e632a86b2ca8fbb7f83b3130ba083784c7817667/verification_design.md#3-step-level-checkpoints
[p4]: https://raw.githubusercontent.com/verificationdesign/verificationdesign/e632a86b2ca8fbb7f83b3130ba083784c7817667/verification_design.md#4-adversarial-framing
[p5]: https://raw.githubusercontent.com/verificationdesign/verificationdesign/e632a86b2ca8fbb7f83b3130ba083784c7817667/verification_design.md#5-explicit-criteria
[p6]: https://raw.githubusercontent.com/verificationdesign/verificationdesign/e632a86b2ca8fbb7f83b3130ba083784c7817667/verification_design.md#6-executable-verification-is-king
[p7]: https://raw.githubusercontent.com/verificationdesign/verificationdesign/e632a86b2ca8fbb7f83b3130ba083784c7817667/verification_design.md#7-cross-family-beats-self-verification
[p8]: https://raw.githubusercontent.com/verificationdesign/verificationdesign/e632a86b2ca8fbb7f83b3130ba083784c7817667/verification_design.md#8-simulate-debate
[p9]: https://raw.githubusercontent.com/verificationdesign/verificationdesign/e632a86b2ca8fbb7f83b3130ba083784c7817667/verification_design.md#9-isolate-verification-from-ambient-state
