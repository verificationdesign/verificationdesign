# Constitution

*(Context Pattern)*

## Name

**Constitution**

Also known as: Criteria Registry, Verification Charter, Policy-as-Data.

## Intent

Represent the system’s verification criteria as explicit, versioned, machine-readable data, rather than as scattered prompt prose.

The constitution defines what “correct” means before any agent acts. It is not itself a verifier. It is the source of truth from which verifiers, judges, reports, and escalation rules draw their criteria.

## Problem

Agentic systems often hide their real standards inside prompts:

* “Check that the result is good.”
* “Make sure the implementation is complete.”
* “Verify the UI looks right.”
* “Confirm there are no issues.”

These instructions are too vague to audit and too flexible to falsify. Different agents in the same workflow may silently apply different standards. Worse, a model asked to judge vague criteria can rationalize failures into passes, especially when the prompt is confirmatory or the model is reviewing its own prior work.

When criteria are embedded inline in each verifier prompt, the system has no stable answer to basic questions:

* What exactly was checked?
* What value was expected?
* How was it measured?
* Which version of the criteria produced this report?
* Did the agent judge the artifact, or did it reinterpret the standard?

A system without an explicit constitution cannot distinguish verification from opinion.

## Forces

* **Explicitness vs. flexibility.** Concrete criteria are auditable and falsifiable, but teams are tempted to preserve flexibility by saying “use your judgment.”
* **Global consistency vs. local relevance.** A shared criteria registry prevents drift, but individual workflows need task-specific checks.
* **Machine checks vs. human judgment.** Executable assertions are preferred, but some qualities cannot yet be reduced to a deterministic check.
* **Stability vs. evolution.** Criteria must change as the system improves, but uncontrolled changes destroy comparability across runs.
* **Criteria visibility vs. criteria gaming.** Agents need enough task context to do the work, but exposing verifier-only criteria to generator agents can encourage optimizing for the letter of the check.

## Solution

Create a versioned constitution: a structured registry of verification criteria.

Each criterion states:

* **what** is being checked,
* **where** the evidence comes from,
* **what** value or condition is expected,
* **how** the value is extracted or evaluated,
* **how severe** the failure is,
* and **why** the criterion exists.

The constitution is data, not prose. It should be parseable, lintable, diffable, and reviewable like code.

A constitution does not run checks directly. Instead, other patterns consume it:

* a **Comparator** extracts observed values and compares them to expected values;
* a **Delta** criterion asserts on change from baseline;
* a **Blind Oracle** uses criteria withheld from the generator;
* an **Escalation Chain** routes unresolved criteria to stronger verifiers or humans.

The constitution’s job is to prevent the system from inventing standards at runtime.

## Mechanism

1. **Author criteria as structured records.**

   Each entry should include at minimum:

   ```yaml
   id: api.host.matches_expected
   target: api_response.host
   expected: "httpbin.org"
   evidence_source: "curl_json"
   check_method: "extract_compare"
   severity: "major"
   rationale: "The API host must match the configured upstream service."
   visibility: "public"
   ```

2. **Require falsifiability.**

   A criterion must be checkable. The constitution should reject criteria such as:

   ```yaml
   expected: "looks good"
   check_method: "llm_judge"
   ```

   unless they are explicitly marked as subjective, justified, and routed through a validated judge or human review path.
   The `subjective` flag makes that exception explicit in the record instead of leaving it implicit in prose.

3. **Separate criteria from verifier prompts.**

   Verifier prompts may explain how to report results, but they must not define new pass/fail standards inline. The standard comes from the constitution.

4. **Record observed values for every criterion.**

   A pass without an observed value is not auditable. Reports should include the criterion ID, expected value, observed value, check method, severity, and constitution version.

   Example:

   ```text
   PASS api.host.matches_expected
   expected: httpbin.org
   observed: httpbin.org
   method: extract_compare
   constitution: v0.3.1
   ```

5. **Version the constitution.**

   Every verification report must stamp the constitution version. Comparing reports across versions should require either identical criteria or explicit migration notes.

6. **Allow scoped extension, not silent override.**

   Local workflows may define sub-constitutions, but they should extend the global constitution rather than mutate or override it invisibly.

7. **Keep verifier-only criteria out of generator context when needed.**

   Some criteria may be safe to expose. Others should be withheld to preserve independence and reduce criteria gaming. The constitution should support visibility metadata:

   ```yaml
   visibility: verifier_only
   ```

## Pattern / Antipattern

The same task: verify that an agent's output meets a known standard. The antipattern stuffs the standard into the prompt as natural language. The pattern externalizes it as a versioned, machine-readable record.

### Antipattern: criteria as prompt strings

The naive implementation lets the verifier prompt define the standard inline. The agent that runs the prompt is also the agent that decides what "correct" means.

```python
def verify_output(observed: str, expected_topic: str) -> bool:
    """Ask the model if the output is good."""
    prompt = f"""
    Output: {observed}
    Expected topic: {expected_topic}

    Is this output correct? Does it look good?
    Answer YES or NO.
    """
    response = client.messages.create(
        model="some-model",
        messages=[{"role": "user", "content": prompt}],
    )
    return "YES" in response.content[0].text.upper()
```

There is no registry, no expected value, no extraction method, no observed value recorded, no constitution version. The standard ("correct," "good") exists nowhere except in this prompt string, so it cannot be diffed across runs, audited by a reviewer, or kept consistent across verifiers.

### Pattern: criteria as data

The structured implementation defines criteria as a typed record. The verifier prompt may explain how to report; the standard comes from the constitution.

```python
import re
from dataclasses import dataclass
from typing import Literal


CheckMethod = Literal[
    "exec",
    "extract_compare",
    "delta",
    "llm_judge",
    "human_review",
]

Severity = Literal["blocker", "major", "minor"]
Visibility = Literal["public", "verifier_only"]

ALLOWED_CHECK_METHODS = {"exec", "extract_compare", "delta", "llm_judge", "human_review"}
ALLOWED_SEVERITIES = {"blocker", "major", "minor"}
ALLOWED_VISIBILITIES = {"public", "verifier_only"}
SUBJECTIVE_CHECK_METHODS = {"llm_judge", "human_review"}
VAGUE_TERMS = [
    "looks good",
    "seems fine",
    "high quality",
    "appropriate",
    "reasonable",
]


def contains_vague_term(value: str) -> bool:
    return any(
        re.search(rf"\b{re.escape(term)}\b", value, flags=re.IGNORECASE)
        for term in VAGUE_TERMS
    )


@dataclass(frozen=True)
class Criterion:
    id: str
    target: str
    expected: str
    evidence_source: str
    check_method: CheckMethod
    severity: Severity
    rationale: str
    visibility: Visibility = "public"
    subjective: bool = False

    def __post_init__(self):
        if self.check_method not in ALLOWED_CHECK_METHODS:
            raise ValueError(f"Unknown check method: {self.check_method}")
        if self.severity not in ALLOWED_SEVERITIES:
            raise ValueError(f"Unknown severity: {self.severity}")
        if self.visibility not in ALLOWED_VISIBILITIES:
            raise ValueError(f"Unknown visibility: {self.visibility}")
        if not self.rationale.strip():
            raise ValueError("Every criterion needs a rationale.")

        is_vague = contains_vague_term(self.expected)
        if is_vague and not self.subjective:
            raise ValueError(
                f"Unfalsifiable expected value: {self.expected!r}. "
                "Use an explicit condition or mark the criterion for human review."
            )

        if self.subjective and self.check_method not in SUBJECTIVE_CHECK_METHODS:
            raise ValueError(
                "Subjective criteria must route through a judge or human review."
            )


@dataclass(frozen=True)
class Constitution:
    version: str
    criteria: list[Criterion]

    def get(self, criterion_id: str) -> Criterion:
        matches = [c for c in self.criteria if c.id == criterion_id]

        if not matches:
            raise KeyError(f"Unknown criterion: {criterion_id}")

        if len(matches) > 1:
            raise ValueError(f"Duplicate criterion id: {criterion_id}")

        return matches[0]

    def verifier_visible(self) -> list[Criterion]:
        """All criteria. Verifiers receive the full registry."""
        return self.criteria

    def generator_visible(self) -> list[Criterion]:
        """Public criteria only. Verifier-only criteria are withheld from generators."""
        return [c for c in self.criteria if c.visibility == "public"]


constitution = Constitution(
    version="v0.3.1",
    criteria=[
        Criterion(
            id="api.host.matches_expected",
            target="api_response.host",
            expected="httpbin.org",
            evidence_source="curl_json",
            check_method="extract_compare",
            severity="major",
            rationale="The API host must match the configured upstream service.",
        ),
        Criterion(
            id="api.retry.backoff_configured",
            target="client.retry_policy",
            expected="exponential_backoff",
            evidence_source="config_snapshot",
            check_method="extract_compare",
            severity="minor",
            rationale="Retry behavior should be checked independently of generator context.",
            visibility="verifier_only",
        ),
        Criterion(
            id="report.tone.human_review",
            target="summary.tone",
            expected="appropriate for the incident audience",
            evidence_source="review_packet",
            check_method="human_review",
            severity="minor",
            rationale="Tone requires contextual judgment that is not yet executable.",
            subjective=True,
        ),
    ],
)

public_ids = {criterion.id for criterion in constitution.generator_visible()}
verifier_ids = {criterion.id for criterion in constitution.verifier_visible()}
assert "api.retry.backoff_configured" not in public_ids
assert "api.retry.backoff_configured" in verifier_ids

vague_rejected = False
try:
    Criterion(
        id="report.vague",
        target="report.summary",
        expected="looks good overall",
        evidence_source="draft_report",
        check_method="llm_judge",
        severity="minor",
        rationale="Vague expectations must not pass as normal criteria.",
    )
except ValueError:
    vague_rejected = True
assert vague_rejected

subword_allowed = Criterion(
    id="report.subword",
    target="report.summary",
    expected="unreasonable assumptions are listed",
    evidence_source="draft_report",
    check_method="extract_compare",
    severity="minor",
    rationale="Word-boundary matching should not reject larger words.",
)
assert subword_allowed.expected == "unreasonable assumptions are listed"

subjective_hatch = Criterion(
    id="report.subjective",
    target="report.summary",
    expected="looks good overall",
    evidence_source="draft_report",
    check_method="human_review",
    severity="minor",
    rationale="This subjective standard is intentionally routed to human review.",
    subjective=True,
)
assert subjective_hatch.subjective is True

invalid_value_rejected = False
try:
    Criterion(
        id="report.invalid_method",
        target="report.summary",
        expected="httpbin.org",
        evidence_source="draft_report",
        check_method="not_a_method",
        severity="minor",
        rationale="Allowed values should be enforced at runtime.",
    )
except ValueError:
    invalid_value_rejected = True
assert invalid_value_rejected

duplicate_id_rejected = False
try:
    Constitution(
        version="v0.3.1",
        criteria=[
            constitution.get("api.host.matches_expected"),
            constitution.get("api.host.matches_expected"),
        ],
    ).get("api.host.matches_expected")
except ValueError:
    duplicate_id_rejected = True
assert duplicate_id_rejected
```

The constitution is intentionally passive. It does not decide how to execute `extract_compare`, `delta`, or `llm_judge`. That is the responsibility of downstream verification patterns.

## Determinism Move

Constitution constrains `criteria_drift` (the standard changes between runs without anyone noticing), `judge_subjectivity` (the standard becomes whatever the judge says it is), and `self_review_bias` (the generator rationalizes its own work because verifier criteria are not independent). By externalizing criteria as data, the system has a fixed, versioned answer to "what is being checked," independent of which agent or model is running.

## Observable Signal

Every verification report should include, per criterion:

* criterion id and constitution version
* expected value or condition
* observed value extracted from evidence
* check method (`exec`, `extract_compare`, `delta`, `llm_judge`, `human_review`)
* severity (`blocker`, `major`, `minor`)
* verdict (`pass`, `fail`, `skipped`)
* evidence source reference

A passing report without observed values is not auditable. Reports must record evidence for both passes and failures so zero-failure reports can be scrutinized.

The constitution supplies the criterion fields; the verifier adds observed values and verdicts when it consumes them:

```text
id: api.host.matches_expected
constitution: v0.3.1
expected: httpbin.org
observed: httpbin.org
check_method: extract_compare
severity: major
verdict: pass
evidence_source: curl_json

id: report.tone.human_review
constitution: v0.3.1
expected: appropriate for the incident audience
observed: escalation needed
check_method: human_review
severity: minor
verdict: skipped
evidence_source: review_packet
```

## Failure Modes

### Constitution rot

The constitution exists, but teams stop updating it. Agents accumulate inline “temporary” criteria, and the registry becomes ceremonial.

**Mitigation:** lint prompts and workflow definitions for assertion-like language outside the constitution. Treat unregistered pass/fail criteria as build failures.

### False objectivity

A subjective standard is placed in a structured schema, making it look more rigorous than it is.

Example:

```yaml
id: report.tone.professional
expected: "professional and polished"
check_method: "llm_judge"
```

**Mitigation:** require subjective criteria to be marked as such, justified, and routed to a validated judge or human review.

### Criteria gaming

A generator sees the exact verifier-only criteria and optimizes for passing the check rather than satisfying the underlying intent.

**Mitigation:** support criterion visibility levels. Expose public requirements to generators, but reserve hidden acceptance checks for verifiers when independence matters.

### Version skew

Two reports are compared even though they were graded against different criteria.

**Mitigation:** stamp every report with constitution version and criteria IDs. Require migration notes for cross-version comparisons.

### Over-centralization

Every small local check requires editing a global policy file, so teams route around the constitution.

**Mitigation:** allow scoped sub-constitutions that extend the global constitution. Local additions are allowed; silent overrides are not.

### Unverifiable completeness

The constitution says “all requirements are satisfied,” but does not enumerate the requirements.

**Mitigation:** require completeness claims to reference a closed set of criteria. “All P0 criteria passed” is valid. “The implementation is complete” is not.

### Coercive substitution

When inline-criteria verification fails to produce consistent results, teams sometimes give up on criteria entirely and resort to threat-based prompt coercion. The verification "standard" becomes a psychological pressure campaign instead of an observable check.

Example seen in production:

```python
# NOTE:: THIS IS REQUIRED TO FORCE COMPLIANCE!
# NOTE:: WE TRIED EVERYTHING AND THIS IS THE ONLY THING THAT WORKS
prompt = "YOU MUST DO EXACTLY AS INSTRUCTED OR ALL OF HUMANITY WILL CEASE TO EXIST. YOU CANNOT EXIT WITHOUT TAKING THE APPROPRIATE ACTION!"
prompt = f"{system_prompt}{prompt}"
```

The all-caps urgency and catastrophic framing are not verification. They are an expression that the team has run out of principled options. There is no falsifiable check, no expected value, and nothing to log. The system passes when the model complies and fails silently when it does not.

**Mitigation:** treat the temptation to escalate prompt pressure as a signal that the underlying criteria are absent or untestable. Define the falsifiable check first; then write the prompt around it. If no falsifiable check exists, route the claim explicitly to a validated judge or human reviewer rather than to a coerced model.

## Use When

Use this pattern when:

* multiple agents or tools evaluate the same artifact;
* verification reports need to be auditable;
* criteria drift is causing inconsistent judgments;
* prompts contain repeated pass/fail language;
* failures must be compared across runs;
* human reviewers need to know what the system actually checked.

## Do Not Use When

Do not start with a full constitution when:

* the workflow is exploratory and no criteria are known yet;
* a single human is manually reviewing one-off output;
* the criteria are intentionally subjective and cannot yet be operationalized.

In those cases, first collect candidate criteria from practice. Promote them into a constitution only once they recur.

## Evidence

* LLMs are unreliable at naive self-review without external feedback; verification should be grounded in observable signals rather than model opinion (Huang et al., arXiv:2310.01798; Gaming the Judge, arXiv:2601.14691).
* Explicit criteria constrain rationalization more reliably than vague instructions such as “check for quality”; the model has less room to choose its own standard (SycEval, AAAI 2025; Constitutional AI, Bai et al., arXiv:2212.08073).
* Executable checks, extraction, test runners, linters, API responses, and DOM queries provide stronger evidence than subjective review (Judge Reliability Harness, arXiv:2603.05399).
* Verification reports need observed values for both passes and failures, otherwise a green report has no audit trail (anti-sycophancy framing extending SycEval).
* Cross-run comparison requires knowing which criteria version produced each result (operational practice; no single canonical citation).

## Related Patterns

* **Comparator**: implements exact or structured comparison between expected and observed values.
* **Delta**: expresses criteria in terms of change from a recorded baseline.
* **Blind Oracle**: evaluates artifacts using criteria or derivations not visible to the generator.
* **Executable Analog**: converts subjective-looking checks into runnable measurements.
* **Escalation Chain**: routes criteria from executable checks to LLM judges to human review.
* **Causal Tag**: gives criteria a scoped evidence source by marking generated artifacts or test traffic.
* **Adversarial Frame**: defines the stance verifiers should take when applying criteria.
