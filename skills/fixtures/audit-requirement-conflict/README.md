# audit-requirement-conflict

This script fixture covers a principle 2 requirement conflict and a separate requirement-basis defect. It is not a blind model evaluation; blind host tests have not run on this artifact.

A blind audit must record AC1 in artifact/spec.md:6 as a conflict: sole self-approval excludes the independent evaluator principle 2 demands. The finding quotes both demands with the requirement location, carries no severity, and remains for the operator to resolve.

A blind audit must separately record a defect with `basis: "requirement"` for AC2 in artifact/spec.md:7: the complete generate.py implementation prints the summary but has no receipt file writer. This structural failure has medium severity and an unmapped failure with a reason. It does not depend on observing a run or resolving AC1.

The filled record includes every checklist question; the other questions remain not-checked with explicit reasons. The generated expected.md compares routed and unrouted rendering, including Requirement conflicts and Basis: stated requirement.

Four negatives cover empty conflict evidence (`evidence`), empty requirement-basis defect evidence (`basis`, `evidence`), one-demand conflict evidence (`evidence`) and requirement-basis evidence without a location (`basis`). The validator checks quote counts and location shape; whether the quoted text expresses the demands and criterion remains an operator judgment.
