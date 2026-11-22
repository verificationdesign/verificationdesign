# When Evaluators of AI Agents Disagree: An Empirical Study of Native Scoring, LLM Judges, and Commit-Boundary Checks on tau2-bench

Reviewed: 2026-11-22
Reviewer: Codex draft; human review pending
Source: https://arxiv.org/abs/2611.14581
Evidence grade: C
Grade confidence: high

## Why It Matters

A stable transcript verdict can miss a state change that the transcript is supposed to help evaluate. The study distinguishes repeatability, task correctness, policy compliance, and commitment correctness. Its write check gives a concrete example of how to measure a specific boundary event alongside a broader evaluator.

## Method / Evidence

Read: arXiv v1 abstract and full paper (arXiv HTML, local text extraction, 2026-11-22).

- Population and evaluation. The study runs 50 airline and 40 retail tau2-bench tasks with gpt-4.1-mini and gpt-4.1 across cumulative gate configurations and repeated episodes. Native scoring uses the benchmark's gold state and required actions. A transcript judge runs with and without the domain policy. The deterministic boundary evaluator compares a gold write expectation with the logged commit.
- Disagreement and repeatability. Across all 2,160 episodes, the gpt-4.1-mini judge agrees with its repeat call on 98.2% and with native scoring on 56.2%. Of 1,007 episodes native scoring fails, the judge passes 929. These comparisons measure agreement between evaluators and calls.
- Human comparison. Two annotators label a stratified sample of 120 episodes on task correctness, policy compliance, and commitment correctness. Agreement proportions use sampling weights and the case counts here are unweighted. The boundary evaluator's weighted agreement on commitment is 0.708, compared with 0.575 for the main judge. It detects all 11 human-confirmed premature commitments but only 24 of the 53 commitment failures. For policy compliance the always-compliant rule scores 0.688, above all four main evaluators.
- Judge trade-off on that sample. The main gpt-4.1-mini configurations pass 11 of the 11 premature commitments. With full transcripts, it passes 10 without the policy and 11 with it. The stronger gpt-5.6 Sol judge passes 6 of the 11 without policy and fails 11 of 55 fully correct episodes. With policy it passes none of the 11 and fails 40 of 55 fully correct episodes.
- Gates. Across the 540 ungated episodes, the boundary evaluator labels 60 (11.1%) premature commitments. No tested gate effect survives Holm correction. The retail gpt-4.1 boundary success comparison has permutation p = 0.030 and adjusted p = 0.240. Trace analysis shows omitted order status and authentication evidence in the analyzed retail cases. The aggregate contribution of the digest defect was unmeasured.
- Checkability. The benchmark action list and successful WRITE tool events let another reader recompute the boundary labels. This checks whether an expected write occurred and requires a trusted expectation and sufficiently faithful tool logs. Write content, timing, and general policy compliance need additional evidence.
- Reproducibility signals. The paper reports a public Zenodo package with traces, code, prompts, model identifiers, labels, and adjudication records. The package and ancillary material were unopened for this review.
- Authority signals. The arXiv preprint has a sole author with academic and industry affiliations. The competing-interests statement discloses industry employment during the study and identifies the second annotator as a colleague at the same employer. These facts tune grade confidence while the evidence grade depends on the method and its scope.

## Limitations

The benchmark covers two domains with one model family serving as agent, simulated customer, gate verifier, and judge. Annotators were blinded to benchmark gold and evaluator verdicts but saw observed commit facts. The boundary evaluator's perfect detection of the 11 premature commitments is partly by construction because the human criterion and the boundary label both depend on a write where none was expected. Policy compliance was relabeled using an outcome-oriented definition and remained difficult for the annotators to agree on. The gate experiment measures the implementation with its digest defect, and the tests provide limited evidence on the effect of repaired checkpoints.

## Suggested Update

Disposition: fold-a-narrow-warning. For principles 3 and 6, log the actual commit and verify it against an explicit expectation, with separate checks for write content and timing. Validate the evidence delivered to the checkpoint as well. This narrows "A deterministic or automated gate can satisfy its surface metric while missing the failure class it is meant to detect." Hold claims that the measured gates reduce premature commits pending corroboration. Expand-on: yes. Seed topics: commit-boundary evaluation across model families; policy precondition evidence in verification gates; independent human annotation of state changes.

## Claims Needing Human Review

- Whether the triage description of observed forbidden writes adequately distinguishes the 11 human-confirmed cases from the ungated benchmark count and acknowledges the check's shared criterion with annotators.
- Whether the judge comparison should emphasize both error directions after adding policy, given the stronger model's false failures and the narrow evaluation sample.
- Whether the trace evidence warrants only a localized diagnosis. The paper sometimes describes the digest defect as the cause of the reversal, while the trace analysis establishes it only for the analyzed cases.
