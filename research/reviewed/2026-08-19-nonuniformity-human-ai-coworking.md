# Nonuniformity Principle in Human-AI Coworking

Reviewed: 2026-08-19
Reviewer: Codex draft; human review pending
Source: https://arxiv.org/abs/2607.16530
Evidence grade: C
Grade confidence: medium

## Why It Matters

The paper asks where a fixed number of oversight events should occur in a multi-stage workflow. Its strongest reusable contribution is an explicit scheduling objective and algorithm, not a general empirical result about human attention: under stated assumptions, optimal oversight gaps do not decrease as work progresses.

## Method / Evidence

Read: arXiv v1 abstract and full paper.

- The model fixes a workflow of T stages and K oversight events. It represents post-oversight residual alignment error with a revision factor, models uncertainty growth between reviews, and assigns greater inspection cost to later, longer intermediate deliverables.
- Under conditional-independence, stage-homogeneous error-growth, and increasing-cost assumptions, the paper derives non-decreasing gaps between oversight events. For a random-walk error model with linear review cost, Algorithm 1 takes T, K, a revision factor, and the review-cost-to-uncertainty ratio and returns a globally minimizing discrete schedule under the paper's objective.
- Study 1 uses 40 accepted ICLR 2026 papers sampled across 18 primary areas. Each of 6 schedule populations produces one related-work artifact per paper, with T=10 production stages and K=3 oversight events for the 5 oversight schedules. Separate LLM calls instantiate agent, reviewer, and judge roles.
- Study 2 uses 10 landing-page tasks. Each of 6 schedule populations produces one page per task, again with T=10 and K=3 for the 5 oversight schedules. A vision-language model supplies both oversight and final quality judgments, with scoring repeated 3 times in randomized presentation order per set of 6 pages.
- In the 10-task page population, Tilt-Early had mean quality 7.74 with standard error 0.21 on the paper's 1 to 10 judge scale at fixed schedule cost 10. Uniform had mean quality 7.56 with standard error 0.20 at cost 15, and Burst-Late had mean quality 6.58 with standard error 0.26 at cost 24. Cost is the sum of review-stage indices, not observed human time or cognitive load.
- The theoretical schedule is independently computable from declared parameters. An executable test can observe stage indices, gap monotonicity, intermediate artifact length, review events, and the objective value. It cannot infer whether the assumed uncertainty process or proxy cost matches a real operator without additional measurements.
- Reproducibility signals: the full paper supplies formulas, pseudocode, task and schedule definitions, and supplementary implementation detail. No code or data artifact was inspected or executed in this review.
- Authority signals: this is a two-author, unrefereed preprint from one university department. Affiliation and author count tune confidence only; they do not raise the grade or replace independent corroboration.

## Limitations

The main theorem depends on restrictive assumptions: future requirements are conditionally independent of unreviewed intermediate drafts, error growth depends on lag rather than stage, oversight fully resolves the current requirement in motivating examples, and inspection cost increases with accumulated work. The experiments test only two authored workflow families, T=10, K=3, five oversight schedules, and model-simulated reviewers rather than human operators. Quality is assigned by model judges. The page-study cost is a fixed sum of stage indices, while the writing-study proxy is tied to deliverable length; neither measures attention, fatigue, interruption cost, or actual review time. Empirical agreement with non-decreasing gaps does not validate the latent stochastic assumptions.

## Suggested Update

Disposition: hold-and-watch. Checkable mechanism for operator attention or budget: yes. The scheduling algorithm and objective expose executable observables: the allowed review count K, review-stage indices, gap sequence, deliverable-size or stage-based cost proxy, and computed loss. A test can verify schedule construction and compare candidate schedules under declared parameters. This is a checkable budget-allocation mechanism, but it is not yet evidence that the proxy optimizes real human attention. Hold pattern-card promotion until a human-operator study or independent replication tests measurable time or cognitive cost. Expand-on: yes. Seed topics: executable oversight scheduling under measured human review cost; replication of nonuniform review schedules with human operators; sensitivity tests for stage-dependent error growth.

2026-10-04 update: expand-on registered. Seed topics wired into research/scouts/config.json under oversight_scheduling: oversight scheduling, human review cost, review budget allocation, review-stage placement, review stage placement, nonuniform review schedules, non-uniform review schedules, human review scheduling, stage-dependent error growth, stage dependent error growth, review schedule replication, review cost measurement. Disposition unchanged.

## Claims Needing Human Review

- Whether the algorithm is useful enough under declared assumptions to become an exploratory pattern before human validation.
- Whether the experimental judge and reviewer role overlap creates correlated measurement that weakens the empirical comparison.
- Whether "operator attention" is too broad a label for a model that allocates review events but does not measure attention directly.
