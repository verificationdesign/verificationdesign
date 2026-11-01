# Stronger Judges Do Not See More: Deployment-Integrity Blindness in LLM Evaluation

Reviewed: 2026-11-01
Reviewer: Codex draft; human review pending
Source: https://arxiv.org/abs/2610.21135
Evidence grade: C
Grade confidence: medium

## Why It Matters

Behavioral acceptance does not identify the runtime that produced the accepted output. This paper separates output evaluation from deployment identity, making a useful distinction between checking task performance and checking whether the declared system was actually measured. The distinction matters when evaluation results are reused after deployment changes, including changes that leave the evaluated behavior intact.

## Method / Evidence

Read: arXiv v1 abstract and full paper (local text extraction, 2026-11-01).

- DIB-Bench evaluates 7,560 scored examples across six tamper types, three model pairs, and three seeds. Mean tamper acceptance rises from 88.6% under rule-based scoring to 89.3% under Qwen3-8B and 94.1% under GPT-5-nano. These are acceptance rates for the controlled altered deployments, not estimates of undetected changes in production.
- The manifest channel compares expected and observed per-component content hashes over canonical JSON. Main-study identity acceptance is 0.0% for tampered conditions because the controlled modifications affect declared, measured components. It observes identity differences rather than whether those differences are harmful.
- Coverage controls expose both directions of mismatch. In the Qwen2.5-7B instrument validation, seed 42, n=120 per condition, undeclared sampling and chat-template changes pass identity at 100% while changing 33.3% and 77.5% of behavior respectively. Benign prompt paraphrase and dependency patch changes fail identity while leaving behavior unchanged.
- Behavioral fingerprinting identifies the model component with 76.7% accuracy against 33.3% chance, but covers only one of six stack components. This is evidence for a useful partial observable, not full-stack identification.
- Checkability: the hash comparison is executable given trustworthy expected and observed manifests. The indistinguishability argument is also inspectable: identical output distributions cannot be distinguished by passive output-only sampling. Neither establishes that the observed manifest faithfully measures the actual execution. The paper uses software-level evidence, explicitly excludes forged manifests, and leaves hardware-rooted attestation outside its implementation; it assumes rather than establishes a trusted measurement path.
- Reproducibility signals: the paper describes models, benchmark anchors, inference settings, component-localized evidence, and artifact licenses. The paper text read for this review does not state whether code or data are released. No artifact was executed for this review.
- Authority signals: the arXiv manuscript lists University of Connecticut affiliations and no peer-reviewed venue acceptance. University affiliation tunes confidence and does not move the grade. The controlled experiments and argument warrant early-evidence status rather than a replication claim.

## Limitations

The primary tasks are synthetic and modifications are made to individual components. Multi-component changes and an adversary able to forge manifests are outside the tested scope. The manifest cannot cover components it neither declares nor measures, and hash inequality cannot classify an authorized benign update as harmful. Public benchmark anchors broaden task coverage but do not establish production attestation or frontier deployment coverage. The passive sampling argument does not establish the same bound for adaptive probing. These limits separate a valid observability warning from an endorsement of the proposed identity channel as a complete defense.

## Suggested Update

Disposition: fold-a-narrow-warning. For principles 1, 6, and 9, distinguish behavioral evidence from independently measured runtime identity, and require any identity claim to name its coverage and trusted measurement path. This would narrow the synthesis heading "9. Isolate Verification from Ambient State" by identifying an additional obligation when binding results to a deployment. The existence finding can support a scoped warning; the manifest implementation should not be promoted as complete attestation. Expand-on: yes. Seed topics: trusted runtime manifest measurement; deployment identity coverage audits; independent replication of output evaluation blindness.

## Claims Needing Human Review

- Confirm that the trusted-path wording accurately distinguishes an assumed honest observed manifest from production attestation.
- Review whether the claim that stronger evaluators accept more altered outputs should remain strictly tied to this evaluator ladder and task mix.
- Confirm grade C and medium confidence given controlled authorship of both modifications and identity instrumentation.
