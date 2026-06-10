# Auditing LLM Benchmarks with Item Response Theory

Reviewed: 2026-06-09
Reviewer: Claude; human review pending
Source: https://arxiv.org/abs/2605.30504
Evidence grade: B
Grade confidence: medium

## Why It Matters

This is the first source in the corpus that directly attacks an assumption Principle 6 currently treats as unconditional: "the test suite does not care what the agent thinks." An executable check against a wrong expected value is still confidently wrong. The paper shows at scale that benchmark labels (the oracle side of many executable checks) carry systematic errors, that those errors propagate silently into downstream benchmarks and reward-model training, and that the error sources include exactly the mechanical letter-over-spirit artifacts a verification designer would build. This adds a failure mode the doc's nine principles do not currently cover: oracle validity needs its own audit path.

## Method / Evidence

Read: pages 1 to 6 of the v1 PDF (methods, results, mislabel patterns, model-level anomalies).

- Data: two classes of multiple-choice benchmarks. Preference benchmarks used to evaluate judges and reward models (RewardBench, RewardBench 2, RM-Bench, JudgeBench) and factual 4-way MC benchmarks (GPQA Diamond, MC variants of MATH and GSM8K). 20986 items spanning 32 subsets; responses from 114 models from 2023 to 2026, including six dedicated reward models.
- Method: a four-parameter logistic (4PL) IRT fit where the upper asymptote models the probability that an arbitrarily strong model matches the reference. The mislabel indicator is a forced-ceiling likelihood ratio: refit each item under ceiling-equals-one and ceiling-equals-zero hypotheses and score the difference. Positive scores mean ability inflates the probability of the non-reference answer.
- Headline result: 95.0% precision in the top 200 flagged items under strict mislabel scoring, and the best average precision among the baselines tested (top-10 disagreement, XGBoost on 4PL parameters, raw ceiling, 2PL, GLAD). Flagged items are mislabeled or subjective 81% of the time versus 3% for unflagged items.
- Validation basis: weak reference labels built with a strong-model consensus aggregator (GPT-5.4 over several strong-model judgments) plus hand inspection of flagged items in an appendix. Not full independent human re-annotation of the corpus.
- Error taxonomy from hand inspection: (1) construction and verification artifacts, where topic-fit labels, format verifiers, style-variant templates, and by-construction error injection mark a response correct for satisfying the construction rule rather than being the better answer (letter-versus-spirit failures); (2) source errors inherited unchanged from upstream datasets (GSM8K reasoning errors, MMLU-Pro key issues) reappearing across generated variants downstream; (3) items with no defensible single answer (duplicate options, convention-dependent answers, near-equivalent preference pairs).
- Model-level anomaly: one high-scoring reward model (Skywork-Reward V2 Llama 8B) agrees with detected mislabels far outside its peer group (78% versus 38% for peers, abstract figures). The authors name two mechanisms they cannot distinguish from response data alone: accidental contamination via a 40M-pair public preference mixture, or benchmark-specific over-optimization.
- Secondary finding: reward models cluster above their own mean ability on preference benchmarks and below it on factual MC benchmarks, suggesting format-specific specialization.

## Limitations

Preprint (28 May 2026); no peer review or replication yet. The 95% precision figure is measured against weak reference labels (model-consensus plus hand inspection), so the figure partly inherits the judgment of the aggregator model; the authors are explicit about this construction. The method needs many diverse models per benchmark and items where high-ability behavior is informative; subjective items blur the mislabel boundary (the paper scores them separately). Findings are about public multiple-choice and preference benchmarks; transfer to project-local test suites and fixtures is a design inference, not a measured result.

## Suggested Update

Append a dated note under Principle 6: executable checks inherit the validity of their oracle; labels, expected values, and fixtures need their own audit path; mechanical letter-over-spirit verifier artifacts are a documented source of wrong oracles at scale. Add a References table row.

## Claims Needing Human Review

- Whether "95% precision in the top 200" should appear in the canonical note given the weak-reference validation basis, or whether the note should carry only the qualitative claim with the figure left here.
- Whether the letter-versus-spirit verifier-artifact finding deserves its own anti-pattern entry (a verifier that enforces the construction rule rather than the intent) or stays inside the Principle 6 note.
- Whether the Skywork mislabel-agreement anomaly should be mentioned as a contamination signal, given the authors themselves cannot distinguish contamination from over-optimization.
