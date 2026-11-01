# Local Allow, Global Deny: Why Per-Action Authorization Does Not Compose in LLM Agents

Reviewed: 2026-11-01
Reviewer: Codex draft; human review pending
Source: https://arxiv.org/abs/2610.27620
Evidence grade: C
Grade confidence: high

## Why It Matters

An authorization monitor can make correct decisions about individual actions without observing the evidence needed to judge a relational policy. The paper distinguishes missing runtime state from a stronger limitation: some purpose restrictions concern how outputs vary across executions under matched authorized inputs. The verification requirement is to state the policy class, trusted abstraction, and observation scope before claiming authorization coverage.

## Method / Evidence

Read: arXiv v1 abstract and full paper (local text extraction, 2026-11-01).

- Policy class: purpose is modeled as declassification-based noninterference. Executions agreeing on public inputs and the purpose-authorized view of private context must agree on the policy-relevant output abstraction. This is a 2-safety hyperproperty. Its nontrivial relational character requires residual disclosure freedom: admissible executions with the same authorized view can still differ in abstracted output. For the combined global policy, those witnesses must remain inside the locally authorized trace set. A collapsing abstraction makes the condition trivial.
- Exact impossibility scope: every singleton trace set satisfies this relational condition. A per-trace monitor with no false alarms for that condition therefore detects no violations of it. For stochastic agents, the separate distributional result excludes nondeclassified context, the full conditional distribution, and cross-context samples from the monitor's observation. Over all stochastic agents, a single such observation cannot decide conditional independence soundly and completely. Cross-execution sampling supplies relational evidence, but no finite sample provides universal certainty about arbitrary distributional independence.
- Mechanical validation: the symbolic implementation and exhaustive oracle agree on all 72 profile-by-class cells. This checks soundness, bounded completeness, and minimality within the supplied finite models. The strongest surveyed single-execution profile covers seven of eight classes, with explicit labeled flow covered conservatively; the matrix assigns capabilities from published designs rather than executing those guardrail implementations.
- Judge headline: nine judges evaluate ten templates with three repetitions, yielding 30 scenario-repetitions per model and condition. Eight block the relational witness in 0/30 per-action views; Kimi-K2.6 blocks it in 3/30. With paired executions, eight judges detect it in 30/30 and Llama-4-Maverick in 17/30. All detect the overt single-trace control in 30/30. Observation access and reliable judgment remain distinct requirements.
- Narrowing result: the live Qwen3-30B consent-composition task records 22/60 failures without a guard, 20/60 with intent closure, and 0/60 with composition-aware monitoring. That catchable single-execution class is not the relational impossibility class. Gemma-4 records 0/60 throughout. The separate Claude Sonnet 4.6 offline relational audit observes no failures over 80 cases, with an upper bound of 3.7%; monitor blindness does not establish that every agent violates the policy.
- Checkability: the singleton argument and finite-model differential checks are independently inspectable mechanisms. They do not validate the chosen policy semantics, deployment instrumentation, or model behavior outside the tested population. No concrete bypass construction is needed to state what evidence the monitor lacks.
- Reproducibility signals: the paper states that its artifact, documentation, logs, raw judge responses, and settings are released. Hosted judge routing did not pin the serving provider. No artifact was executed for this review.
- Authority signals: the text states acceptance in IEEE TPS 2026 proceedings and lists university affiliations. These facts tune confidence only and do not move the grade or replace independent corroboration.

## Limitations

The formal purpose semantics is declassification-based rather than a general account of user intent. The statistical theorem is model-free over all stochastic agents, while deployment-specific restrictions may supply additional evidence. Symbolic validation uses small models and is not a scalability study or a proof of implementation correctness. The live-agent tasks are synthetic, and the judge campaign measures judgments rather than autonomous agent behavior. The policy-relevant output abstraction also matters: an initial offline positive was removed as a parser artifact.

## Suggested Update

Disposition: fold-a-narrow-warning. For principle 9 and the authorization notes, state the policy class and observation scope before interpreting gateway coverage. This challenges the completeness boundary in `2026-08-19-fava-permission-graphs.md` and `2026-08-19-intent-governed-tool-authorization.md`, and narrows the synthesis claim "Agent authorization can separate probabilistic interpretation or action proposal from a deterministic runtime decision, conditional on the completeness of the decision evidence and mediation boundary." A correct deterministic decision cannot certify an unobserved relational predicate. This does not invalidate either gateway's stated single-execution guarantees. Hold general monitoring-effectiveness claims pending replication. Expand-on: yes. Seed topics: relational policy evidence for agent authorization; deployment audits of monitor observation scope; independent replication of authorization composition checks.

## Claims Needing Human Review

- Whether the proposed connection to principle 9 and the existing authorization synthesis claim captures the formal limitation without broadening it to all purpose policies.
- Whether grade C remains appropriate for the limited empirical coverage despite stated conference acceptance and an inspectable proof mechanism.
- Whether the stochastic observation exclusions and locally authorized residual-freedom assumption are stated narrowly enough for canonical reuse.
