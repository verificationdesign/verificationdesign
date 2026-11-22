# Done Is Not Correct: Measuring Silent Failures and Self-Verification Calibration When LLM Agents Take CAD Actions

Reviewed: 2026-11-22
Reviewer: Codex draft; human review pending
Source: https://arxiv.org/abs/2611.10063
Evidence grade: C
Grade confidence: medium

## Why It Matters

An artifact can build successfully and still violate the requirements attached to a completion claim. The CAD benchmark pairs those claims with independent measurements of the final geometry. Its grader audit also shows how omitted checks and ambiguous requirements can change the measured failure rate.

## Method / Evidence

Read: arXiv v1 abstract and full paper (arXiv HTML, local text extraction, 2026-11-22).

- Population and design. The primary study uses 13 tasks with 122 checks and 156 attempts per condition across Claude Haiku, Claude Sonnet, DeepSeek, and Qwen. It compares single-shot generation, tool use with measurements of the final revision required before accepting a completion claim, and a planner-coder-checker pipeline. The hardened grader checks measurable properties of the solid against task-specific tolerances.
- Silent failures and claim precision. A silent failure requires a valid solid, an explicit claim, and a failed semantic check. As shares of all primary attempts in each condition, silent failures are 22/156 (14.1%) single-shot, 5/156 (3.2%) with enforced tool use, and 4/156 (2.6%) with the checker. Among valid claimed parts the corresponding figures are 22/120 (18.3%), 5/126 (4.0%), and 4/89 (4.5%). Claim precision measures pass given a claim and is reported as 64.1%, 96.0%, and 95.5%, respectively. The paper gives percentages for precision and does not print the corresponding pass-over-claim fractions. The checker claims on 57.1% of attempts and reaches 61.5% task success, compared with 64.1% for single-shot and 77.6% for enforced tool use. The two high-precision conditions thus differ in overall task success.
- Claim contract ablation. With the same measurement feedback, the legacy arm has 14 silent failures in 156 attempts against 5 in the fixed arm. The unpaired Fisher test gives p = 0.056. The larger reported contrast is in claim precision, 67.6% versus 96.0%. Two legacy arms ran three months later, with the Sonnet arm using a different gateway, so the comparison also carries time and routing differences.
- Grader audit. Of the 31 silent failures in the primary population, 13 come from one ambiguously specified task. Outside that task the blind expert audit overturns 3 of the remaining 18 silent failures. Separately, hardening the oracle changes 18 of 519 stored verdicts from pass to fail and none in the reverse direction. It exposes 17 of the 48 silent failures in that regraded corpus, which includes original-protocol and exploratory runs.
- Checkability. Regrade final solids using the frozen specifications, kernel measurements, and published bands. Check harness enforcement separately by comparing accepted claims with the measurement record for the final code. Those checks can establish measured compliance and measurement delivery. Actual review by the model, omitted requirements, manufacturability, and intended meaning need separate evidence.
- Reproducibility signals. The paper reports released specifications, reference solutions, harness and grader code, per-attempt records, fixed-protocol and ablation transcripts, and expert audit records. The GitHub and Zenodo artifacts were unopened for this review.
- Authority signals. The arXiv preprint lists industry, university, and independent affiliations. A co-author with CAD practice performed the expert audit. These facts tune grade confidence while the evidence grade depends on the method and its scope.

## Limitations

The tool-use protocol and oracle both changed after a mid-study audit. The plan was unregistered and first committed with the results. The sample covers a small set of mechanical parts, with 39 attempts per model and condition. The condition contrast uses uncontrolled decoding, and the architecture comparison changes more than the claim contract. The single expert rater was a co-author who was blinded to grader verdicts. The ambiguous specification accounts for a large share of primary silent failures and demonstrates that deterministic measurement still depends on how the requirement was translated.

## Suggested Update

Disposition: fold-a-narrow-warning. For principles 5 and 6, verify completion claims against measurements of the final artifact and test the checker against known disagreements or independently reviewed outputs. The regrade narrows "Executable benchmark checks can pass against erroneous labels or construction rules that miss intended correctness." Hold the attribution of the improvement to the claim contract pending independent comparison with concurrent arms and equivalent routing. Expand-on: yes. Seed topics: independent audits of artifact graders; claim calibration under measured feedback; concurrent claim-contract ablation.

## Claims Needing Human Review

- The triage paraphrase credits the loop with the reduction. The ablation's silent-failure comparison is inconclusive at the conventional threshold, and the stronger claim-precision contrast still has timing and routing confounds.
- The paper describes four vendors while its model identifiers list two Claude variants from Anthropic plus DeepSeek and Qwen. Confirm the intended meaning of vendor.
- The claim-precision fractions are absent from the paper text. Preserve the printed percentages and distinguish the valid-claimed conditional rates from precision before folding.
- Confirm the scope of the audit interpretation. Excluding the ambiguous task changes the population, and the single rater's overrides do not establish universal error bounds.
