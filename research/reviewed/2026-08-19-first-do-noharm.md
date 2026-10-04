# First, do NOHARM: A Medical Safety Benchmark and Randomized Study of Physician and AI Teaming on Clinical Consultations

Reviewed: 2026-08-19
Reviewer: Codex draft; human review pending
Source: https://arxiv.org/abs/2512.01241
Evidence grade: C
Grade confidence: low

## Why It Matters

The abstract reports a mismatch between having useful AI recommendations available and physicians incorporating them into final consultation answers. For verification methodology, that is a warning that operator attention and use cannot be inferred from model output quality or tool availability.

## Method / Evidence

Read: arXiv v4 abstract only.

- The abstract describes NOHARM as 1,100 primary-care-to-specialist consultation tasks across 10 specialties, with 12,747 expert annotations covering 4,249 clinical management options.
- The system evaluation population comprises 20 named notable LLMs and 4 widely used retrieval-augmented clinical AI tools. The abstract reports potential severe harm in up to 24.6% of cases for direct application of recommendations, but it does not identify the system-specific numerator and denominator behind that maximum. No stronger quantitative characterization is made here.
- The abstract states that performance was not uniform across the evaluated systems: clinical AI tools outperformed generalist LLMs, and multi-agent teaming improved generalist-model performance. That heterogeneity makes the unidentified system and case denominator behind the up-to-24.6% maximum especially material.
- The randomized physician study population contains 101 U.S.-licensed generalist physicians. The abstract says AI assistance improved physician performance relative to conventional resources, but assisted physicians still scored lower than many AI systems alone and omitted valuable AI recommendations. It separately states that errors of omission accounted for more than 80% of severe errors. The abstract does not provide arm sizes, effect estimates, uncertainty intervals, or omission denominators.
- The counterfactual claim that combined human and AI responses could outperform each component depends on incorporating recommendations that physicians did not use. The abstract does not provide enough detail to distinguish attention failure from disagreement, workflow friction, time limits, or appropriate rejection.
- Reproducibility signals: the abstract says the benchmark and leaderboard are public. Neither was inspected or executed in this review, and the full paper, annotation protocol, study materials, and analysis were not read.
- Authority signals: this is a 57-author, unrefereed preprint. The study concerns licensed physicians and expert annotations, but author count and professional or institutional authority do not raise the grade or substitute for reading the method and independently checking the evidence.

## Limitations

This note is constrained to the abstract. It cannot assess randomization, allocation, physician arm composition, scoring, annotation agreement, specialty balance, statistical analysis, counterfactual construction, conflicts of interest, or artifact contents. The phrase "up to 24.6%" names a maximum without the responsible system or case denominator in the abstract. The physician findings have a stated total population of 101 but no arm denominators or quantitative effects. Medical consultation performance is also a high-stakes, domain-specific setting, so transfer to general operator oversight should be treated as a caution rather than a general law.

## Suggested Update

Disposition: hold-and-watch. The abstract supports discovery, not canonical characterization. The reported result that AI-assisted physicians still scored below many AI systems alone makes operator uptake the load-bearing reason to keep watching this source, and the reported concentration of severe errors in omissions strengthens that warning. Checkable mechanism for operator attention or budget: no. The abstract supplies no executable attention measure, review-budget control, or observable mechanism that distinguishes non-attention from deliberate non-use. These additions do not change the disposition because the method and quantitative denominators remain unavailable at this read scope. Expand-on: yes. Seed topics: observable uptake measures in human-AI decision support; randomized operator-attention interventions; recommendation omission versus justified rejection.

2026-10-04 update: expand-on registered. Seed topics wired into research/scouts/config.json under operator_attention: AI recommendation uptake, recommendation omission, justified rejection, operator-attention interventions, operator attention interventions, randomized attention interventions. Disposition unchanged.

## Claims Needing Human Review

- Whether the full paper operationalizes "omitted valuable recommendations" in a way that separates attention from clinical judgment.
- Whether the counterfactual combined-response analysis preserves randomization or introduces post-treatment selection.
- Whether benchmark and physician-study results warrant grade B after full-paper and artifact review.
