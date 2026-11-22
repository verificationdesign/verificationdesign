# Does the Judge See What the Evaluation Requires? Input Assurance for LLM Agent Evaluation

Reviewed: 2026-11-22
Reviewer: Codex draft; human review pending
Source: https://arxiv.org/abs/2611.02676
Evidence grade: C
Grade confidence: high

## Why It Matters

A judge evaluates a rendering of an agent's run. If the renderer drops required action evidence, the evaluation can return a reproducible score for an incomplete input. The paper separates fidelity to the source record, coverage of the validation criteria, enforcement of failed checks, and identity of the bytes consumed at judgment.

## Method / Evidence

Read: arXiv v1 abstract and full paper (arXiv HTML, local text extraction, 2026-11-22).

- Design and observed omission. The study reused 30 AgentProcessBench trajectories, 14 from BFCL and 16 from tau2. Each contributed an erroneous target and an earlier correct comparison target. The original packets matched their recorded hashes while omitting every structured call. Of 60 targets, 53 appeared blank, including 26 of 30 error targets and 27 of 30 comparison targets. The rest had message text and also lost their calls.
- Judge contrast. Prefix and full-trajectory packets were compared before and after restoring calls throughout the packets. Each cell held 30 targets, with two draws per packet and a consensus flag requiring both draws to flag an error. Under J0, error-prefix flags rose from 2 to 20. The difference in differences between full and prefix flag counts for error and comparison targets fell from 13 to 2. The paper reports a reduction of 11, or 0.37 per trajectory, with a 95% cluster-bootstrap interval of 0.17 to 0.53 per trajectory. Original-packet contrasts for the other configurations were 0, 5, 4 and -1. Those configurations sometimes flagged blank error and correct targets.
- Checker coverage. Across 34 shared cases from 38 constructed mutations, the inline checker missed two and the disk checker missed one. Both accepted the same unmatched result. Neither checker inspected the staged copies, and the disk checker's hash comparison used the same archived text for its actual and expected values.
- Integration and control results. A recording stub read a failed build's packet and a changed staged copy in separate constructed integration tests. In the 19 constructed fault cases, the cumulative controls stopped 18 before any packet read. Failure enforcement stopped 11, dispatch checks refused four more, and reverse matching stopped three. The remaining stale script was unused under every condition.
- Checkability. A source-to-packet comparison can verify preservation of required fields, targeted negative fixtures can test each checker obligation, and a recording stub can establish which bytes reach the point of use. A hash match establishes byte identity against a reference. Content coverage requires an independent comparison with the source and the evaluation contract.
- Reproducibility signals. The paper lists study plans, observations, source code and scripts for reconstruction, replay and reanalysis in an anonymized repository. The repository was not opened.
- Authority signals. The arXiv preprint lists university and public-research affiliations and states no peer-reviewed acceptance. These facts tune confidence. The grade reflects the inspectable study and its scope.

## Limitations

The authors selected the pipeline after finding the omission. They developed the controls on the same cohort and tested them on constructed cases with knowledge of the implementation. The configurations varied jointly in model, delivery, prompt and serving conditions. Restored packets still omitted result identifiers and some tool definitions. Supplementary tables were unavailable, so results attributed to them here come from the main text. The reported interval holds the recorded verdicts fixed.

## Suggested Update

Disposition: fold-a-narrow-warning. For principles 5, 6 and 9, this case narrows "A deterministic or automated gate can satisfy its surface metric while missing the failure class it is meant to detect." Require a source-to-rendering test for criterion-required fields and verify that the validation result and checked input reach the actual judge entry point. The case supports the warning for evaluation pipelines with a separate rendering path. Transfer and the size of any effect on judge scores require corroboration. Expand-on: no.

## Claims Needing Human Review

- The triage label narrows fits. Its shorthand should distinguish omission of all structured calls from the 53 steps that were visibly blank.
- Check the interpretation of the J0 contrast as a configuration-specific result and assess whether the proposed warning should mention abstentions separately from negative judgments.
- Confirm the provenance distinction between the diagnostic corpus and the two point-of-use violations observed with a recording stub.
