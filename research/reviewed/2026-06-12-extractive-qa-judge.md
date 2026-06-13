# LLM-as-a-Judge for Extractive QA

Reviewed: 2026-06-12
Reviewer: Human + Codex
Source: https://arxiv.org/abs/2504.11972
Evidence grade: B
Grade confidence: medium

## Why It Matters

This paper is relevant to the repo's distinction between reliable checks and valid checks. Exact Match is deterministic and repeatable, but in extractive QA it can be invalid when a single gold string under-specifies the space of correct answers. In the paper's human-checked sample, 39 of 200 sampled instances were excluded because the gold answer itself was incorrect, a derived 19.5% exclusion rate. That is direct evidence for the oracle-validity thread behind Principle 6, and it also qualifies Principle 1's claim that mechanical extraction can be reliable.

The paper does not imply replacing executable checks with judges. Its judge works in a grounded setting where the question, gold answer, predicted answer, and context are all shown to the judge, and it still has answer-type weak spots. The design lesson is to audit the oracle and understand what a metric measures before treating a deterministic comparator as ground truth.

## Method / Evidence

The reviewed source was the arXiv v2 full text, with the v3 abstract checked separately. The live v3 abstract retitles the paper to "Reassessing Extractive QA Datasets at Scale: LLM-as-a-Judge and In-Depth Analyses" and is consistent with the v2 full text on the core numbers used here.

The study evaluates four extractive QA datasets: Quoref, DROP, HotpotQA, and 2WikiMultiHopQA. The authors select about 1,000 samples per dataset after excluding boolean answers, for 4,193 total samples across seven retained answer types. The QA systems are eight instruction-tuned models from four families: Mistral v0.1, Qwen 2, Gemma 2, and Llama 3.1. The main judge models are Mistral-Instruct-7B-v0.3, Llama 3.3 70B, and Qwen 2.5 72B. The judge prompt uses few-shot examples and, at evaluation time, provides the question, gold answer, predicted answer, and context.

For the human study, the authors sampled 200 instances, 50 per dataset, each with eight predicted answers. Two author-annotators judged the samples, with one annotator assigned to each sample and discussion allowed for ambiguous cases. They excluded cases where the gold answer was incorrect, leaving 161 valid instances and 1,288 judged predicted answers.

Against human judgment, Table 2 reports average Pearson correlations across the eight QA models of 0.220 for EM, 0.404 for F1, 0.653 for the Mistral judge, 0.750 for the Llama 3.3 judge, and 0.847 for the Qwen 2.5 judge. The paper attributes the metric gap to cases where a prediction is a valid alternative to the gold answer but does not exactly match the single gold string.

The answer-type analysis also matters. For Qwen 2.5 as judge, the reported correlations with human judgment are 0.899 for number, 1.000 for date on only 16 samples, 0.862 for name, 0.862 for string, 0.771 for place, and 0.352 for job. The paper explains the job weakness through ambiguity around multiple professions in the gold answer and predictions that list more or fewer jobs, where the judge is less strict than humans.

Self-preference bias is small in this grounded setup. At the unanimous-disagreement threshold, the self-preference score is 5.77% for Llama 3.1 8B when it is both QA model and judge, and 0.63% or lower for the other three tested QA and judge pairings. The authors explain this by the extractive QA setting, where the gold answer is clearly provided. The paper's practical comparison uses the judge on false-EM samples, while Appendix B.1 also reports all-sample results.

The evidence grade is B because the paper is directly relevant, uses multiple datasets and model families, includes a real human-judgment study, and states that code and data are released. It is not grade A because it is still an arXiv preprint, the human study has 161 valid instances with author-annotators, and each sample receives a single annotation after ambiguous-case discussion rather than independent replicated labels.

## Limitations

The human-judgment subset is small relative to the full evaluation, and the annotators are two authors of the paper. The single-annotation protocol limits what can be inferred about human-label reliability.

The judge has clear answer-type weak spots, especially job answers at 0.352 correlation with human judgment. Date has a perfect reported correlation but only 16 samples.

The self-preference finding should not be generalized beyond this extractive QA regime. The judge is given the gold answer and context, which is an easier setting than open-ended evaluation or agent-trajectory judgment.

The reviewed full text is v2, while the live arXiv version is v3. The v3 abstract is consistent on the core numbers used here, but the full v3 text was not the reviewed copy.

## Suggested Update

Append a dated note under Principle 6: deterministic comparators can be reliable while their oracle is invalid, so single-gold-string metrics should be audited against human judgment and dataset-label quality before being treated as correctness. The note should emphasize that judge fallback is a hybrid pattern only when scoped to known metric blind spots, because the judge itself has answer-type failures and depends on the gold answer and context supplied in the prompt.

Maintainer decision (2026-06-13): fold into Principle 6. The maintainer reviewed this paper specifically and approved the fold; under the fold-in bar it qualifies as corroboration of the already-folded 2026-06-09 oracle-validity callout (it counts as the second source) and as a scoped warning. The canonical callout and References row land through a separate fold cycle; this note is the source of record for that callout.

## Claims Needing Human Review

- Whether this reliability-versus-validity nuance belongs under Principle 6 or Principle 1.
- Whether the derived 19.5% wrong-gold exclusion rate may be quoted in the canonical document or should remain qualitative.
- Whether judge-as-fallback-for-false-EM deserves mention as a hybrid verification pattern.
