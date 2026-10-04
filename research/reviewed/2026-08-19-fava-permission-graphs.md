# FAVA: Formal Authorization for Verified Agents with Evidence-Backed Permission Graphs

Reviewed: 2026-08-19
Reviewer: Codex draft; human review pending
Source: https://arxiv.org/abs/2607.27267
Evidence grade: C
Grade confidence: medium

## Why It Matters

FAVA separates probabilistic extraction of natural-language permissions from deterministic authorization over an explicit runtime graph. That boundary is relevant to verification because the final decision can expose a counterexample path, but only for the labels, dependencies, obligations, and effects represented in the graph.

## Method / Evidence

Read: arXiv v1 abstract and full paper.

- Decision point: immediately before an effectful action, a runtime gateway re-authorizes the current finite prefix graph. It allows the candidate action only when the SMT result and extracted risk posture permit it; a counterexample or sensitive, dangerous, or ambiguous posture blocks it.
- Decision evidence: an LLM-guided Permission IR supplies intents, assets, operations, obligations, allowances, prohibitions, and evidence spans. Deterministic lowering produces nodes and dependency edges with contextual labels, requested capabilities, timestamps, evidence ancestry, and trust provenance. The solver combines that graph with forbidden label-to-sink policies, trusted sanitizer specifications, observed prefix facts, and the candidate action's capability request.
- Across the aggregate evaluation population of 801 cases, FAVA made 725 compliant binary decisions and 76 noncompliant decisions, for 90.5% Decision Compliance Rate. The population combines 217 OctoBench cases, 359 OpenAgentSafety cases, 35 ActPlane public cases, and 190 ActPlane trace cases. This is binary decision accuracy, not a rate of prevented harmful executions.
- Per population, FAVA recorded 197/217 compliant decisions on OctoBench, 303/359 on OpenAgentSafety, 35/35 on ActPlane public, and 190/190 on ActPlane traces. The two 100% results apply to structured and labeled ActPlane populations, not to the aggregate dataset or unseen deployments.
- The paper reports 607 runtime policy checks. Median solver time was 0.845 ms and the 95th percentile was 1.580 ms over those checks; observed graphs contained 6 to 10 nodes. These timings exclude the upfront semantic extraction path, reported separately as an 18.9-second average on OctoBench.
- Checkability: yes, conditionally. Given a fixed permission graph, policy translation, sanitizer specification, and candidate capability, the finite SMT query and returned counterexample are independently executable. The mechanism does not verify that the LLM extracted every relevant label or obligation, that the graph matches runtime reality, or that all effects pass through the gateway.
- Reproducibility signals: the paper specifies a Python and Z3 prototype and benchmark composition. This review did not inspect or execute an implementation or dataset, so it does not establish independent reproduction of the reported numbers.
- Authority signals: this is a six-author, unrefereed preprint. Author count is an authority fact only; it tunes confidence and does not move the evidence grade or substitute for replication.

## Limitations

The formal result begins after semantic evidence has been lowered into the graph. Missed labels, obligations, dependencies, or sinks can therefore produce false negatives. Complete gateway mediation, capability-conformant backends, correct policy translation, and correct sanitizer specifications are trusted engineering assumptions rather than proved deployment properties. Shell execution is modeled as a coarse command sink, not syscall-level provenance. The 190-case trace population attaches benchmark-provided evidence directly to violating nodes, making it a labeled diagnostic rather than a test of zero-shot evidence discovery. This review did not independently replicate the study.

## Suggested Update

Disposition: fold-a-narrow-warning. The checkable SMT decision mechanism lowers the fold bar for a warning that formal authorization is only as complete as its evidence graph, policy translation, mediation boundary, and backend conformance. Canonical prose should recommend tests that delete or corrupt labels and dependency edges, bypass the gateway, and compare a counterexample with the realized effect. Hold the reported effectiveness and generalization claims pending independent reproduction. Expand-on: yes. Seed topics: permission-graph completeness testing; semantic extraction failures in formal agent authorization; independent replication of runtime SMT gateways.

2026-10-04 update: expand-on registered. Seed topics wired into research/scouts/config.json under agent_authorization_testing: permission-graph completeness, permission graph completeness, formal agent authorization, semantic extraction failures, runtime SMT gateways, SMT gateway replication, intent-certificate authorization, intent certificate authorization, request-to-effect bounds, request to effect bounds, complete-mediation audits, complete mediation audits, agent gateway evaluation. Disposition unchanged.

## Claims Needing Human Review

- Whether grade C is too generous without an artifact inspected in this review, despite the independently checkable solver formulation.
- Whether the aggregate DCR comparison is fair across baselines whose inputs or supported populations may differ.
- Whether the labeled ActPlane trace population should be excluded from any canonical summary of generalization.
