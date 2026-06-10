# Judge Reliability Harness: Stress Testing the Reliability of LLM Judges

Reviewed: 2026-05-29
Reviewer: Human + Codex
Source: https://arxiv.org/abs/2603.05399
Evidence grade: B
Grade confidence: medium

## Why It Matters

Judge Reliability Harness is directly relevant to Principle 7 because it treats LLM judges as systems that need their own validation suite before they are trusted. It strengthens the doc's position that LLM-based verification should be used cautiously and paired with external, observable checks where possible.

## Method / Evidence

The paper presents an open-source library for constructing validation suites that stress-test LLM judges. Given a benchmark dataset and judge configuration, the harness generates tests for binary judgment accuracy and ordinal grading performance across free-response and agentic task formats. The authors evaluate four judges across four benchmarks spanning safety, persuasion, misuse, and agentic behavior, and report variation across models and perturbation types. The arXiv abstract states that no evaluated judge was uniformly reliable and that consistency issues appeared under formatting changes, paraphrasing, verbosity changes, and flipped ground-truth labels in LLM-produced responses.

## Limitations

The reviewed source was the arXiv abstract page, not a full paper or code audit. The reported results depend on the selected judges, benchmarks, perturbations, and judge configurations. This supports stress-testing and calibration of LLM judges, not a general rejection of all LLM-as-judge use.

## Suggested Update

Append a dated update note under Principle 7 stating that cross-family LLM judges should be validated with perturbation-based reliability tests before being treated as verification signals, especially for free-response and agentic task formats.

## Claims Needing Human Review

- Whether the evidence grade should stay B after reading the full paper and inspecting the harness code.
- Whether the canonical doc should add a separate section on judge calibration and perturbation testing.
- Whether the phrase "no judge uniformly reliable" should remain scoped to the paper's evaluated models and benchmarks.
