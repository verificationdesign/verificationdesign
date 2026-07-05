# Judge Harness

*(Verification Pattern)*

## Name

**Judge Harness**

Also known as: Judge Reliability Harness, LLM-as-Judge Harness, Calibrated Judge Wrapper, Perturbation + Repetition Layer.

## Intent

Wrap an LLM judge in a structural harness of perturbation, repetition, calibration, and reporting so that one judge verdict becomes a measured signal with visible consistency and bias controls.

The harness is the layer around the judge. It is not the judge prompt itself. A prompt that tells the judge to avoid bias may help the call, but it does not create the harness.

## Problem

An LLM judge returns one verdict. The system treats that verdict as ground truth.

That can look disciplined in code:

* the judge prompt warns the model to avoid position, length, and name biases;
* assistant A and assistant B are shown in fixed labeled slots, then a single pairwise verdict is parsed;
* the judge is repeated only when the verdict disagrees with the architect's expectation;
* a numeric judge score is logged, but the judge is never calibrated against human labels;
* downstream consumers receive only `PASS` or `FAIL`, not the sample distribution behind it.

The verifier failure is not that the judge is an LLM. The failure is treating a single subjective sample as a reliable measurement. Prompt-level caution does not expose whether the judge is stable under harmless input changes, whether repeated samples agree, or whether aggregate verdicts track human labels.

`verification_design.md` Principle 7 names the broader boundary: cross-family beats self-verification. The Judge Reliability Harness update narrows it: cross-family LLM judges are not automatically reliable verification signals; they need perturbation tests, observed-behavior reporting, and calibration [arXiv:2603.05399]. The Gaming the Judge update extends the caution: even cross-family judges can be manipulated through chain-of-thought, so the harness must report observed judge behavior under perturbation, not only raw verdicts [arXiv:2601.14691].

## Forces

* **Single verdict vs. distribution of verdicts.** One call is cheap; a distribution exposes variance the single call hides.
* **Prompt-level mitigation vs. structural mitigation.** "Avoid position bias" in the prompt is a wish; swapping positions before each run is a property.
* **Cost vs. confidence.** Each perturbation, swap, or repetition multiplies the judge call budget; the harness trades budget for measured reliability.
* **Calibration anchor vs. drift.** Without a human-label calibration set, harness output is internally consistent but externally unanchored.
* **Aggregation rule vs. ambient majority.** Majority vote is one rule; abstain-on-disagreement is another. The harness names the rule.
* **Reporting boundary.** A harness that aggregates internally but reports only a final verdict loses the calibration evidence the downstream consumer needs.

## Solution

Put a structural harness around the judge call. The judge prompt can still say "be careful about position bias," but the harness enforces the check outside the prompt.

The harness has four layers:

* **Perturbation:** vary judge inputs in ways that should not change the verdict, such as paraphrase, formatting changes, name swap, or position swap when the judge compares two answers.
* **Repetition:** invoke the judge N times per perturbation with independent samples.
* **Aggregation rule:** choose a named rule that turns the sample into a harness verdict, such as majority, supermajority, or abstain-on-disagreement.
* **Calibration and reporting:** compare aggregated verdicts against a human-labeled calibration set, then report the verdict, sample distribution, consistency rate, and calibration anchors together.

A bias-warning prompt is a judge input. Perturbation, repetition, aggregation, calibration, and reporting are harness properties.

## Mechanism

1. **Identify the judge call surface.** Find the LLM call that returns the verdict.
2. **Define the perturbation set.** Name which input variations should preserve the verdict.
3. **Set the repetition count and aggregation rule.** Choose N and the rule before seeing the result.
4. **Maintain calibration labels.** Keep a human-labeled calibration set and periodically re-calibrate the judge.
5. **Stamp the verdict.** Record sample distribution, consistency rate, perturbations applied, aggregation rule, and calibration source.

## Pattern / Antipattern

The two examples use different judge shapes to show the same reliability boundary. The antipattern is a one-call pairwise judge that trusts one A/B/C parse. The pattern is a single-answer PASS/FAIL judge wrapped as an instrument with sampling, perturbation, aggregation, calibration, and reportable behavior.

### Antipattern: one-call judge with bias warning

The naive implementation places the bias instruction in the prompt and treats the first parsed verdict as the result.

```python
from typing import Literal


Verdict = Literal["A", "B", "C"]


def one_call_pairwise_judge(model, question: str, answer_a: str, answer_b: str) -> Verdict:
    prompt = f"""
You are an impartial judge.
Avoid position bias, length bias, and name bias.

[Question]
{question}

[Assistant A]
{answer_a}

[Assistant B]
{answer_b}

Return exactly one verdict: [[A]], [[B]], or [[C]].
"""
    raw = model.complete(prompt)
    if "[[A]]" in raw:
        return "A"
    if "[[B]]" in raw:
        return "B"
    return "C"
```

The prompt warns about bias, but the code never swaps positions, repeats the call, calibrates against labels, or reports the sample distribution. One parse becomes the verdict.

LangChain's pairwise evaluator is the canonical antipattern pick: it puts explicit position, length, and name bias warnings in the prompt, fixes assistant A and assistant B in labeled slots, then parses one pairwise verdict, `[[A]]`, `[[B]]`, or `[[C]]`, from a single judge call. The LangChain scoring evaluator is the sibling shape: an impartial one-shot prompt returns a 1-to-10 rating instead of an A/B/C choice.

A bias-warning in the judge prompt is not wrong on its own; it is a useful nudge. It becomes the Judge Harness antipattern when the bias-warning is treated as the harness, with no perturbation, repetition, calibration, or reporting around the call. This also cross-lists with **Blind Oracle** when the submitted answer is already in the verifier's context before independent expected evidence exists.

### Pattern: calibrated perturbation and repetition wrapper

The structured implementation wraps the judge call and returns the measurement boundary with the verdict.

```python
from collections import Counter
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from typing import Literal


Verdict = Literal["PASS", "FAIL"]
AggregationRule = Literal[
    "majority",
    "supermajority",
    "abstain_on_disagreement",
]
SUPERMAJORITY_THRESHOLD = 2 / 3


@dataclass(frozen=True)
class PromptInputs:
    question: str
    answer: str


@dataclass(frozen=True)
class Perturbation:
    name: str
    apply: Callable[[PromptInputs], PromptInputs]


@dataclass(frozen=True)
class CalibrationSet:
    name: str
    labeled_examples: tuple[tuple[PromptInputs, Verdict], ...]


@dataclass(frozen=True)
class HarnessResult:
    verdict: Verdict | Literal["ABSTAIN"]
    sample_distribution: dict[str, int]
    consistency_rate: float
    perturbations: tuple[str, ...]
    repetitions: int
    aggregation_rule: AggregationRule
    calibration_source: str
    judge_model: str
    calibrated_precision: float | None
    calibrated_recall: float | None


class JudgeHarness:
    def __init__(
        self,
        perturbations: Iterable[Perturbation],
        repetitions: int,
        aggregation_rule: AggregationRule,
        calibration_set: CalibrationSet,
    ):
        self.perturbations = tuple(perturbations)
        if not self.perturbations:
            raise ValueError("JudgeHarness requires at least one perturbation")
        if repetitions <= 0:
            raise ValueError("JudgeHarness repetitions must be positive")
        self.repetitions = repetitions
        self.aggregation_rule = aggregation_rule
        self.calibration_set = calibration_set

    def evaluate(
        self,
        judge_call: Callable[[PromptInputs], Verdict],
        prompt_inputs: PromptInputs,
        judge_model: str,
    ) -> HarnessResult:
        samples: list[Verdict] = []
        for perturbation in self.perturbations:
            perturbed = perturbation.apply(prompt_inputs)
            for _ in range(self.repetitions):
                samples.append(judge_call(perturbed))

        counts = Counter(samples)
        verdict, count = counts.most_common(1)[0]
        total = sum(counts.values())
        consistency_rate = count / total
        if self.aggregation_rule == "abstain_on_disagreement" and len(counts) > 1:
            final_verdict: Verdict | Literal["ABSTAIN"] = "ABSTAIN"
        elif self.aggregation_rule == "supermajority" and count / total < SUPERMAJORITY_THRESHOLD:
            final_verdict = "ABSTAIN"
        else:
            final_verdict = verdict

        precision, recall = calibrate(judge_call, self.calibration_set)
        return HarnessResult(
            verdict=final_verdict,
            sample_distribution=dict(counts),
            consistency_rate=consistency_rate,
            perturbations=tuple(item.name for item in self.perturbations),
            repetitions=self.repetitions,
            aggregation_rule=self.aggregation_rule,
            calibration_source=self.calibration_set.name,
            judge_model=judge_model,
            calibrated_precision=precision,
            calibrated_recall=recall,
        )


def calibrate(
    judge_call: Callable[[PromptInputs], Verdict],
    calibration_set: CalibrationSet,
) -> tuple[float, float]:
    labels = calibration_set.labeled_examples
    if not labels:
        return 0.0, 0.0
    predicted_positive = 0
    true_positive = 0
    actual_positive = 0
    for inputs, human_label in labels:
        prediction = judge_call(inputs)
        predicted_positive += int(prediction == "PASS")
        true_positive += int(prediction == "PASS" and human_label == "PASS")
        actual_positive += int(human_label == "PASS")
    precision = true_positive / predicted_positive if predicted_positive else 0.0
    recall = true_positive / actual_positive if actual_positive else 0.0
    return precision, recall


def identity(inputs: PromptInputs) -> PromptInputs:
    return inputs


class SequencedJudge:
    def __init__(self, verdicts: tuple[Verdict, ...]):
        self.verdicts = verdicts
        self.index = 0

    def __call__(self, inputs: PromptInputs) -> Verdict:
        verdict = self.verdicts[self.index % len(self.verdicts)]
        self.index += 1
        return verdict


prompt_inputs = PromptInputs(
    question="Does the answer cite the required source?",
    answer="Yes. It cites the required source directly.",
)
judge_sequence: tuple[Verdict, ...] = (
    "PASS",
    "PASS",
    "PASS",
    "FAIL",
    "PASS",
    "FAIL",
    "PASS",
    "FAIL",
    "PASS",
)

majority_harness = JudgeHarness(
    perturbations=[
        Perturbation("paraphrase", identity),
        Perturbation("format_change", identity),
    ],
    repetitions=4,
    aggregation_rule="majority",
    calibration_set=CalibrationSet("human_labeled_set_v1", ((prompt_inputs, "PASS"),)),
)
majority_result = majority_harness.evaluate(SequencedJudge(judge_sequence), prompt_inputs, "gpt-4o")
assert majority_result.verdict == "PASS"
assert majority_result.sample_distribution == {"PASS": 5, "FAIL": 3}

supermajority_harness = JudgeHarness(
    perturbations=[
        Perturbation("paraphrase", identity),
        Perturbation("format_change", identity),
    ],
    repetitions=4,
    aggregation_rule="supermajority",
    calibration_set=CalibrationSet("human_labeled_set_v1", ((prompt_inputs, "PASS"),)),
)
supermajority_result = supermajority_harness.evaluate(
    SequencedJudge(judge_sequence),
    prompt_inputs,
    "gpt-4o",
)
assert supermajority_result.verdict == "ABSTAIN"

result = majority_harness.evaluate(SequencedJudge(judge_sequence), prompt_inputs, "gpt-4o")
expected = HarnessResult(
    verdict="PASS",
    sample_distribution={"PASS": 5, "FAIL": 3},
    consistency_rate=0.625,
    perturbations=("paraphrase", "format_change"),
    repetitions=4,
    aggregation_rule="majority",
    calibration_source="human_labeled_set_v1",
    judge_model="gpt-4o",
    calibrated_precision=1.0,
    calibrated_recall=1.0,
)
assert result == expected
```

The load-bearing move is the returned measurement object. The downstream consumer can see that the verdict came from two perturbations, four repetitions per perturbation, majority aggregation, and a named human-labeled calibration source.

ADK `llm_as_judge` plus `rubric_based_evaluator` is the closest OSS contrast. It already gives repetition and named majority-vote aggregation. It still needs the remaining harness layers: input perturbation, external calibration anchors, and explicit sample-distribution and consistency reporting. The returned `PerInvocationResult` exposes selected aggregate rubric scores and status, not a count or distribution.

## Determinism Move

Judge Harness constrains `sampling_variance` by replacing one judge sample with an aggregated distribution. The verdict is no longer whichever sample happened to arrive first.

It constrains `judge_subjectivity` by anchoring aggregate verdicts to a human-labeled calibration set. The judge's reading is checked against an external reference rather than accepted as its own proof.

The determinism move is structural N-and-anchor; a single judge call without perturbation, repetition, or calibration is a verdict, not a measurement.

## Observable Signal

Every Judge Harness report should include:

* judge model identity;
* perturbations applied, such as `paraphrase`, `format_change`, `name_swap`, `position_swap` for pairwise judges, or `none`;
* repetitions per perturbation;
* aggregation rule, such as `majority`, `supermajority`, or `abstain_on_disagreement`;
* verdict;
* sample distribution;
* consistency rate;
* calibration source;
* calibrated precision and recall when calibration source is not `none`.

A useful report exposes the measurement behind the verdict:

```text
judge_model: gpt-4o
perturbations: paraphrase, format_change
repetitions_per_perturbation: 4
aggregation_rule: majority
sample_distribution: 5 PASS, 3 FAIL
verdict: PASS
consistency_rate: 0.625
calibration_source: human_labeled_set_v1
calibrated_precision: 1.0
calibrated_recall: 1.0
```

## Failure Modes

* **Bias-Warning As Harness:** the judge prompt says "avoid position bias" but the surrounding code does not swap positions. Replace the prompt-level wish with a structural pre-call perturbation.
* **Single-Sample Verdict:** the harness runs one judge call and reports its verdict directly. Set `repetitions >= 2` and define an aggregation rule.
* **Uncalibrated Aggregation:** the harness aggregates N samples but never compares the aggregated verdict against human labels. Maintain a calibration set; report precision and recall at the boundary.
* **Hidden Distribution:** the harness aggregates internally but reports only the final verdict. Surface sample distribution and consistency rate in the verdict object.

## Use When

Use this pattern when:

* the verification path uses an LLM-based judge;
* the verdict is high leverage, such as a gate for promotion, training, deployment, or automation;
* false positives or false negatives are costly enough to justify multi-sample budget;
* human labels exist or can be collected for a calibration set;
* the judge family has documented bias modes that can be perturbed against.

## Do Not Use When

Do not reach for Judge Harness when:

* verification is fully executable, so an **Executable Analog** or **Comparator** can decide it without an LLM;
* the verdict is low leverage and a single-sample judge call is proportionate;
* no calibration set can be obtained and the harness would aggregate without an anchor;
* the budget for repetitions is unavailable and the alternative is no judge at all.

If a harness is infeasible, label the judge verdict as informal and report the single sample without aggregation framing.

## Evidence

* **Verification Design Principle 7:** the design doc names cross-family verification as stronger than self-verification, while the Judge Reliability Harness update adds that LLM judges need perturbation tests, observed-behavior reporting, and calibration [arXiv:2603.05399].
* **Gaming the Judge update:** the design doc records that cross-family judges can still be manipulated through chain-of-thought, which makes observed judge behavior under perturbation part of the report [arXiv:2601.14691].
* **[LangChain](https://github.com/langchain-ai/langchain) pairwise evaluator:** the verification sweep records the canonical antipattern: explicit position, length, and name bias warnings in the prompt, fixed assistant A and assistant B slots, one parsed `[[A]]`, `[[B]]`, or `[[C]]` verdict, and no surrounding perturbation, repetition, calibration, or reporting code.
* **LangChain scoring evaluator:** the same sweep records a sibling one-shot shape: an impartial scoring prompt returns a 1-to-10 rating with no surrounding harness machinery.
* **[ADK](https://github.com/google/adk-python) LLM judge and rubric evaluator:** the verification sweep records partial harness machinery: multiple samples and majority-vote aggregation, but no inspected input perturbation, external calibration anchors, or explicit sample-distribution and consistency reporting.
* **Anthropic cookbook knowledge-graph eval:** the OSS sweep records a mechanical metric paired with an explicit note about what it does not measure. That reporting-boundary discipline is part of the Judge Harness contract.

## Related Patterns

* **Blind Oracle:** derives expected without conditioning on the draft; Judge Harness wraps the judge's verdict with structural N and calibration.
* **Cross-Family:** addresses which model judges; Judge Harness addresses how the judge's output is sampled, aggregated, and anchored.
* **Admissibility Gate:** defines admissibility for acceptance; Judge Harness measures the judge's reliability under perturbation.
* **Constitution:** provides the shared rubric the harness can calibrate against.
* **Comparator:** replaces Judge Harness when a deterministic comparison operator can decide the verdict without invoking an LLM judge.
