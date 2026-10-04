# Intent-Governed Tool Authorization for AI Agents

Reviewed: 2026-08-19
Reviewer: Codex draft; human review pending
Source: https://arxiv.org/abs/2606.22916
Evidence grade: C
Grade confidence: medium

## Why It Matters

The paper treats the user's current request as a narrower authorization boundary inside an integration's broader static permissions. Its useful verification move is architectural: an untrusted model proposes an action, while a server-side gateway decides whether the tool, payload, and expected effect remain within a short-lived certificate derived from trusted request content.

## Method / Evidence

Read: arXiv v3 abstract and full paper.

- Decision point: IGAC decides twice. It filters the visible tool manifest before planning, then checks a proposed tool call and payload before the existing action pipeline may draft, preflight, or execute it.
- Decision evidence: the gateway consumes static integration policy plus a bound intent certificate containing the trusted request hash, actor and session bindings, allowed and denied intent classes, resource and effect predicates, confidence, maximum routing outcome, expiry, classifier provenance, and policy and tool-registry versions. It also consumes the proposed tool, payload, and adapter-declared effect interpretation.
- The unconditional mechanism is monotone narrowing: session policy cannot reveal a tool hidden by static policy. Request confinement is conditional on certificate fidelity, conservative effect bounds, trusted-message separation, complete mediation, and a correct gateway.
- The evaluation includes 176 author-generated deterministic runtime instances. It also includes 306 end-to-end model-task runtime trials, formed from 34 synthetic tasks, 3 repeats per task, and 3 model populations, plus 36 transfer-subset trials, formed from 12 locally authored benchmark-shaped tasks and 3 model populations.
- In the 176-instance deterministic runtime comparison, reference-certificate IGAC reduced the paper's archived composite exposure-or-path indicator from 1.0000 under OpenPort-only to 0. This is a comparison on the authored deterministic suite, not an isolated production-effect estimate.
- In the 306 end-to-end trials, each model row contains 34 synthetic tasks repeated 3 times. Of those 102 trials per model, 66 are attack-or-ambiguous trials, formed from 22 such tasks repeated 3 times. Unsafe accepted authority ranged from 6/66 (0.0909, which reduces to 1/11) to 18/66 (0.2727, which reduces to 3/11). The eleven in those reduced fractions is not an eleven-item evaluation population. Across all 198 attack-or-ambiguous trials, the combined IGAC-OpenPort path accepted 40 unsafe drafts and completed 0 unsafe effects; every residual accepted-authority case was a non-executed draft.
- A trace-backed counterfactual re-scored the collected model-runtime traces rather than replaying models or actions. Adding a strict bound validator and normalized gate reduced unsafe accepted authority from 40/198 (0.2020) to 0, while governed benign artifacts fell from 36/108 (0.3333) to 15/108 (0.1389). This is the paper's stated substantial utility cost.
- In a separate classifier pilot, each of 3 open-weight model populations processed 55 synthetic certificate tasks. Intent-class accuracy ranged from 40/55 (72.73%) to 47/55 (85.45%), while exact resource-bound accuracy ranged from 10/55 (18.18%) to 32/55 (58.18%). This supports the paper's narrower observation that coarse intent classification was more reliable than bound extraction in that authored task population.
- Checkability: yes, partially. The manifest-ordering rule, certificate validity checks, monotone policy relation, and tool-payload consistency predicate are deterministic and can be probed without trusting aggregate model results. The full request-confinement claim is not independently established because the reference envelopes and effect bounds are author specified, and exact provider-call recreation is unavailable.
- Reproducibility signals: the paper describes endpoint tests, synthetic scripts, runtime fixtures, recorded traces, and a reference prototype, but the review did not execute any artifact. The paper reports that historical provider runs lack complete revision provenance and cannot be recreated exactly.
- Authority signals: this is a two-author, unrefereed preprint with university affiliations listed alongside an organization affiliation. Author count and affiliation tune confidence only; they do not raise the evidence grade or replace independent corroboration.

## Limitations

All evaluated tasks and data are synthetic. Reference certificates, resource bounds, effect bounds, and the benchmark-family analogues were authored by the paper's team without independent annotation. The end-to-end study has no matched real-model OpenPort-only runtime row, so it does not identify IGAC's isolated effect. Repeated trials share task templates, the three models use one provider configuration, and there are no production tenants, real operators, adaptive adversaries, or measurements of reviewer fatigue. The prototype keeps certificate state in memory. Its strongest guarantee depends on complete mediation and correct adapter effect contracts, which the experiments do not independently audit.

## Suggested Update

Disposition: fold-a-narrow-warning. The checkable mechanism lowers the fold bar for a scoped design warning: static credentials and coarse intent labels are insufficient evidence that a proposed payload is justified by the current request, so authorization tests should probe manifest monotonicity, certificate binding and expiry, payload-effect bounds, and direct-call bypasses. Do not fold the effectiveness numbers or a general claim that IGAC confines production agents. Expand-on: yes. Seed topics: independent evaluations of intent-certificate authorization; executable tests for request-to-effect bound fidelity; complete-mediation audits for agent gateways.

2026-10-04 update: expand-on registered. Seed topics wired into research/scouts/config.json under agent_authorization_testing: permission-graph completeness, permission graph completeness, formal agent authorization, semantic extraction failures, runtime SMT gateways, SMT gateway replication, intent-certificate authorization, intent certificate authorization, request-to-effect bounds, request to effect bounds, complete-mediation audits, complete mediation audits, agent gateway evaluation. Disposition unchanged.

## Claims Needing Human Review

- Whether the deterministic monotonicity mechanism is sufficiently distinct from existing capability and purpose-limitation patterns to merit a new canonical warning.
- Whether describing certificate fidelity as the principal bottleneck overstates evidence from author-generated synthetic tasks.
- Whether the absence of an independently executed artifact should lower the evidence grade below C despite the mechanism's direct checkability.
