# Executable Analog

*(Verification Pattern)*

## Name

**Executable Analog**

Also known as: Mechanical Extraction, Tool-Mediated Verification, Objective Grounding.

## Intent

Translate a subjective, language-based verification step into a deterministic, programmatic execution step that yields a binary pass/fail signal independent of the agent's judgment.

## Problem

LLMs are vulnerable to sycophancy and hallucinated reasoning, especially when asked to self-correct or evaluate their own outputs. The most common anti-pattern in agentic design is the instruction: *"Review your work and ensure it is correct."* 

When an agent is asked to "verify the API is healthy" or "check if the host is visible on the page," it may read a text snapshot (like an accessibility tree or a JSON dump), infer that the desired state is present, and return a passing grade without committing to the observed value. The verification step inherits the biases and blind spots of the generation step.

Because naive self-review is unreliable without external feedback, verification steps that rely only on the model's interpretation of text should be treated as weak evidence.

## Forces

* **Semantic understanding vs. mechanical checks.** LLMs are useful for interpreting messy language, but they are weak evidence for strict pass/fail claims. Executable checks are narrower, but easier to audit.
* **Ease of prompting vs. effort of tooling.** It is much faster to write a prompt asking the model to "check the UI" than to write a headless browser evaluation script.
* **Confirmation bias.** Models are biased toward accepting confirmatory framing ("Does this look right?"), especially around their own prior work.

## Solution

Where possible, replace LLM judgment calls with runnable checks. Find the executable analog for the claim the agent is trying to verify.

Instead of asking the model to read an API response, give it a tool that executes `curl -sf` and assert on the exit code. Instead of passing a DOM snapshot to the model to ask if an element is visible, use `browser_evaluate` with a Javascript query selector and strictly compare the returned string. 

The strongest verification is grounded in something the system can **execute and observe**, not something the agent merely **reads and opines on**.

## Mechanism

1. **Identify the subjective check.** (e.g., *"Does the webpage show the success message?"*)
2. **Determine the extraction tool.** (e.g., Playwright `page.evaluate()`)
3. **Write the deterministic extractor.** (e.g., `() => document.querySelector('.success-toast')?.textContent`)
4. **Implement Extract-then-Compare.** Force the verification system to log the raw extracted value *before* any comparison happens, creating an auditable trail.

## Pattern / Antipattern

The same task: verify that a host name is visible on a rendered web page. The antipattern hands the rendered output to an LLM and asks for a judgment. The pattern executes a deterministic extraction and compares the result to a fixed expected value.

### Antipattern: LLM reads the snapshot and decides

The naive implementation captures a snapshot of the rendered page and asks the model whether the expected host is visible. The verifier's pass/fail comes from model interpretation of the snapshot, not from a comparison the system can audit.

```python
def verify_host_visible(snapshot: str, expected_host: str, model) -> bool:
    """Ask the model whether the host appears on the page."""
    prompt = (
        f"Here is the page snapshot:\n{snapshot}\n\n"
        f"Is the host {expected_host} visible on the page? Answer YES or NO."
    )
    response = model.complete(prompt)
    return "YES" in response.upper()
```

There is no extracted observed value, no recorded comparison, no audit trail. The snapshot may contain the host, or contain something that looks like the host, or omit it; the verifier cannot distinguish those cases on review. The same model that wrote the page would happily approve it.

### Pattern: extract mechanically, compare strictly, record both

The structured implementation forces a deterministic extraction first, prints the observed value, and only then compares. Failure paths are logged with the same audit fields as success paths so zero-failure reports can be scrutinized.

```python
from typing import Callable, Any


class BrowserStub:
    def evaluate(self, js: str) -> str:
        if "document.querySelector('.host')?.textContent" not in js:
            raise ValueError(f"unsupported selector query: {js}")
        return "httpbin.org"


browser = BrowserStub()


class ExecutableAnalog:
    """
    Wraps an executable check to ensure separation of extraction
    and judgment. Pass/fail comes from the comparison, not model opinion.
    """
    def __init__(self, check_id: str, extractor: Callable[[], Any], expected: Any):
        self.check_id = check_id
        self.extractor = extractor
        self.expected = expected

    def verify(self) -> dict:
        try:
            # 1. Mechanical extraction (no LLM involved)
            observed = self.extractor()

            # 2. Strict comparison
            passed = (observed == self.expected)

            # 3. Audit trail generation
            return {
                "check_id": self.check_id,
                "passed": passed,
                "expected": self.expected,
                "observed": observed,
                "error": None,
            }
        except Exception as e:
            return {
                "check_id": self.check_id,
                "passed": False,
                "expected": self.expected,
                "observed": None,
                "error": str(e),
            }


def get_host_from_dom():
    return browser.evaluate("document.querySelector('.host')?.textContent")


checker = ExecutableAnalog(
    check_id="api.host.visible",
    extractor=get_host_from_dom,
    expected="httpbin.org",
)
pass_report = checker.verify()

mismatch_report = ExecutableAnalog(
    check_id="api.host.visible",
    extractor=lambda: "example.com",
    expected="httpbin.org",
).verify()


def failing_extractor():
    raise RuntimeError("DOM query failed")


error_report = ExecutableAnalog(
    check_id="api.host.visible",
    extractor=failing_extractor,
    expected="httpbin.org",
).verify()

assert pass_report["passed"] is True and pass_report["observed"] == pass_report["expected"]
assert (
    mismatch_report["passed"] is False
    and mismatch_report["observed"] == "example.com"
    and mismatch_report["error"] is None
)
assert (
    error_report["passed"] is False
    and error_report["observed"] is None
    and isinstance(error_report["error"], str)
    and error_report["error"]
)
```

The extractor is a single executable boundary the system can replay. The comparison is a single line the system can diff. The report carries everything a reviewer needs to challenge the verdict without rerunning the test.

Anthropic-cookbook's text-to-SQL eval shows the same shape in a literal form: parse the SQL, execute it against SQLite, and assert on the returned rows. Aider's linter loop is the repair-loop version: run a narrow mechanical check, carry line-grounded failures back to the agent, and ask for a bounded fix.

## Determinism Move

Executable Analog constrains `self_review_bias` (the same agent that produced the artifact no longer judges whether it satisfies the check) and `judge_subjectivity` (the verdict comes from a deterministic equality on extracted values, not from a model's interpretation of rendered output). By forcing extract-then-compare instead of interpret-and-decide, the system loses the freedom to rationalize a coincidental pass.

## Observable Signal

Every report includes:

* `check_id`: the named check being run;
* `expected`: the value the executable analog is checking against;
* `observed`: the raw value returned by the extractor, before judgment;
* `passed`: the strict comparison result;
* `error`: the exception text when extraction fails, otherwise `None`.

A reviewer challenging the verdict reads observed, reads expected, and either agrees the comparison was sound or pins down which side was wrong. Zero-failure reports must still record observed values for every check; a green report with no observed values is not auditable.

```text
check_id: api.host.visible
expected: httpbin.org
observed: httpbin.org
passed: true
error: null

check_id: api.host.visible
expected: httpbin.org
observed: example.com
passed: false
error: null
```

## Failure Modes

* **Fixed Sleep over Polling:** If the executable analog relies on asynchronous state, developers often add `time.sleep(5)`. This flakes. Wrap executable analogs in a poll-with-timeout mechanism.
* **Brittle Selectors:** The executable extraction logic (like a regex or CSS selector) breaks due to minor, valid changes in the output, causing false negatives.
* **Over-delegation:** Letting the same agent write the executable analog on the fly. If the agent writes the test for its own code, it may write a tautological test that passes the bug.

## Use When

Use this pattern when:

* the claim being verified can be expressed as a deterministic check;
* the output has structure (DOM, JSON, exit code, log line) that can be queried;
* you can write a test rather than just describe one;
* the same check will run repeatedly (regression, CI, multi-agent loops);
* the verification trail needs to be auditable.

## Do Not Use When

Do not reach for an executable analog when:

* the property is genuinely subjective and has no programmatic surface (tone, readability, design taste);
* the extractor would be more brittle than the LLM judgment it replaces;
* the cost of writing the executable check exceeds the cost of one-off human review;
* the claim is exploratory and "good" is not yet defined.

When no executable analog exists, route the claim explicitly to a validated judge or human reviewer rather than to an inline LLM judgment.

## Evidence
* **Agent-as-a-Judge (ICML 2025):** Evaluators with agency (ability to run code) achieved ~90% agreement with human experts, vs ~70% for LLM-as-Judge. (arXiv:2410.10934)
* **LLMs Cannot Self-Correct (ICLR 2024):** The most widely replicated finding is that LLM performance degrades with naive self-correction without external execution feedback. (arXiv:2310.01798)

## Related Patterns
* **Comparator:** strict equality is the named comparison step in this example; Comparator is the broader family of operators for deciding whether observed satisfies expected.
* **Constitution:** an Executable Analog is how one codified rule becomes a runnable check instead of a prose instruction.
* **Blind Oracle:** Blind Oracle protects the expected value from draft contamination; Executable Analog is its executable specialization, the strongest form when the comparison can run as code.
* **Judge Harness:** when no executable analog exists, route the claim to a validated judge harness rather than an inline LLM judgment.
* **Admissibility Gate:** keeps the challenge independent of the producer, which reduces the risk that the agent writes a tautological check for its own work.
