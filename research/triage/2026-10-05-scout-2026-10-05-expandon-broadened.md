# Triage: Scout 2026-10-05 Broadened Expand-on Batch

Date: 2026-10-05
Source scout: research/scouts/scout-2026-10-05-expandon-broadened.md
Reviewer: Human + Codex

Limitation: Excerpt-only judgment with no external retrieval. This targeted run covers agent_authorization_testing and oversight_scheduling and tests whether broadened phrases hunt. Added phrases matched 17 agent_authorization_testing entries and 10 oversight_scheduling entries; original phrases matched 0 and 1 respectively. These are retrieval attributions, not evidence strength. The 17 already dispositioned entries are not re-judged for disposition; queue labels are assigned from excerpts. All 11 new entries have insufficient excerpts to assess methods, effectiveness, or generality. Confidence reflects that limitation. Promote recommends source review only.

Seed mapping: Retained entries are neighbors, with no established corroboration or challenge to any seed finding. Judgment-based seed assignment can differ from retrieval attribution.

## Candidate: OpenAgentFlow: Enabling System-Wide Safety Boundaries for Heterogeneous AI Agent Fleets

Source: https://arxiv.org/abs/2609.00015
Initial label: extends
Confidence: low

### Abstract Paraphrase

The authors frame shared environments containing agents, planners, tools, and backends as an action-governance problem.

### Key Findings

The excerpt locates the decision at commitment of a pending action; policy-state representation and enforcement results are cut off.

### Why It Might Matter

Check whether authorization covers the whole execution system. This is a reading-priority judgment, not a validated effectiveness claim.

### What Would Change In The Doc

Neighbors research/reviewed/2026-08-19-intent-governed-tool-authorization.md and research/reviewed/2026-08-19-fava-permission-graphs.md; seed: agent_authorization_testing; matched phrase: "policy enforcement point". No excerpt establishes corroboration or challenge. Source review could inform this question: Check whether authorization covers the whole execution system. No canonical change is made.

### Decision

Decision: promote

## Candidate: When Does Memory Help? A Cost-Aware Evaluation of Long-Term Memory in Tool-Using LLM Agents

Source: https://arxiv.org/abs/2609.05441
Initial label: operational technique
Confidence: low

### Abstract Paraphrase

The authors distinguish dialogue recall from memory that changes tool-using behavior.

### Key Findings

MERIT is introduced as a benchmark and harness for marginal memory utility; cost measurements and validation are truncated.

### Why It Might Matter

Evaluate memory through realized task behavior rather than recall scores. This is a reading-priority judgment, not a validated effectiveness claim.

### What Would Change In The Doc

Neighbors none of the four seed notes; seed: none; matched phrase: "spot-check". No excerpt establishes corroboration or challenge. Source review could inform this question: Evaluate memory through realized task behavior rather than recall scores. No canonical change is made.

### Decision

Decision: keep-in-triage

## Candidate: From Intent to Action: Benchmarking LLM Safety in Vehicle Voice Command Authorization

Source: https://arxiv.org/abs/2609.19630
Initial label: operational technique
Confidence: low

### Abstract Paraphrase

The authors describe authorization choices for vehicle voice requests before commands execute.

### Key Findings

The excerpt enumerates execute, refuse, clarify, confirm, defer, and emergency-response choices; benchmark construction and accuracy are not visible.

### Why It Might Matter

Assess authorization as a decision among context-dependent responses. This is a reading-priority judgment, not a validated effectiveness claim.

### What Would Change In The Doc

Neighbors research/reviewed/2026-08-19-intent-governed-tool-authorization.md; seed: agent_authorization_testing; matched phrase: "authorization policy". No excerpt establishes corroboration or challenge. Source review could inform this question: Assess authorization as a decision among context-dependent responses. No canonical change is made.

### Decision

Decision: promote

## Candidate: Auditing and Repairing LLM-as-Judge Failures in a Production Text-to-SQL Pipeline

Source: https://arxiv.org/abs/2609.30290
Initial label: challenges
Confidence: low

### Abstract Paraphrase

The authors audit a deployed text-to-SQL judge against two-author annotations.

### Key Findings

The excerpt reports Cohen's kappa of 0.04 on a disagreement-enriched sample and 0.42 on a uniform-random spot-check; the over-flagging statistic is cut off and repair results are unavailable.

### Why It Might Matter

Separate sampling choices when measuring judge agreement and review burden. This is a reading-priority judgment, not a validated effectiveness claim.

### What Would Change In The Doc

Neighbors research/reviewed/2026-06-30-automation-bias-overreliance.md; seed: oversight_scheduling; matched phrase: "spot-check". No excerpt establishes corroboration or challenge. Source review could inform this question: Separate sampling choices when measuring judge agreement and review burden. No canonical change is made.

### Decision

Decision: promote

## Candidate: PinSieve: Production Selective VLM Serving and a Governed Memory Flywheel for Enterprise Content-Quality Triage

Source: https://arxiv.org/abs/2608.24040
Initial label: operational technique
Confidence: low

### Abstract Paraphrase

The authors describe a bounded, observable selective VLM serving agent in a production content-quality pipeline.

### Key Findings

The agent handles the grey-zone slice left unresolved by an earlier component; audit protocol, review costs, and outcomes are truncated.

### Why It Might Matter

Inspect how unresolved cases are selected for further processing. This is a reading-priority judgment, not a validated effectiveness claim.

### What Would Change In The Doc

Neighbors research/reviewed/2026-08-19-nonuniformity-human-ai-coworking.md and research/reviewed/2026-06-30-automation-bias-overreliance.md; seed: oversight_scheduling; matched phrase: "audit sampling". No excerpt establishes corroboration or challenge. Source review could inform this question: Inspect how unresolved cases are selected for further processing. No canonical change is made.

### Decision

Decision: promote

## Deferred

- Not All Tokens Are Equal: Inflation-Aware Routing for Agentic LLM Systems ([arXiv:2608.13571](https://arxiv.org/abs/2608.13571)); label: narrows; Retry overhead separates per-token prices from whole-workflow costs. Neighbors none of the four seed notes, not corroboration or challenge; matched phrase: "escalation policy"; seed: none
- From Routing Signals to Selective Review: Visual regrounding in MoE VLMs ([arXiv:2609.38111](https://arxiv.org/abs/2609.38111)); label: narrows; VLMs can answer questions about absent target objects. Neighbors research/reviewed/2026-08-19-nonuniformity-human-ai-coworking.md and research/reviewed/2026-06-30-automation-bias-overreliance.md, not corroboration or challenge; matched phrase: "selective review"; seed: oversight_scheduling
- ServeGuard: Verifiable, Bounded-Residual Confinement of Operator-Invisible Channels Without Revealing the Certified Read Factor ([arXiv:2609.21515](https://arxiv.org/abs/2609.21515)); label: narrows; Opaque adapters can contain behavior in channels structurally invisible to a safety monitor. Neighbors none of the four seed notes, not corroboration or challenge; matched phrase: "monitoring budget"; seed: none

## Ignore

- SomaliBench Eval: Measuring English-to-Somali Refusal Gaps in Open-Weight Language Models ([arXiv:2605.25420](https://arxiv.org/abs/2605.25420)); The excerpt measures English versus Somali refusal behavior rather than oversight scheduling.
- When to Call an LLM: A Confidence-Gated Hybrid for Cost-Effective Emotion Recognition in Conversational AI ([arXiv:2609.17977](https://arxiv.org/abs/2609.17977)); The excerpt compares emotion-recognition deployment options under cost and latency constraints.
- SegTME-UNI2: A Foundation Model-Based Framework for Generalisable Multiclass Cell Segmentation and LLM-Driven Tumour Microenvironment Characterisation in Histopathology ([arXiv:2606.17702](https://arxiv.org/abs/2606.17702)); The excerpt describes histology segmentation and clinical reporting rather than agent-work verification.

## Batch accounting

Total: 28 = 17 already-handled + 3 ignore + 5 full-record + 3 deferred.

Per-label (all 28): challenges: 3; narrows: 11; extends: 3; operational technique: 7; ignore: 4.

Per-decision (full records): promote: 4; keep-in-triage: 1; keep-in-scout: 0; ignore: 0.

Per-seed (full records / Deferred): agent_authorization_testing: 2 / 0; oversight_scheduling: 2 / 1; none: 1 / 2.

Prune-watch: spot-check only: 2605.25420 off-topic for the two seeds; 2609.05441 on-topic for general verification but off-topic for the two seeds; 2602.13576 on-topic for general judge verification but off-topic for the two seeds (already handled); 2606.17702 off-topic; 2609.30290 on-topic as an oversight neighbor. Least privilege only: 2608.26699 off-topic; 2605.05868 and 2609.17648 on-topic authorization neighbors (all three already handled). 2609.33371 also matched action authorization, so is not a prune-watch-only hit.
