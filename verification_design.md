# Verification Design Principles

Reference document for building systems that guide agents through end-to-end verification. Based on published research in LLM self-correction, verification chains, and agent evaluation.

## The Core Finding

**LLMs cannot reliably self-correct their own reasoning without external feedback.**

This is the single most replicated finding across the literature (Huang et al., ICLR 2024 [arXiv:2310.01798](https://arxiv.org/abs/2310.01798); Kamoi et al., TACL 2024 [doi:10.1162/tacl_a_00713](https://direct.mit.edu/tacl/article/doi/10.1162/tacl_a_00713/125177/); ICLR 2025 self-verification study [openreview:4O0v4s3IzY](https://openreview.net/forum?id=4O0v4s3IzY)). Asking an agent to "review your work" is the most common and least effective verification pattern. Performance *degrades* with naive self-correction. The model changes correct answers to incorrect ones.

> **2026-05-30 Update**: Treat "self-correction" as a family of interventions, not a single capability. CorrectBench separates intrinsic, external, and fine-tuned correction, and reports that self-correction can help on some complex reasoning tasks while remaining strongly model- and task-dependent, efficiency-sensitive, and often competitive with a direct chain-of-thought baseline. The strongest warning in this doc applies to naive intrinsic self-review: the same model re-reading its own answer without new external information. Source: [arXiv:2510.16062](https://arxiv.org/abs/2510.16062)

> **2026-05-30 Update**: Self-Correction Bench offers a mechanism for weak intrinsic review: models can correct identical errors more reliably when the error is framed as external than when it is their own output. In the paper's controlled error-injection setup over 14 open-source non-reasoning models, this "self-correction blind spot" supports the practical rule to prefer independent reviewers or external verifiers; when self-review is unavoidable, force explicit reconsideration rather than a single-pass critique. Source: [arXiv:2507.02778](https://arxiv.org/abs/2507.02778)

The implication is absolute: every verification step in a system must be grounded in something the agent can **execute and observe**, not something it **reads and opines on**.

---

## Principles

### 1. External Signals Over Self-Review

Tests, builds, linters, type checkers, API responses, browser DOM extraction: binary pass/fail signals that don't depend on the agent's judgment. These are sycophancy-proof.

**Do**: `curl -sf http://api/health` and check the exit code.
**Don't**: "Review the API response and determine if it looks healthy."

**Do**: `browser_evaluate(() => document.querySelector('.host')?.textContent)` and compare the string.
**Don't**: `browser_snapshot` then "verify the host is visible."

The difference is mechanical extraction vs. subjective interpretation. Mechanical extraction is reliable. Subjective interpretation inherits every bias the model has.

> **Research**: Agent-as-a-Judge (ICML 2025) showed that giving evaluators agency (the ability to run code and check files) achieved ~90% agreement with human experts, vs. ~70% for LLM-as-Judge (reading and opining). [arXiv:2410.10934](https://arxiv.org/abs/2410.10934)

> **2026-05-30 Update**: An agent's chain-of-thought is not an external signal. Gaming the Judge shows that changing only the reasoning text while holding actions and observations fixed can substantially increase false-positive trajectory judgments, especially when the CoT fabricates progress. Treat CoT as an unverified claim stream: useful for hypotheses, but not evidence until checked against observed actions, tool outputs, and environment state. Source: [arXiv:2601.14691](https://arxiv.org/abs/2601.14691)

### 2. Independence Between Generation and Verification

If the verifier can see the original output, it copies the same errors. The verification step must NOT be conditioned on the draft. Force the agent to re-derive or independently check claims.

In a single-agent system, full independence is impossible; the agent shares a context window. Mitigations:

- **Extract-then-compare**: Structure verification as (a) extract the raw value, (b) print it, (c) compare to expected. This creates a paper trail and forces the agent to commit to an observed value before rationalizing.
- **Blind re-derivation**: Ask the agent to solve the same problem from scratch without referencing its prior answer, then compare.
- **Tool-mediated extraction**: Use programmatic tools (curl, browser_evaluate, jq) to extract values rather than having the agent interpret rendered output.

> **Research**: Chain-of-Verification (CoVe) found that the "factored + revise" variant, where verification questions are answered *without* conditioning on the draft, yields the best results. On biography generation, CoVe improved FACTSCORE from 55.9 to 71.4. The non-independent variant showed significantly less improvement. [arXiv:2309.11495](https://arxiv.org/abs/2309.11495)

### 3. Step-Level Checkpoints

Verify intermediate steps throughout the workflow, not just the final output. Step-level verification catches errors at the layer where they originate, before they compound through the pipeline.

For a multi-scenario system: verify after each scenario, not just at the end. For a code generation pipeline: check the design before implementation, check the implementation before testing, check the tests before the report.

> **Research**: Process Reward Models (PRMs) provide feedback at each step of a reasoning chain rather than only evaluating the final output. ThinkPRM outperformed LLM-as-Judge by 7.2% on ProcessBench. Step-level verification also enables better error localization: you know *which* step failed, not just that something failed. [arXiv:2504.16828](https://arxiv.org/abs/2504.16828)

> **2026-05-29 Update**: Tool-agent verification is becoming a step-level problem in its own right, not just an application of reasoning-chain PRMs. ToolPRMBench frames tool-use PRM evaluation around interaction history, a correct action, a plausible incorrect alternative, and tool metadata, with offline sampling for local single-step errors and online sampling for multi-step rollout failures. For systems, this supports checking tool choice, argument validity, and observed tool-state transitions at each action boundary rather than waiting for final task success. Source: [arXiv:2601.12294](https://arxiv.org/abs/2601.12294)

### 4. Adversarial Framing

"What could fail?" not "Does this look right?" Force the agent into a critical frame.

When a system asks "does this look correct?", the agent is biased toward saying yes, especially about its own prior output. Sycophancy rates of 58-78% across models mean that confirmatory framing produces unreliable results *by default*.

Techniques:
- Ask "what could be wrong?" rather than "is this correct?"
- Use directive framing: "find three problems with this output"
- Force the agent to argue the *opposite* position before concluding
- Structure assertions as falsifiable claims: "this value MUST equal X. If it doesn't, that's a FAIL, no exceptions"

The grading rules in a verification system should explicitly instruct:
- Never explain away a failure
- Never reinterpret an assertion to make it pass
- A green report with zero failures should be treated with suspicion
- Failures are the valuable output; they surface real problems

> **Research**: SycEval (AAAI 2025) measured 58.19% sycophancy overall, with "regressive sycophancy" (leading to incorrect answers) being a substantial portion. Model size does NOT reduce sycophancy: bigger models are not less sycophantic. RLHF training can exacerbate it by rewarding user satisfaction over correctness. [aaai:36598](https://ojs.aaai.org/index.php/AIES/article/download/36598/38736/40673) Northeastern University (Nov 2025) found LLMs "overcorrect their beliefs" when presented with user judgment.

### 5. Explicit Criteria

"No hardcoded values, all error paths handled, no TODOs remain" beats "check for quality."

Self-critique works when the criteria are externally defined, specific, and unambiguous. The model does not decide what is "good"; the criteria do. Vague instructions like "verify the output is correct" give the agent latitude to rationalize. Specific criteria constrain it.

Every assertion in a verification system should state:
- **What** is being checked (which field, which element, which value)
- **Expected** value or condition (exact match, range, presence/absence)
- **How** to check it (which tool, which command, which extraction method)

> **Research**: Constitutional AI (Anthropic) demonstrated that principle-based self-critique can work when the principles are clear, specific, and externally defined. The model does not decide what is "good"; the constitution does. The approach works best for clear violations (detectable criteria) and less well for nuanced quality judgments. [arXiv:2212.08073](https://arxiv.org/abs/2212.08073)

### 6. Executable Verification Is King

`run the tests` is the single most reliable verification step a system can include. Tests provide a binary, external signal: exactly what the self-correction research says is needed. Tests act as specifications, constraining the agent to correct behavior. The test suite does not care what the agent thinks.

For code-generating systems: TDD is the strongest verification pattern available. The system should either generate tests first or require tests as input.

For non-code systems: find the executable analog. Can you curl an endpoint? Run a linter? Execute a query? Parse structured output? Any tool that returns pass/fail without requiring interpretation is more reliable than agent judgment.

> **Research**: TDD teams released 32% more frequently; TDD produces 40-80% fewer bugs (Thoughtworks 2024). Reflexion (NeurIPS 2023) works because it uses *external* feedback (test output, environment signals). The reflection itself is not the magic; the external signal is. [arXiv:2303.11366](https://arxiv.org/abs/2303.11366)

> **2026-06-09 Update**: Executable checks inherit the validity of their oracle. An IRT-based audit of seven preference and multiple-choice benchmarks (20986 items, responses from 114 models) surfaced likely label errors, with its authors reporting 95% precision in the top 200 flagged items against consensus-plus-hand-inspection reference labels. The error sources are instructive for verification design: mechanical construction rules that mark answers correct for satisfying the letter of a format rather than the intent, upstream annotation errors inherited unchanged across downstream variants, and items with no defensible single answer. A test that does not care what the agent thinks is still confidently wrong when its expected value is wrong. Design implication: expected values, labels, and fixtures need their own audit path; "the check passed" is conditional on oracle validity. Source: [arXiv:2605.30504](https://arxiv.org/abs/2605.30504)

> **2026-06-13 Update**: A deterministic comparator can be reliable yet invalid when its oracle under-specifies correctness. In an extractive-QA setting, Ho et al. report that Exact Match and F1 had average correlations with human judgment of 0.220 and 0.404, while an LLM judge reached up to 0.85; they also discarded 39 of 200 sampled instances because the gold answer itself was wrong. The judge is not a free substitute for oracle audit: its own job-title answer correlation was 0.352, a blind spot tied to ambiguous multi-job answers. This strengthens the 2026-06-09 oracle-validity note: executable comparators and learned judges both need evidence that the target they compare against actually represents correctness. [arXiv:2504.11972](https://arxiv.org/abs/2504.11972)

### 7. Cross-Family Beats Self-Verification

If using LLM-based verification, a different model family is needed. Self-verification and intra-family verification are systematically biased toward accepting incorrect outputs. The same blind spots that caused the error also prevent detecting it.

For single-agent workflows, this means: lean on tooling rather than self-review. When you cannot use a different model, maximize the use of external tools and minimize the number of assertions that depend on the agent's own judgment.

| Condition | Verification Helps? |
|---|---|
| Cross-family verification (different model) | Yes, most effective |
| Self-verification (same model) | Often no, biased toward accepting own errors |
| Intra-family verification (same model family) | Marginal, shared biases reduce gain |
| Mathematical/logical tasks | Highest verifiability |
| Knowledge-heavy tasks | Lower verifiability |

> **Research**: A study of 37 models across 9 benchmarks found that self-verification increases compute cost while imperfect verifiers produce false positives, eliminate valid reasoning paths, and fail to select the right solution. "Significant performance collapse with self-critique" but "significant performance gains with sound external verification." [arXiv:2512.02304](https://arxiv.org/html/2512.02304), [openreview:4O0v4s3IzY](https://openreview.net/forum?id=4O0v4s3IzY)

> **2026-05-29 Update**: Cross-family LLM judges are not automatically reliable verification signals; they need their own validation harness. Judge Reliability Harness evaluates judge consistency and discrimination across free-response and agentic task formats, and its authors report that no evaluated judge was uniformly reliable across their benchmarks and perturbation types. For systems, this suggests treating LLM judges as calibrated instruments: use perturbation tests, report observed judge behavior, and prefer executable checks for claims that can be made verifiable. Source: [arXiv:2603.05399](https://arxiv.org/abs/2603.05399)

> **2026-05-30 Update**: Cross-family judging does not make chain-of-thought safe as a verification surface. Gaming the Judge reports that manipulation-aware prompts, rubric changes, and extra judge compute reduce but do not eliminate CoT manipulation, while removing CoT can reduce recall. The design implication is not "never show CoT"; it is to ground any CoT-derived judgment in action logs, tool results, and environment evidence, and to report the resulting precision/recall tradeoff. Source: [arXiv:2601.14691](https://arxiv.org/abs/2601.14691)

> **2026-06-09 Update**: "Debias the judge" is not a dependable fix. Reward Bias Substitution proves that under any audit-distribution scoring, even with oracle access to the true reward, successful mitigation, bias substitution, and overcorrection produce identical observables; single-axis fixes for length, sycophancy, or style can rotate optimization pressure onto correlated proxies instead of removing it. Empirically, a length penalty under GRPO compressed responses while driving the policy into overconfidence and lower free-form accuracy, and a published length-debiasing operator that zeroed reward-length correlation on the audit set reintroduced the bias under best-of-N selection on three of four reward models tested. The transfer to verification design: a debiased judge is only certified under the distribution the optimized system actually induces, with multiple bias features tracked at once, and a single-axis debiasing claim validated on a static audit set is an unverified claim. This strengthens the existing stance: prefer executable checks over patched judges. Source: [arXiv:2605.27996](https://arxiv.org/abs/2605.27996)

> **2026-06-09 Update**: Judge validation is becoming a measurement discipline. An Item Response Theory framework formalizes judge reliability in two ordered phases: intrinsic consistency first (stability of the judge's latent quality estimates under typo, line-break, and paraphrase perturbations, with explicit acceptance thresholds), then human alignment, which is only meaningful for judges that pass the consistency phase. Across seven judges, reliability varied sharply by task: summarization judging held up while dialogue understandability scoring fell well below the framework's reliability threshold. For harness design this sharpens the 2026-05-29 note: perturbation tests with stated thresholds come before any alignment claim, and validation is per task, not per judge. Source: [arXiv:2602.00521](https://arxiv.org/abs/2602.00521)

### 8. Simulate Debate

In a single-agent context, you can ask the agent to argue *against* its own output before concluding. This is more effective than asking "does this look right?" because it forces a critical frame.

The debate pattern: two agents argue opposing positions; a judge determines the winner. Competitive debate incentivizes truthful behavior because maintaining a consistent deceptive argument is harder than exposing falsehoods.

For single-agent systems, the practical translation is:
- After generating output, instruct the agent to "argue against this approach: what are three reasons it could be wrong?"
- Only after articulating the counterargument should the agent finalize
- This adds a small amount of compute cost but significantly reduces sycophantic acceptance

> **Research**: Scalable AI Safety via Doubly-Efficient Debate (2024) showed debate outperforms consultancy (one-sided advice) and direct QA under genuine information asymmetry. [openreview:MTvYflAH62](https://openreview.net/forum?id=MTvYflAH62) Multi-Agent Reflexion (Dec 2025) found that separating acting, diagnosing, critiquing, and aggregating into different agents improved HumanEval pass@1 from 76.4 to 82.6. [arXiv:2512.20845](https://arxiv.org/html/2512.20845)

### 9. Isolate Verification from Ambient State

Assertions must prove the system's actions caused the expected outcome, not that the environment happened to already contain matching data. Count-based assertions (`total_flows >= 5`) and existence checks (`a task with flow_count >= 3 exists`) pass trivially against a system with pre-existing data, proving nothing about the test traffic.

This is distinct from Principle 2 (independence between generation and verification). Principle 2 concerns the agent's context window; the verifier shouldn't be biased by having seen the generated output. This principle concerns the system's state; assertions shouldn't be satisfied by data the system didn't create.

Techniques:

- **Delta-based assertions**: Record baseline values before the agent acts (e.g., flow count before sending traffic). Assert on the change (`flow count increased by at least N`) rather than the absolute value. This is the most reliable pattern; it works regardless of what data already exists.
- **Tagged test data**: Include a unique identifier per run (e.g., a UUID query parameter, a distinctive header value) and filter assertions to only match tagged records. This lets the system identify its own traffic unambiguously.
- **Scoped queries**: If the API supports time-range or session-based filtering, scope queries to only return data created after the system started.
- **Avoid "at least N" assertions on shared state**: `total_flows >= 5` is unfalsifiable in a busy system. `total_flows increased by >= 5 since baseline` is a real check.

The LLM context makes state contamination worse than in traditional test automation. A deterministic test harness fails loudly when an assertion matches the wrong data by coincidence; the next assertion in the chain breaks. An agent is more likely to rationalize a coincidental pass as "the system is working" and move on, producing a green report that verified nothing.

> **Research**: State contamination across test runs is one of the most studied causes of flaky tests in software engineering. Google's analysis of test flakiness (Luo et al., FSE 2014) found that order-dependent and state-leaking tests account for a significant share of flaky failures. [acm:10.1145/2635868.2635920](https://dl.acm.org/doi/10.1145/2635868.2635920) In the agent context, the problem compounds: agents cannot distinguish "my action caused this state" from "this state already existed" without explicit before/after measurement.

---

## Anti-Patterns

### "Review your work"

The most common and least effective verification pattern. Without external feedback, performance *degrades* after self-correction. The agent is more likely to change a correct answer to an incorrect one than to catch a real error.

### `browser_snapshot` + "verify X is visible"

This is LLM-as-Judge applied to UI testing. The agent reads an accessibility tree and makes a judgment call. Research shows ~70% agreement with humans, meaning ~30% of assertions could be wrong. Use `browser_evaluate` for programmatic DOM extraction instead.

### Treating CoT as evidence

Reasoning traces are useful hypotheses, not proof. A verifier that accepts an agent's chain-of-thought as evidence can be manipulated by post-hoc rationalization or fabricated progress. Check CoT claims against actions, observations, tool outputs, and environment state.

### Confirmatory framing

"Is this correct?" biases the agent toward "yes." "Does this look right?" produces unreliable results. Always use adversarial framing or explicit pass/fail criteria.

### Fixed sleep instead of poll-with-timeout

`Wait 2 seconds` is a magic number. It will flake on slow systems and waste time on fast ones. Poll with timeout: retry the check every 500ms, fail after 10s.

### Filing bugs from verification output without human review

If a verification system auto-files issues, false-positive assertions create noise. Report failures; let the user decide what to file.

### Absolute assertions on shared state

`total_flows >= 5` is unfalsifiable in a system with existing data. It passes before the system even runs. Use delta-based assertions (`flow count increased by >= 5`) or tag test data with a unique identifier and filter to only match tagged records.

### Observed values only on failure

If the report only shows observed values when assertions fail, a passing report has no audit trail. Include observed values for ALL assertions so zero-failure reports can be scrutinized.

---

## Applying These Principles in Systems

When writing a verification system:

1. **Make every assertion executable.** If you can't express it as a tool call that returns a value, it's a judgment call, and judgment calls are unreliable.

2. **Extract-then-compare, never interpret-and-decide.** Structure: (a) run tool to extract raw value, (b) print observed value, (c) compare to expected. Never combine extraction and judgment into one step.

3. **Include observed values in all report entries.** `[x] API: host == httpbin.org (observed: httpbin.org)` provides an audit trail. `[x] API: host == httpbin.org` does not.

4. **Poll, don't sleep.** Replace `Wait N seconds` with `Poll every Xms, timeout after Ys`.

5. **Add negative test cases.** Happy-path-only verification misses error-path bugs. Include at least one scenario that tests "does the wrong thing NOT happen?"

6. **Separate verification from action.** A verification system should verify and report. Side effects (filing bugs, modifying state) belong in separate steps under human control.

7. **Grade strictly by default.** Include explicit anti-sycophancy rules: never explain away a failure, never reinterpret assertions, treat zero-failure reports with suspicion.

8. **Assert on deltas, not absolutes.** Record baseline state before the agent acts. Assert that values *changed by* the expected amount, not that they *equal* a threshold. `total_flows >= 5` is unfalsifiable in a busy system; `total_flows increased by >= 5` is a real check.

---

## References

| Topic | Paper | Link |
|---|---|---|
| Chain-of-Verification | Dhuliawala et al., ACL 2024 | [arXiv:2309.11495](https://arxiv.org/abs/2309.11495) |
| Reflexion | Shinn et al., NeurIPS 2023 | [arXiv:2303.11366](https://arxiv.org/abs/2303.11366) |
| LLMs Cannot Self-Correct | Huang et al., ICLR 2024 | [arXiv:2310.01798](https://arxiv.org/abs/2310.01798) |
| When Can LLMs Correct Mistakes? | Kamoi et al., TACL 2024 | [doi:10.1162/tacl_a_00713](https://direct.mit.edu/tacl/article/doi/10.1162/tacl_a_00713/125177/) |
| CorrectBench | Tie et al., NeurIPS 2025 Datasets & Benchmarks | [arXiv:2510.16062](https://arxiv.org/abs/2510.16062) |
| Self-Correction Bench | Jul 2025 | [arXiv:2507.02778](https://arxiv.org/abs/2507.02778) |
| When Does Verification Pay Off? | Dec 2025 | [arXiv:2512.02304](https://arxiv.org/html/2512.02304) |
| Self-Verification Limitations | ICLR 2025 | [openreview:4O0v4s3IzY](https://openreview.net/forum?id=4O0v4s3IzY) |
| Judge Reliability Harness | Dev et al., ICLR 2026 workshop | [arXiv:2603.05399](https://arxiv.org/abs/2603.05399) |
| Gaming the Judge | Khalifa et al., Jan 2026 | [arXiv:2601.14691](https://arxiv.org/abs/2601.14691) |
| Reward Bias Substitution | Lamparth et al., May 2026 | [arXiv:2605.27996](https://arxiv.org/abs/2605.27996) |
| Benchmark Label Auditing (IRT) | Land and Bikel, May 2026 | [arXiv:2605.30504](https://arxiv.org/abs/2605.30504) |
| LLM-as-a-Judge for Extractive QA | Ho et al., Apr 2025 | [arXiv:2504.11972](https://arxiv.org/abs/2504.11972) |
| Judge Reliability via IRT | Choi et al., Jan 2026 | [arXiv:2602.00521](https://arxiv.org/abs/2602.00521) |
| Agent-as-a-Judge | ICML 2025 | [arXiv:2410.10934](https://arxiv.org/abs/2410.10934) |
| ThinkPRM | Apr 2025 | [arXiv:2504.16828](https://arxiv.org/abs/2504.16828) |
| ToolPRMBench | Li et al., Jan 2026 | [arXiv:2601.12294](https://arxiv.org/abs/2601.12294) |
| Constitutional AI | Bai et al., Anthropic | [arXiv:2212.08073](https://arxiv.org/abs/2212.08073) |
| Multi-Agent Reflexion | Dec 2025 | [arXiv:2512.20845](https://arxiv.org/html/2512.20845) |
| SycEval | AAAI 2025 | [aaai:36598](https://ojs.aaai.org/index.php/AIES/article/download/36598/38736/40673) |
| Doubly-Efficient Debate | 2024 | [openreview:MTvYflAH62](https://openreview.net/forum?id=MTvYflAH62) |
| Test Flakiness (state contamination) | Luo et al., FSE 2014 | [acm:10.1145/2635868.2635920](https://dl.acm.org/doi/10.1145/2635868.2635920) |
