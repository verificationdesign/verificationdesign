# Shared and structured inputs undermine collective random choice by reasoning AI agents

Reviewed: 2026-11-01
Reviewer: Codex draft; human review pending
Source: https://arxiv.org/abs/2610.09667
Evidence grade: C
Grade confidence: high

## Why It Matters

A plausible audit selection rate does not establish independent or unpredictable sampling. This paper tests whether models implement selection policies through visible identifier fields, and whether shared or timestamp-bearing inputs turn individual regularities into collective correlation or bias. The relevant verification target is the realized selection mechanism, including its dependence on operational inputs, rather than the model's stated intent to randomize.

## Method / Evidence

Read: arXiv v1 abstract and full paper (local text extraction, 2026-11-01).

- Population and design: six closed models from three developers were screened across reasoning settings. Study 1 used 64 designed identifiers, varied participation targets, and obtained 3,966 answers. Threshold and divisibility effects are behavioral hypotheses, not observations of internal algorithms. Study 2 used four separate calls per group, 64 groups per condition and model, and six input conditions for GPT-6 Sol, GPT-6 Luna, and Gemini 3.8 Flash.
- Collective headline: at target 1/3, shared identifiers made 91% of Sol groups and 88% of Gemini groups unanimous, versus 19% and 22% expected independently at observed rates. Shared identifiers preserved average participation while raising group loss to 0.21 and 0.19. Distinct UUIDv7 identifiers instead shifted participation to 0.95 and 0.93, illustrating rate bias separately from correlation.
- Audit headline: study 5 used 1,008 synthetic customer requests with uniformly generated UUIDv4s and a requested 1% review rate. Sol selected 9 requests, or 0.89%, but selected none of the other 989 after accounting for the reported identifier-feature groups. Gemini selected none, Claude selected two, and Luna selected four. A rate near the target therefore concealed predictable selection for Sol, while the other models selected too rarely or provided weak rare-event evidence.
- Controls and narrowing: all three study 2 models followed supplied private random numbers exactly in 768 of 768 answers. Explicit independent-randomization instructions reduced but did not eliminate shared-input correlation. Of 89 pre-specified readings across the reported studies and earlier text-input tests, 21 were not met; these readings are correlated predictions, not independent replications or a success-rate estimate. The initial group task did not require randomization, and independent draws were its reference rather than its optimum.
- Checkability: identifier interventions, repeated decisions, agreement relative to independent draws at observed rates, and comparison with supplied draws can independently test the proposed input-dependence mechanism. These tests do not identify internal computation, establish deployment-level unpredictability, or verify that a review schedule optimizes human attention.
- Reproducibility signals: the paper states that saved trial records, prompts, settings, visible responses, and decisions are available in a Zenodo reproducibility package. Offline analysis and figure code are released under the MIT licence; internal protocols and operational logs are excluded. This review did not execute the package.
- Authority signals: the text is an arXiv preprint with University of Tokyo research-center and engineering affiliations and no stated peer-reviewed venue. Those affiliation and venue facts tune confidence; they do not move the grade or substitute for independent replication.

## Limitations

The experiments use synthetic, isolated decisions without tools or history. Most closed-model names lack dated snapshots. Studies were single runs, predictions were not externally preregistered, and prompt labels and identifier formatting changed the observed regularities. Mixed-model groups were not tested despite exploratory cross-model agreement. Supplied-draw results do not establish reliable rare-event sampling in deployment, and hostile models or adaptive senders were not evaluated. The evidence supports checking input dependence, not treating the inferred rules as universal model behavior.

## Suggested Update

Disposition: fold-a-narrow-warning. For principle 1, recommend checking audit rates, dependence, and predictability separately and making the randomness source externally inspectable. This is an expand-on corroboration candidate for `2026-08-19-nonuniformity-human-ai-coworking.md` and would narrow the synthesis claim "Under a declared stochastic objective and cost proxy, oversight checkpoints can be scheduled as an executable budget-allocation problem." It tests whether agents implement random selection, not whether the seed note's nonuniform schedule or objective is sound. Hold any endorsement of a particular sampling implementation pending independent corroboration. Expand-on: yes. Seed topics: independent replication of agent audit sampling; input dependence in review allocation; trusted random sources for oversight decisions.

## Claims Needing Human Review

- Whether the input-dependence mechanism justifies folding the narrow warning now while keeping deployment effectiveness on hold.
- Whether linking this note to the nonuniform scheduling claim makes its implementation-only relevance sufficiently explicit.
- Whether grade C with high confidence appropriately separates inspectable study detail from absent independent replication.
