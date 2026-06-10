# Adversarial Frame

*(Verification Pattern)*

## Name

**Adversarial Frame**

Also known as: Operationalized Skepticism, Evidence-First Verification, Default-No Rubric.

## Intent

Replace tone-level skepticism instructions with admissibility rules that define what counts as proof, name common shortcut paths to reject, and invert the verifier's default from "accept if plausible" to "fail unless backed by trusted evidence."

## Problem

LLM verifiers tend to approve plausible work, especially when they are asked confirmatory questions:

* "Does this look right?"
* "Review carefully."
* "Be objective."
* "Give constructive feedback, then approve when addressed."

Those instructions describe a desired attitude, not a verification procedure. They ask the model to behave skeptically without defining what skepticism means. The judge may still treat the final answer as evidence, accept the agent's reasoning as if it were ground truth, or pass a lookalike source because it sounds close enough.

`verification_design.md` Principle 4 names the frame shift: ask "what could fail?" rather than "does this look right?" The same principle cites SycEval's 58.19% sycophancy rate as population-level evidence that agreement pressure is not a small edge case (AAAI 2025). A verifier that starts from plausibility will often rationalize acceptance.

Adversarial Frame makes skepticism structural. It names what evidence is admissible, names what evidence is forbidden, lists common shortcuts to reject, and makes the default verdict `no` when evidence is missing.

## Forces

* **Tone instruction vs. admissibility rule.** "Be critical" is a wish; "final answers and reasoning traces are not trusted evidence" is a constraint.
* **Accept-if-plausible vs. reject-unless-supported.** Default verdicts matter. Missing evidence should fail the property, not defer the decision.
* **Adversarial role vs. adversarial stance.** A critic role with a confirmatory prompt is not adversarial.
* **Improvement loop vs. disconfirmation loop.** Evaluator-optimizer loops can refine outputs, but refinement is not the same as adversarial verification.
* **Rubric cost vs. false approval cost.** Admissibility rules and shortcut lists take effort to write once; approving judges create recurring verification debt.

## Solution

Write rubrics that operationalize skepticism. Do not rely on the verifier's tone.

A rubric in this shape names:

* what counts as trusted evidence;
* what does not count as trusted evidence;
* which domain shortcuts must be rejected;
* what default verdict applies when evidence is missing;
* the required output order: evidence first, rationale second, verdict last.

Common shapes:

* **Evidence-admissibility rubric:** trusted evidence must come from procedurally sound tool calls or verified external sources. Final answers, reasoning, summaries, interpretations, and flawed tool calls do not count.
* **Shortcut-rejection list:** known lookalikes are rejected explicitly, such as an 8-K press-release exhibit when the rubric requires a 10-K or 10-Q filing.
* **Failure-hypothesis structure:** the verifier lists ways the answer could be wrong before it can approve.

The point is not to make the judge sound harsh. The point is to remove the judge's freedom to accept unsupported work.

## Mechanism

1. **Define admissibility.** Name the evidence categories that can support each property.
2. **Define forbidden evidence.** Name sources that cannot support the property, such as final answer text, reasoning trace, summaries, or flawed tool calls.
3. **Invert the default.** A property defaults to `no` unless admissible evidence supports it.
4. **Enumerate shortcuts.** List domain-specific substitutions the verifier must reject.
5. **Require evidence before verdict.** The report records evidence, then rationale, then yes/no verdict for each property.

## Pattern / Antipattern

The same task: decide whether an agent's final answer satisfies a property. The antipattern labels a role "critic" but gives it a confirmatory prompt. The pattern makes admissible evidence load-bearing and defaults to rejection when evidence is missing.

### Antipattern: critic role with confirmatory prompt

The naive implementation creates a critic agent but asks for general feedback and an approval token. There is no admissibility rule, no required failure search, no shortcut list, and no evidence-first report.

```python
critic = AssistantAgent(
    name="critic",
    system_message=(
        "You are a critic. Provide constructive feedback. "
        "Respond with APPROVE if your feedback has been addressed."
    ),
)

team = RoundRobinTeam(
    participants=[writer, critic],
    termination_token="APPROVE",
)
```

This is adversarial in role label only. It can improve an answer, but it does not require the critic to find disconfirming evidence before approval.

The AutoGen Chainlit sample has this shape: a `critic` agent gives constructive feedback and the team terminates on `APPROVE`. This is sample code, not the library core, but examples are how patterns spread. A critic role with a confirmatory prompt can look like verification in code review while producing acceptance at runtime.

Evaluator-optimizer loops need a different caveat. The Anthropic evaluator-optimizer notebook is a valid iteration pattern: the evaluator can return PASS, NEEDS_IMPROVEMENT, or FAIL and provide feedback for regeneration. The antipattern appears only when that improvement loop is misclassified as Adversarial Frame. "Has suggestions" is a weaker gate than "survived adversarial checks." Iteration and disconfirmation are separate patterns.

### Pattern: evidence admissibility with default-no verdict

The structured implementation defines what evidence may support each property and refuses to approve when support is absent.

```python
from dataclasses import dataclass
from typing import Literal


EvidenceType = Literal[
    "procedurally_sound_tool_call",
    "verified_external_source",
    "final_answer",
    "reasoning_trace",
    "summary",
    "flawed_tool_call",
]

Verdict = Literal["yes", "no"]


@dataclass(frozen=True)
class Evidence:
    kind: EvidenceType
    detail: str


@dataclass(frozen=True)
class PropertySpec:
    name: str
    admissible_evidence_types: set[EvidenceType]
    forbidden_evidence_types: set[EvidenceType]
    shortcut_rejections: list[str]
    default_verdict: Verdict = "no"


def verify_property(evidence: list[Evidence], spec: PropertySpec) -> dict:
    admissible = [
        item for item in evidence
        if item.kind in spec.admissible_evidence_types
        and item.kind not in spec.forbidden_evidence_types
    ]

    if not admissible:
        return {
            "property": spec.name,
            "evidence": [],
            "rationale": "No admissible evidence supports this property.",
            "verdict": spec.default_verdict,
        }

    return {
        "property": spec.name,
        "evidence": [item.detail for item in admissible],
        "rationale": "At least one admissible source supports the property.",
        "verdict": "yes",
    }


named_operator = PropertySpec(
    name="Named operator evidence comes from a 10-K or 10-Q filing",
    admissible_evidence_types={"verified_external_source"},
    forbidden_evidence_types={"final_answer", "reasoning_trace", "summary", "flawed_tool_call"},
    shortcut_rejections=["8-K press-release exhibit", "earnings recap", "news article"],
)

report = verify_property(evidence=[], spec=named_operator)
assert report["verdict"] == "no"
```

ADK's rubric-based final-response evaluator is the canonical evidence for this shape. It defines yes/no semantics, requires trusted evidence from procedurally sound tool calls, forbids deriving trusted evidence from the final answer, reasoning, summaries, interpretations, or flawed tool calls, and requires each property to output evidence, rationale, and verdict.

The Anthropic outcome-grader notebook is the shortcut-list variant. Its rubric forces the grader to require concrete evidence and reject lookalike substitutions, including an 8-K press-release exhibit when the requirement was a 10-K or 10-Q. The Pattern code above demands a 10-K or 10-Q filing; the rubric draws the line that makes an 8-K rejection possible.

## Determinism Move

Adversarial Frame constrains `self_review_bias` by inverting the default from accept-if-plausible to reject-unless-supported. Missing evidence becomes a `no`, not an invitation to rationalize.

It constrains `judge_subjectivity` by replacing tone instructions with admissibility rules and shortcut-rejection lists. The verifier no longer decides what counts as proof at runtime; the rubric says what counts.

## Observable Signal

Every Adversarial Frame report should include:

* admissible-evidence types for each property;
* forbidden-evidence types for each property;
* shortcut-rejection list;
* evidence collected per property;
* rationale per property;
* default verdict when evidence is missing;
* aggregate result with missing-evidence count.

A useful report shows the rejection surface:

```text
property: Named operator evidence comes from a 10-K or 10-Q filing
admissible: verified_external_source
forbidden: final_answer, reasoning_trace, summary, flawed_tool_call
shortcut_rejections: 8-K press-release exhibit, earnings recap, news article
evidence: []
rationale: No admissible evidence supports this property.
verdict: no
aggregate: fail
```

## Failure Modes

* **Tone Instruction:** The rubric says "be objective" or "be skeptical" without defining admissible evidence. Replace stance instructions with evidence rules.
* **Confirmatory Critic:** A role is named critic or adversary, but the prompt asks for constructive feedback and approval. Require evidence collection and a "why reject" field before any approval token can fire.
* **Improvement Loop Misclassified:** Evaluator-optimizer iteration is treated as adversarial verification. Keep improvement and disconfirmation as distinct patterns.
* **Hidden Shortcut:** The rubric lacks explicit rejection rules for common lookalikes. Enumerate shortcuts and make missing support fail by default.

## Use When

Use this pattern when:

* the verifier checks work produced by an LLM;
* false approvals are more costly than false rejections;
* the task has known shortcut paths or lookalike evidence;
* generation and verification share a model family or context;
* the rubric will be reused across many runs.

## Do Not Use When

Do not reach for Adversarial Frame when:

* the task is genuinely iterative and evaluator-optimizer is the desired loop;
* the output is exploratory and no one has defined what "wrong" means yet;
* strict admissibility would reject too many acceptable answers;
* a named **Comparator** or **Executable Analog** can decide the check directly;
* the right escalation is a calibrated **Judge Harness** around a subjective property.

## Evidence

* **Verification Design Principle 4:** The design doc names adversarial framing and cites SycEval's sycophancy finding as the reason confirmatory review is unsafe (AAAI 2025).
* **[ADK](https://github.com/google/adk-python) rubric-based final response quality:** The evidence summary records a direct pattern instance: trusted evidence must come from sound tool calls, forbidden evidence is listed, and missing support produces `no`.
* **Anthropic outcome grader:** The verification sweep records a shortcut-rejection rubric that rejects an 8-K press-release exhibit when the requirement was a 10-K or 10-Q.
* **[AutoGen](https://github.com/microsoft/autogen) Chainlit critic:** The antipattern cleanup sweep records a critic role whose prompt asks for constructive feedback and approval without required failure search.
* **Anthropic evaluator-optimizer:** The same sweep records a valid improvement loop that becomes a partial-fit antipattern only when it is mistaken for adversarial verification.

## Related Patterns

* **Judge Harness:** wraps the rubric with perturbation, repetition, calibration, and consistency checks.
* **Blind Oracle:** derives expected evidence without conditioning on the draft; Adversarial Frame defines admissibility for acceptance.
* **Cross-Family:** reduces shared blind spots when the adversarial rubric is judged by a different model family.
* **Comparator:** should replace Adversarial Frame when a named comparison operator can decide the check.
* **Constitution:** can require admissibility rules and default-no posture as part of the criteria contract.
