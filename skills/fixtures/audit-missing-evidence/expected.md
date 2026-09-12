# Verification findings

Artifact: skills/fixtures/audit-missing-evidence/artifact

Scope: Audit the deployed nightly inventory summarizer and its verification behavior.

Corpus revision: `e632a86b2ca8fbb7f83b3130ba083784c7817667`

Corpus tag: `corpus/v1.0.0`

Skill: verification-audit 1.4.0

Skill pins: catalog `b1d737c5ea62e18fc276b8efe64d963e1326c7f93c8b2e639515ed2583ce2d3f`; principles `03033f7084e8fee60e5f7fff7249238af9f375942ad856d4cf485d22d68bf61a`; checklist `a21fcd0d80aebd1970dea6960e71c8d18da704f37b16d87c9d7c5a41ececcd80`

Generator model: unknown

Verifier model: fixture author, no model review

## Assumptions

None.

## Summary

Defects: 0. high: 0; medium: 0; low: 0.

- defect: 0
- sound: 0
- not-applicable: 0
- not-checked: 0
- insufficient-evidence: 18
- out-of-scope: 0

Unmapped defects:

None.

## Defects

None.

## Checked and sound

None.

## Not applicable

None.

## Not checked

None.

## Insufficient evidence

### Principle 1

What external observation, distinct from the generator saying done, records completion? [Principles][p1]

Reason: artifact/workflow.md:3-5 describes deployed behavior but supplies no run evidence. A deployed run trace, the checker implementation and its expected/observed results would settle this question.

### Principle 1

Which expected and observed values are recorded for each completion check? [Principles][p1]

Reason: artifact/workflow.md:3-5 describes deployed behavior but supplies no run evidence. A deployed run trace, the checker implementation and its expected/observed results would settle this question.

### Principle 2

Who evaluates the generated output, and what evidence separates that evaluator from the generator? [Principles][p2]

Reason: artifact/workflow.md:3-5 describes deployed behavior but supplies no run evidence. A deployed run trace, the checker implementation and its expected/observed results would settle this question.

### Principle 2

Which generator context is withheld from the verifier, and where is that boundary recorded? [Principles][p2]

Reason: artifact/workflow.md:3-5 describes deployed behavior but supplies no run evidence. A deployed run trace, the checker implementation and its expected/observed results would settle this question.

### Principle 3

Which intermediate steps emit observable signals before the final completion decision? [Principles][p3]

Reason: artifact/workflow.md:3-5 describes deployed behavior but supplies no run evidence. A deployed run trace, the checker implementation and its expected/observed results would settle this question.

### Principle 3

Where are a failed checkpoint and the resulting stop or escalation recorded? [Principles][p3]

Reason: artifact/workflow.md:3-5 describes deployed behavior but supplies no run evidence. A deployed run trace, the checker implementation and its expected/observed results would settle this question.

### Principle 4

Which checks search for a counterexample to completion, with the observed result recorded? [Principles][p4]

Reason: artifact/workflow.md:3-5 describes deployed behavior but supplies no run evidence. A deployed run trace, the checker implementation and its expected/observed results would settle this question.

### Principle 4

What evidence, recorded in the artifact, shows that a failing artifact can be rejected by the verification procedure? [Principles][p4]

Reason: artifact/workflow.md:3-5 describes deployed behavior but supplies no run evidence. A deployed run trace, the checker implementation and its expected/observed results would settle this question.

### Principle 5

Where are the expected conditions and criterion identifiers specified before evaluation? [Principles][p5]

Reason: artifact/workflow.md:3-5 describes deployed behavior but supplies no run evidence. A deployed run trace, the checker implementation and its expected/observed results would settle this question.

### Principle 5

How does the artifact record the criteria version used for each verdict? [Principles][p5]

Reason: artifact/workflow.md:3-5 describes deployed behavior but supplies no run evidence. A deployed run trace, the checker implementation and its expected/observed results would settle this question.

### Principle 6

Which claims are checked by executable assertions or comparisons, and where are their results? [Principles][p6]

Reason: artifact/workflow.md:3-5 describes deployed behavior but supplies no run evidence. A deployed run trace, the checker implementation and its expected/observed results would settle this question.

### Principle 6

Which claims still depend on judgment, and what evidence bounds those claims? [Principles][p6]

Reason: artifact/workflow.md:3-5 describes deployed behavior but supplies no run evidence. A deployed run trace, the checker implementation and its expected/observed results would settle this question.

### Principle 7

When model review is used, what generator and verifier model families are recorded? [Principles][p7]

Reason: artifact/workflow.md:3-5 describes deployed behavior but supplies no run evidence. A deployed run trace, the checker implementation and its expected/observed results would settle this question.

### Principle 7

When model review is used, what evidence supports the selected verifier model family for this artifact and scope? [Principles][p7]

Reason: artifact/workflow.md:3-5 describes deployed behavior but supplies no run evidence. A deployed run trace, the checker implementation and its expected/observed results would settle this question.

### Principle 8

When independent reviewers disagree, where are their claims and evidence recorded separately? [Principles][p8]

Reason: artifact/workflow.md:3-5 describes deployed behavior but supplies no run evidence. A deployed run trace, the checker implementation and its expected/observed results would settle this question.

### Principle 8

What explicit rule routes unresolved disagreement or stops further review? [Principles][p8]

Reason: artifact/workflow.md:3-5 describes deployed behavior but supplies no run evidence. A deployed run trace, the checker implementation and its expected/observed results would settle this question.

### Principle 9

What before-state or isolated baseline lets a check attribute its observation to this run? [Principles][p9]

Reason: artifact/workflow.md:3-5 describes deployed behavior but supplies no run evidence. A deployed run trace, the checker implementation and its expected/observed results would settle this question.

### Principle 9

Where are run identifiers, state changes and observed deltas recorded? [Principles][p9]

Reason: artifact/workflow.md:3-5 describes deployed behavior but supplies no run evidence. A deployed run trace, the checker implementation and its expected/observed results would settle this question.

## Observed outside scope

None.

## Sources

Corpus revision: `e632a86b2ca8fbb7f83b3130ba083784c7817667`.

Principles: [verificationdesign.com][principles] ([pinned source][principles-src]).

[principles]: https://verificationdesign.com/principles/
[principles-src]: https://raw.githubusercontent.com/verificationdesign/verificationdesign/e632a86b2ca8fbb7f83b3130ba083784c7817667/verification_design.md
[p1]: https://raw.githubusercontent.com/verificationdesign/verificationdesign/e632a86b2ca8fbb7f83b3130ba083784c7817667/verification_design.md#1-external-signals-over-self-review
[p2]: https://raw.githubusercontent.com/verificationdesign/verificationdesign/e632a86b2ca8fbb7f83b3130ba083784c7817667/verification_design.md#2-independence-between-generation-and-verification
[p3]: https://raw.githubusercontent.com/verificationdesign/verificationdesign/e632a86b2ca8fbb7f83b3130ba083784c7817667/verification_design.md#3-step-level-checkpoints
[p4]: https://raw.githubusercontent.com/verificationdesign/verificationdesign/e632a86b2ca8fbb7f83b3130ba083784c7817667/verification_design.md#4-adversarial-framing
[p5]: https://raw.githubusercontent.com/verificationdesign/verificationdesign/e632a86b2ca8fbb7f83b3130ba083784c7817667/verification_design.md#5-explicit-criteria
[p6]: https://raw.githubusercontent.com/verificationdesign/verificationdesign/e632a86b2ca8fbb7f83b3130ba083784c7817667/verification_design.md#6-executable-verification-is-king
[p7]: https://raw.githubusercontent.com/verificationdesign/verificationdesign/e632a86b2ca8fbb7f83b3130ba083784c7817667/verification_design.md#7-cross-family-beats-self-verification
[p8]: https://raw.githubusercontent.com/verificationdesign/verificationdesign/e632a86b2ca8fbb7f83b3130ba083784c7817667/verification_design.md#8-simulate-debate
[p9]: https://raw.githubusercontent.com/verificationdesign/verificationdesign/e632a86b2ca8fbb7f83b3130ba083784c7817667/verification_design.md#9-isolate-verification-from-ambient-state
