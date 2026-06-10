# Comparator

*(Verification Pattern)*

## Name

**Comparator**

Also known as: Named Comparison, Comparison Operator, Match Mode.

## Intent

Express verification comparison as a named operator from a finite family, so the verdict is a deterministic function of `(expected, observed, operator, threshold, normalization)` rather than a model's interpretation of "does this look right?"

## Problem

Many verification steps hide the actual comparison inside an LLM prompt:

* "Here is the question, the student's answer, and the true answer. Grade CORRECT or INCORRECT."
* "Here is the expected behavior and the actual behavior. Does the output satisfy the requirement?"
* "Here is the rubric and the answer. Score it."

Those prompts fuse three operations that should be separate:

1. extract the observed value,
2. compare it to the expected value,
3. produce the verdict.

Once those operations are fused, the recorded result is only the model's label. A reviewer cannot replay the comparison without rerunning the judge. They cannot see what tolerance was applied, whether whitespace mattered, whether order mattered, whether JSON was canonicalized, or whether the model silently used a semantic standard that was never specified.

`verification_design.md` Principle 5 says verifiers need explicit criteria: what is checked, what is expected, and how it is checked. Comparator names the "how." Principle 6 then pushes the same idea toward executable verification: once the comparison is named and deterministic, the verdict can be replayed.

## Forces

* **Exact vs. semantic equivalence.** Character-for-character equality is auditable, but many tasks need normalization, regex matching, structured comparison, or trajectory matching.
* **Strict vs. tolerant.** The system must decide whether casing, punctuation, ordering, extra fields, or near misses matter.
* **Single value vs. structured state.** A comparator may operate on one string, a JSON tree, a list of tool calls, or a predicate set.
* **Operator design vs. judge call.** A named operator costs more to design than a one-off prompt, but it is cheaper to run and easier to audit.
* **Replayable verdict vs. opaque label.** A comparator report shows the operator and values; a fused judge report shows only a label.

## Solution

Maintain a finite family of named comparison operators. For each verification step, choose the least restrictive operator allowed by the stated criterion, rather than tuning the operator until the current answer passes.

Extract the observed value before comparison. Do not let the comparison operator fetch state, parse a model's reasoning, or decide what should be checked. It receives `expected`, `observed`, and operator settings. It returns a structured record with the operator name, comparison values, normalization, notes, score, threshold, and derived verdict.

Common shapes:

* **String comparators:** exact match, normalized exact match, regex match, JSON canonical equality, JSON edit distance.
* **Structured-event comparators:** trajectory exact, trajectory in-order, trajectory any-order.
* **Predicate aggregators:** per-criterion predicates with a named aggregation policy such as all-must-pass or k-of-n.

If no named operator fits, that is useful information. Tighten the answer format so a comparator applies, or escalate to a **Judge Harness**. Do not silently collapse the check into an inline LLM judgment.

## Mechanism

1. **Define the comparison surface.** Name whether the comparison is over a string, regex, JSON tree, structured event sequence, or predicate set.
2. **Pick a named operator.** Choose `exact`, `normalized_exact`, `regex`, `json_canonical`, `json_distance`, `trajectory_exact`, `trajectory_in_order`, `trajectory_any_order`, or a named aggregator.
3. **Extract observed value separately.** Extraction happens before the comparator runs and is recorded verbatim.
4. **Apply the operator.** Return a structured score with `{operator, expected, observed, score, threshold, normalization}`; for `regex`, the expected field is the pattern being matched.
5. **Record every comparison.** Reports include operator, expected, observed, normalization, notes, score, threshold, and a verdict derived from `score >= threshold` for passes and failures.

## Pattern / Antipattern

The same task: verify whether a student's answer matches a known answer. The antipattern asks an LLM to perform the comparison and emit a label. The pattern applies a named comparator to extracted values and records the full comparison.

### Antipattern: fused comparison prompt

The naive implementation puts question, submitted answer, and true answer in one prompt. Extraction, comparison, and judgment happen inside the model call.

```python
def grade_answer(question: str, student_answer: str, true_answer: str, model) -> dict:
    prompt = f"""
    You are a teacher grading a quiz.

    QUESTION: {question}
    STUDENT ANSWER: {student_answer}
    TRUE ANSWER: {true_answer}

    Grade the student answer as CORRECT or INCORRECT.
    """
    label = model.complete(prompt).strip().upper()
    passed = label.startswith("CORRECT")
    return {
        "verdict": "pass" if passed else "fail",
        "label": label,
    }
```

This may be a practical fallback for semantic equivalence, but it is not a comparator. The report does not say what was compared, which operator was used, what tolerance applied, or what observed value the comparison consumed. The model's final label is the only artifact.

LangChain's QA evaluator evidence has this shape: the evaluator prompt includes the question, student answer, and true answer, and an LLM chain parses CORRECT or INCORRECT into a score. That is the right tool only when a named comparison operator would over-reject. It becomes the Comparator antipattern when exact, regex, JSON, trajectory, or execution comparison would have sufficed.

### Pattern: named operator dispatch

The structured implementation separates extraction from comparison and makes the operator explicit.

```python
import json
import re
from dataclasses import dataclass, field
from typing import Any, Callable


@dataclass(frozen=True)
class ComparisonResult:
    operator: str
    expected: Any
    observed: Any
    score: float
    threshold: float
    normalization: list[str]
    notes: list[str] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return self.score >= self.threshold

    @property
    def verdict(self) -> str:
        return "pass" if self.passed else "fail"

    def to_report(self) -> dict[str, Any]:
        return {
            "operator": self.operator,
            "expected": self.expected,
            "observed": self.observed,
            "normalization": self.normalization,
            "notes": self.notes,
            "score": self.score,
            "threshold": self.threshold,
            "verdict": self.verdict,
        }


def normalize_text(value: str) -> str:
    return " ".join(value.lower().strip().split())


def exact(expected: str, observed: str) -> tuple[float, list[str], list[str]]:
    return (1.0 if expected == observed else 0.0, [], [])


def normalized_exact(expected: str, observed: str) -> tuple[float, list[str], list[str]]:
    return (
        1.0 if normalize_text(expected) == normalize_text(observed) else 0.0,
        ["lowercase", "strip", "collapse_whitespace"],
        [],
    )


def regex(expected: str, observed: str) -> tuple[float, list[str], list[str]]:
    try:
        matched = re.fullmatch(expected, observed)
    except re.error:
        return (0.0, [], ["invalid_regex_pattern"])
    return (1.0 if matched else 0.0, [], [])


def json_canonical(expected: str, observed: str) -> tuple[float, list[str], list[str]]:
    try:
        expected_json = json.dumps(json.loads(expected), sort_keys=True)
        observed_json = json.dumps(json.loads(observed), sort_keys=True)
    except json.JSONDecodeError:
        return (0.0, [], ["json_parse_failed"])
    return (1.0 if expected_json == observed_json else 0.0, ["json_sort_keys"], [])


OPERATORS: dict[str, Callable[[str, str], tuple[float, list[str], list[str]]]] = {
    "exact": exact,
    "normalized_exact": normalized_exact,
    "regex": regex,
    "json_canonical": json_canonical,
}


def compare(operator: str, expected: str, observed: str, threshold: float = 1.0) -> ComparisonResult:
    if operator not in OPERATORS:
        raise ValueError(f"Unknown comparator: {operator}")
    if not 0.0 < threshold <= 1.0:
        raise ValueError("threshold must be in (0, 1]")

    score, normalization, notes = OPERATORS[operator](expected, observed)
    return ComparisonResult(
        operator=operator,
        expected=expected,
        observed=observed,
        score=score,
        threshold=threshold,
        normalization=normalization,
        notes=notes,
    )


report = compare(
    operator="normalized_exact",
    expected="The answer is 42.",
    observed="the answer is 42.",
)
assert report.passed is True
assert compare("exact", "The answer is 42.", "the answer is 42.").passed is False
assert report.normalization == ["lowercase", "strip", "collapse_whitespace"]

malformed_json = compare("json_canonical", '{"answer": 42}', '{"answer":')
assert malformed_json.passed is False
assert malformed_json.notes == ["json_parse_failed"]

assert report.to_report() == {
    "operator": "normalized_exact",
    "expected": "The answer is 42.",
    "observed": "the answer is 42.",
    "normalization": ["lowercase", "strip", "collapse_whitespace"],
    "notes": [],
    "score": 1.0,
    "threshold": 1.0,
    "verdict": "pass",
}
```

LangChain's non-LLM evaluator family demonstrates this pattern at framework level: exact match, regex match, and JSON edit distance take reference and prediction values and return mechanical scores. Its evaluator schema distinguishes named non-LLM evaluators from LLM evaluators, which is the architectural distinction Comparator needs.

ADK's `TrajectoryEvaluator` shows the structured-event variant. It compares actual and expected tool-call sequences using named match modes: `EXACT`, `IN_ORDER`, and `ANY_ORDER`. This illustrates Comparator as a finite family of declared tolerance contracts, not just equality.

## Determinism Move

Comparator constrains `judge_subjectivity` by making the verdict a deterministic function of expected value, observed value, operator, threshold, and normalization. It constrains `criteria_drift` because a named operator is stable across runs in a way that a prompt-based judge's interpretation is not.

The same `trajectory_in_order` operator should return the same verdict today and next week. If the operator changes, the change is a code or configuration diff, not a hidden shift in a judge prompt's interpretation.

## Observable Signal

Every Comparator report should include:

* operator name;
* expected value or reference;
* observed value extracted before comparison;
* normalization steps applied before comparison;
* notes for recorded parse or pattern failures;
* score and threshold;
* pass/fail verdict.

A useful report is replayable from the record plus the pinned comparator implementation:

```text
operator: normalized_exact
expected: "The answer is 42."
observed: "the answer is 42."
normalization: lowercase, strip, collapse_whitespace
notes: []
score: 1.0
threshold: 1.0
verdict: pass
```

## Failure Modes

* **Fused Judgment:** Extraction, comparison, and verdict collapse into one LLM prompt. Extract observed value first, then apply a named operator outside the model call.
* **Wrong Operator:** The check uses `exact` when `regex`, `json_canonical`, or `trajectory_any_order` matches the criterion. Apply the Solution rule: choose the least restrictive operator the criterion permits.
* **Hidden Normalization:** The operator lowercases, strips punctuation, or canonicalizes JSON without reporting that step. Record normalization and normalized comparison surfaces.
* **No Tolerance Policy:** Structured events are compared without declaring exact, in-order, any-order, distance, or threshold semantics. Reject `compare(expected, observed)` without a mode.

## Use When

Use this pattern when:

* the check has a known expected value, pattern, reference object, or expected event sequence;
* the observed value can be extracted separately from the comparison;
* a named operator covers the comparison or can be defined cheaply;
* the report must be auditable without rerunning a model;
* the same comparison will run repeatedly in CI, regression tests, or agent loops.

## Do Not Use When

Do not reach for Comparator when:

* the answer is genuinely open-ended and no reference exists;
* semantic equivalence is the actual task and a tight comparator would reject acceptable answers;
* designing a comparator costs more than a one-off human review;
* the comparison needs a calibrated model judge. Use **Judge Harness** instead of an inline fused judgment.

## Evidence

* **Verification Design Principles 5 and 6:** The design doc requires explicit criteria and prefers executable verification. Comparator names the comparison method inside that criteria record.
* **[LangChain](https://github.com/langchain-ai/langchain) non-LLM evaluators:** The evidence summary records exact, regex, and JSON distance evaluators that take reference and prediction as inputs and return mechanical scores.
* **LangChain evaluator schema:** The framework distinguishes named non-LLM evaluator types from LLM evaluators, making the operator family explicit.
* **[ADK](https://github.com/google/adk-python) TrajectoryEvaluator:** The evidence summary records `EXACT`, `IN_ORDER`, and `ANY_ORDER` modes for structured tool-call trajectories.
* **LangChain QA evaluator:** The verification sweep records the fused-comparison antipattern: question, answer, and prediction go into one LLM prompt, and CORRECT or INCORRECT is parsed as the score.

## Related Patterns

* **Executable Analog:** extracts the observed value; Comparator names the operator that compares it.
* **Blind Oracle:** fused comparison often violates blind evaluation because the judge sees the draft beside the truth.
* **Judge Harness:** handles cases where no named comparator fits, but only with calibration and reliability checks.
* **Constitution:** can name expected values and accepted comparator operators.
* **Delta:** produces relative observed values that Comparator can evaluate with a declared numeric tolerance operator.
