# Humans Correct Their Judgments Through Debate, but Weaker AI Models Do Not

Reviewed: 2026-11-01
Reviewer: Codex draft; human review pending
Source: https://arxiv.org/abs/2610.28539
Evidence grade: C
Grade confidence: high

## Why It Matters

Debate is an intervention whose effect depends on the supervisor, initial knowledge, and decision protocol. This study measures belief changes before and after debate rather than inferring success from persuasive arguments. It is relevant to principle 8 because human improvements coexist with mixed model results, and because adding judges or requiring consensus does not automatically improve the final decision.

## Method / Evidence

Read: arXiv v1 abstract and full paper (local text extraction, 2026-11-01).

- Population and design: the authors construct 100 specific items across 10 scientific and technological topics, with paired true and false statements. They report 5 human experiments with N = 507 and over 40 model-based experiments. Claude Opus 4.5 supplies assigned-position debate and consultancy. Human priors are measured; model priors are unconditioned or induced through system prompts, personas, and activation interventions. Pre-debate specific answers provide the direct-answer comparison, while consultancy supplies a separate single-expert protocol.
- Human headline: among 92 in-subtopic debate participants, accuracy increases from 41.30% to 57.61%, with adjusted p=.028. In the 80-participant consultancy population, accuracy changes from 51.25% to 48.75%, p=1.000. These are within-protocol pre/post comparisons with different starting populations, not a direct matched effect size between protocols. Cross-subtopic debate involves 89 participants and reaches 58.43% after 50.56% before; the reported p=1.000 is a test against chance with different pre/post items, not evidence of significant transfer.
- Human aggregation: confidence-weighted voting increases accuracy from 45.83% to 65.28%, p=.028, relative to its pre-debate aggregation baseline. Voting and weighted voting are reanalyses of groups formed from collected human judgments, not separately recruited intervention populations. Subsequent human deliberation changes 62.99% to 62.20%, p=1.0, rather than adding a reliable improvement.
- Weaker-model results: on 198 unconditioned GPT-5.2 judgments, debate increases accuracy from 84.85% to 90.40%, p=.044. Other settings are mixed: GPT-4o changes from 86.36% to 84.85%, p=1.0, on 198 judgments. Under induced general beliefs, GPT-4o improves from 53.79% to 60.86%, p=.022, on 396 judgments. These exceptions prevent interpreting the title as a universal failure of model supervisors.
- Panel narrowing: homogeneous model panels with consensus lose accuracy during deliberation, from 48.96% to 44.04%, p=.022. Diverse 7-judge panels improve during deliberation from 58.26% to 64.29%, p=.006, relative to their post-debate state. Increasing panel size from 3 to 7 produces no significant final-accuracy gain in the tested protocols, all p at least .24. The diverse-panel result is a deliberation-stage improvement, not a general debate benefit or a crowd-size effect.
- Checkability: saved pre/post answers, correctness labels, assigned conditions, aggregation rules, and cluster-aware statistical comparisons permit independent recalculation of belief changes. They do not verify the truth of author-written topic labels, establish a causal explanation in terms of internal beliefs, or demonstrate worst-case oversight robustness.
- Reproducibility signals: the paper states that data and code for all experiments are publicly available in a GitHub repository. This review inspected the extracted paper rather than running those artifacts.
- Authority signals: the text states that this is an extended version of a NeurIPS 2026 accepted paper, with university, public-research, and other organization affiliations. Those facts tune confidence only; they do not move the grade or substitute for replication.

## Limitations

The author-written statements were not verified by domain experts. Tasks require factual domain knowledge rather than long-horizon reasoning, and proprietary judges can already know the facts. Induced model beliefs may measure instruction-following conflicts rather than human-like belief revision. Diversity changes both model identity and personas, preventing attribution to either factor. Diverse voting was not tested. Assigned statements measure average-case behavior rather than adversarially selected claims. Human and model starting accuracies differ, so their gains cannot be interpreted as a controlled capability comparison.

## Suggested Update

Disposition: fold-a-narrow-warning. Principle 8, "Simulate Debate," currently has no synthesis claim heading to corroborate; this is its first candidate source. The note would license a scoped warning to evaluate debate against pre-debate answers and consultancy, identify the supervisor population, and report aggregation and deliberation stages separately. It would not license a general endorsement of human debate, a universal rejection of model debate, or a claim that larger juries improve verification. Effectiveness claims remain held pending independent corroboration on comparable tasks. Expand-on: yes. Seed topics: independent replication of debate supervisor comparisons; expert-validated debate benchmarks; diversity and aggregation in oversight juries.

## Claims Needing Human Review

- Whether the triage label narrows remains appropriate: its mixed-results paraphrase is supported, but any blanket reading of model failure conflicts with positive single-model and diverse-deliberation results.
- Whether the human voting reanalysis and different pre/post units are clear enough to prevent an inflated interpretation of the best human result.
- Whether grade C is appropriate despite conference acceptance, given the authored benchmark, induced beliefs, and absent independent replication in this review.
