# Blind Oracle

*(Verification Pattern)*

## Name

**Blind Oracle**

Also known as: Independent Derivation, Extract-Then-Compare, Spec-Only Verification, Draft-Blind Judgment.

## Intent

Derive expected evidence from the spec, the question, or independent re-execution without conditioning that derivation on the agent's draft, reasoning trace, or shortcut history.

The verifier may inspect the draft afterward to extract observed values. The expected side of the comparison must come from a channel the draft cannot influence. The mechanic is structural independence between the derivation path and the production path, not blindness to the artifact.

## Problem

A judge prompt places the draft answer in the verifier's working context before asking for a verdict. The verifier's "is this correct?" collapses into "does this look plausible?" because the verifier has nothing independent to compare against. The same blind spots that produced the answer steer the judgment.

Common shapes:

* judge prompts show `[Submission]` before asking whether the response meets the criteria;
* evaluator prompts pass question, submitted answer, and ground truth into one model call, then parse `CORRECT` or `INCORRECT`;
* factored verification questions are answered while the draft is still visible to the verifier;
* verifiers "do not see the draft" but receive the writer's reasoning trace, which carries the same anchors as the draft.

`verification_design.md` Principle 2 names the rule: if the verifier can see the original output, it copies the same errors. The verification step must not be conditioned on the draft. The Chain-of-Verification factored and revised variant, where verification questions were answered without conditioning on the draft, improved FACTSCORE from 55.9 to 71.4 [arXiv:2309.11495].

Single-agent systems cannot get full independence. The writer and verifier share a context window. Blind Oracle is the mitigation: compute expected before reading the draft, separate extraction from judgment, and use tools where possible.

## Forces

* **Independent derivation vs. agent convenience.** Re-deriving expected values from the spec costs another pass; reading the draft does not.
* **Blindness to draft vs. inspection of artifact.** The verifier may need the artifact to extract observed values. The artifact must not define expected values.
* **Spec-derivable vs. spec-underivable.** The pattern only applies where expected can be computed from a separate path.
* **Single-context vs. separate-context.** In a single-agent system, the mitigation is order and source of derivation, not literal context separation.
* **Reasoning trace as evidence vs. reasoning trace as draft.** A writer's scratchpad anchors the verifier like the draft does.
* **Reference value vs. derived expected.** A pre-supplied reference can substitute for derivation only when the verifier derives expected from it before seeing the draft.

## Solution

Compute expected on a derivation path that has no read access to the draft, the writer's reasoning, or the writer's shortcut history. Extract observed from the draft after expected exists. Compare the two with a named operator.

The pattern lives at three layers:

* **Derivation channel:** the function or call that produces expected takes only the spec, question, or independent reference. Drafts, writer reasoning, and writer summaries are out of scope.
* **Extraction channel:** a separate pass extracts observed from the draft. Extraction may read the draft; it does not render the verdict.
* **Comparison:** a named **Comparator** operator decides verdict from `expected` and `observed`. No model call that takes the draft as input is invoked at comparison time.

Three common shapes:

* **Extract-then-compare:** extract raw values, print them, then compare to expected.
* **Blind re-derivation:** re-derive from scratch without referencing the prior answer, then compare.
* **Tool-mediated extraction:** use parsers, queries, calls, or other tools to extract observed values rather than asking the model to interpret rendered output.

## Mechanism

1. **Identify the derivation channel.** Expected may come from spec parsing, independent execution, a pre-supplied reference, or blind re-derivation by a model call that does not receive the draft.
2. **Compute expected first.** Derive expected before any read access to the draft. The derivation function's signature should not accept the draft as a parameter.
3. **Extract observed from the draft.** A mechanical extractor reads the draft and produces a structured observed value. No verdict is rendered here.
4. **Compare with a named operator.** Exact match, regex, JSON distance, trajectory match, or another named operator decides pass or fail.
5. **Stamp derivation source.** The verdict records `derivation_source: "spec"`, `"reference"`, or `"blind_rederivation"`.

## Pattern / Antipattern

The same task: decide whether a submitted answer satisfies a question or criterion. The antipattern puts the submission into the judge prompt before expected is derived. The pattern derives expected first, extracts observed second, and compares them with an explicit operator.

### Antipattern: criteria and submission in one judge prompt

The naive implementation fuses extraction, comparison, and judgment in one model call.

```python
def grade_submission(model, input_text: str, submission: str, criteria: str) -> str:
    prompt = f"""
[Input]
{input_text}

[Submission]
{submission}

[Criteria]
{criteria}

Does the submission meet the criteria?
Return CORRECT or INCORRECT and explain your answer.
"""
    return model.complete(prompt)
```

The submission is in the verifier's context before the verifier has derived expected. The verdict can anchor on the draft and then rationalize from the criteria.

LangChain's criteria evaluator and scoring evaluator have this prompt shape: criteria and submission are presented together before the model renders a judgment. The scoring variant may also include a reference answer, but adding `[Reference]` does not make the judge blind when `[Submission]` is still in view.

Some evaluations must inspect the artifact being graded. The failure mode is not artifact inspection; it is treating draft-conditioned judgment as independent evidence. Blind Oracle separates derivation from extraction; the antipattern fuses them through a single judge prompt that anchors on the submission.

This is the same body as **Comparator**'s fused QA evaluator antipattern from another angle. Comparator cares that extraction, comparison, and judgment are fused. Blind Oracle cares that the fused call conditions expected on the draft.

### Pattern: derive expected before reading the draft

The structured implementation computes expected through a function that cannot read the draft, then extracts observed and compares.

```python
from collections.abc import Callable
from dataclasses import dataclass
from typing import Literal


Question = str
Draft = str
Expected = str
Observed = str
Verdict = Literal["pass", "fail"]
DerivationSource = Literal["spec", "reference", "blind_rederivation"]


@dataclass(frozen=True)
class BlindVerification:
    question: Question
    expected: Expected
    observed: Observed
    verdict: Verdict
    derivation_source: DerivationSource
    extraction_method: str
    comparator: str
    draft_in_derivation_context: bool


def blind_verify(
    question: Question,
    draft: Draft,
    derive_expected: Callable[[Question], tuple[Expected, DerivationSource]],
    extract_observed: Callable[[Draft], Observed],
    compare: Callable[[Expected, Observed], Verdict],
) -> BlindVerification:
    expected, source = derive_expected(question)
    observed = extract_observed(draft)
    verdict = compare(expected, observed)
    return BlindVerification(
        question=question,
        expected=expected,
        observed=observed,
        verdict=verdict,
        derivation_source=source,
        extraction_method="programmatic",
        comparator=getattr(compare, "__name__", type(compare).__name__),
        draft_in_derivation_context=False,
    )


def derive_expected_from_spec(question: Question) -> tuple[Expected, DerivationSource]:
    filing_spec = {
        "What is the named operator in this 10-K excerpt?": {
            "named_operator": "Eastern Pacific Holdings",
        },
    }
    return filing_spec[question]["named_operator"], "spec"


def extract_answer(draft: Draft) -> Observed:
    return draft.strip()


def exact_match(expected: Expected, observed: Observed) -> Verdict:
    return "pass" if expected == observed else "fail"


question = "What is the named operator in this 10-K excerpt?"
correct_draft = "Eastern Pacific Holdings"
adversarial_draft = "Western Atlantic Holdings"

correct_result = blind_verify(
    question,
    correct_draft,
    derive_expected_from_spec,
    extract_answer,
    exact_match,
)
adversarial_result = blind_verify(
    question,
    adversarial_draft,
    derive_expected_from_spec,
    extract_answer,
    exact_match,
)

assert (
    correct_result.expected == adversarial_result.expected
    and correct_result.verdict == "pass"
    and adversarial_result.verdict == "fail"
)
```

The load-bearing move is the call order and function boundary. `derive_expected_from_spec` has no draft parameter, so the draft cannot set expected. The draft is read only by `extract_answer`, which produces observed for comparison.

Anthropic's outcome-grader notebook is the closest OSS instance. It runs the grader as a second agent with its own context window, cannot see the writer's reasoning, and re-reads the artifact against a rubric. It is adjacent rather than pure Blind Oracle because the grader does not derive a separately channelled expected value before grading. It still operationalizes the key separation: the grader's evidence path is structurally independent of the writer's evidence path.

Outcome grading also composes with **Adversarial Frame**. Blind Oracle separates the derivation channel; Adversarial Frame defines what evidence is admissible for acceptance.

## Determinism Move

Blind Oracle constrains `context_contamination` by separating the derivation channel from the production channel. Expected comes from spec, reference, or re-derivation. Observed comes from the draft. The two never share an input path.

It also constrains `self_review_bias` as a design judgment for same-context systems: when the writer's draft is already in the verifier's context, the check can inherit the writer's anchors before it has independent evidence.

The determinism move is enforced derivation independence; if the function that produces expected can read the draft, the verification is anchored regardless of what the prompt says.

## Observable Signal

Every Blind Oracle report should include:

* question or spec input;
* expected value;
* derivation source (`spec`, `reference`, `blind_rederivation`);
* observed value;
* extraction method (`programmatic`, `model_mediated`);
* comparator name;
* verdict;
* draft-in-derivation-context boolean.

A useful report makes the independence visible:

```text
question: "What is the named operator in this 10-K excerpt?"
expected: "Eastern Pacific Holdings"
derivation_source: spec
observed: "Eastern Pacific Holdings"
extraction_method: programmatic
comparator: exact_match
verdict: pass
draft_in_derivation_context: false
```

In the code sample, `draft_in_derivation_context: false` records the wrapper's call shape: `derive_expected` received the question and no draft argument. The paired correct and adversarial runs are the behavior check that expected stays stable while the verdict changes.

## Failure Modes

* **Submission-First Prompting:** the verifier prompt places the draft in context before asking for a verdict. The model's expected becomes the draft restated. Derive expected first in a separate call that does not receive the draft.
* **Fused Extraction-Comparison-Judgment:** one model call extracts observed, compares it to expected, and renders a verdict. Split the task into deterministic extract and named compare operators.
* **Reasoning-Trace Leakage:** the verifier does not see the draft but receives the writer's chain-of-thought or scratchpad. Treat reasoning trace and shortcut history as draft-equivalent inputs.
* **Reference-As-Adornment:** a reference value is supplied alongside the submission in one prompt. Hide the submission until expected is derived from the reference.

## Use When

Use this pattern when:

* the property under check has a derivable expected value, such as math, parses, structural counts, or executable checks;
* false positives from draft-anchored judgment are a known failure mode;
* the spec or reference can be processed independently of the draft;
* generation and verification share a context window;
* the verifier is LLM-based and could otherwise be conditioned on the draft.

## Do Not Use When

Do not reach for Blind Oracle when:

* expected cannot be derived without reading the draft;
* **Executable Analog** can specialize the pattern with compilation, execution, or runtime traces;
* no expected exists and the right pattern is **Adversarial Frame** or a calibrated **Judge Harness**;
* the artifact and the spec are the same object and derivation must reference the artifact.

If derivation independence cannot be enforced, label the verification as draft-anchored and escalate to a Judge Harness with perturbation, repetition, and calibration.

## Evidence

* **Verification Design Principle 2:** the design doc names independence between generation and verification and warns that a verifier conditioned on the original output copies the same errors.
* **Chain-of-Verification:** the research callout records the factored and revised variant, where verification questions are answered without conditioning on the draft, and reports the FACTSCORE improvement from 55.9 to 71.4 [arXiv:2309.11495].
* **[LangChain](https://github.com/langchain-ai/langchain) criteria and scoring evaluators:** the verification sweep records prompt shapes where criteria, submission, and sometimes reference are shown together before the model renders judgment.
* **LangChain QA evaluator:** the same sweep records a fused extraction, comparison, and judgment path shared with the Comparator antipattern.
* **Anthropic outcome grader:** the verification sweep records a supporting instance: a separate grader context inspects the artifact against a rubric without seeing the writer's reasoning.

## Related Patterns

* **Comparator:** provides the named operator that decides verdict from `expected` and `observed`.
* **Adversarial Frame:** defines admissibility for acceptance; Blind Oracle defines the upstream derivation channel.
* **Cross-Family:** addresses which model verifies; Blind Oracle addresses what the verifier is allowed to see.
* **Executable Analog:** is the executable specialization, and strongest form, of Blind Oracle when expected can be derived by executing the spec.
* **Judge Harness:** wraps a Blind Oracle judge with perturbation, repetition, and calibration when the derivation channel still has subjective slack.
