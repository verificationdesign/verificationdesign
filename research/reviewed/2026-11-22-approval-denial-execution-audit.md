# Auditable Authorization for LLM Agents: Empirical Evidence Across Model, Harness, and Workflow Layers

Reviewed: 2026-11-22
Reviewer: Codex draft; human review pending
Source: https://arxiv.org/abs/2611.19237
Evidence grade: C
Grade confidence: medium

## Why It Matters

An approval checkpoint has two obligations. Denied effects must remain absent, and authorized work that remains feasible and eligible must finish within the declared horizon. Measuring both requires following the decision from call selection through dispatch to the resulting state. A recorded decision or successful refusal can coexist with unfinished authorized work.

## Method / Evidence

Read: arXiv v1 abstract and full paper (arXiv HTML, local text extraction, 2026-11-22).

- Model panel: the authors select a risk-directed panel of 100 Retail checkpoints with 90 target-action signatures across 50 customers. They pair Approve and Reject at each checkpoint for GPT-6.1-Sol, DeepSeek V4.1 Flash, and Claude Haiku 5.5. Across the resulting paired cases, 293/300 approvals complete and 0/300 Reject runs produce the denied effect. A separate approval-only expansion completes 3,232/3,300 episodes. Native state witnesses score effects independently of the model's final response.
- Exploratory prompt contrast: on GPT-6.1-Sol's matched 30-task subset, the original prompt completes 142/150 episodes and action-specific restatement completes 150/150. The task-level exact McNemar test has discordances of 0/3 and unadjusted p=.25. The counts support using restatement as a diagnostic probe. They provide limited evidence for a general intervention.
- Harness: combined parallel approvals in ADK 2.14.0 lose an approved branch in 3/3 tasks for each model. Sequential and separate parallel approvals each lose 0/3. On the tested CrewAI 1.15.37 restoration path, repeated cells built from 42 source proposals omit 336/672 approved effects and suppress the protected effect in all 672 Reject episodes. A bundled scheduling repair completes 672/672 approvals.
- Workflow: sequential exclusions take 100 purposively screened n8n sources to 67 terminal pairs, then 65 with a working Approve control, then 59 policy-comparable pairs. Reject produces the protected effect in 4 of those 59 despite a visible approval gate in each failing workflow.
- Checkability: paired replay holds the initial state and protected operation fixed and varies the decision. Native effect witnesses and ordered traces can independently check completion, denial, and the first recorded divergence. They cover the declared effects and horizon. Unobserved effects and behavior outside that horizon remain outside the result.
- Reproducibility signals: the paper describes an offline toolkit, manifests, and native witnesses. The paper text read for this review does not state whether code or data are released.
- Authority signals: the arXiv preprint lists university and independent researcher affiliations and gives no peer-reviewed acceptance. These facts tune confidence and do not move the grade.

## Limitations

Several experiments are described briefly, with thin design detail, and the figures were unreadable in the text extraction. The authors treat the selected cases and repeated cells as mechanism tests and explicitly exclude deployment prevalence interpretations. The banking transition provider rows use different protocols, which prevents a like-for-like comparison. The paired incompletions include reconfirmation after new information as well as clear omissions. The outcome must retain that distinction when assessing whether completion was warranted.

## Suggested Update

Disposition: fold-a-narrow-warning. For principles 3 and 6, pair denied-effect assertions with approved-completion assertions at the execution boundary. This narrows "A deterministic or automated gate can satisfy its surface metric while missing the failure class it is meant to detect." The selected replays support the coverage concern raised by the FAVA permission-graph and intent-governed tool authorization reviews. They establish that coverage gaps occur in these settings and leave their frequency across deployments open. Expand-on: no.

## Claims Needing Human Review

- Whether a shared operationally unfinished label preserves the distinction between eligible omissions and justified reconfirmation clearly enough.
- What the unexplained AI annotation in the scope section labels, and whether it affects any secondary result. The note relies on native effects.
- Whether the bundled restoration repair identifies the failing transition with enough precision for the proposed warning. The text gives limited evidence about individual repair components.
