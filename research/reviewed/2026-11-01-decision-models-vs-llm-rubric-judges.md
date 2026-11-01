# Decision Models vs. LLMs as Rubric Judges: Cheaper, Faster, and Wrong in the Same Places

Reviewed: 2026-11-01
Reviewer: Codex draft; human review pending
Source: https://arxiv.org/abs/2609.29769
Evidence grade: C
Grade confidence: medium

## Why It Matters

A cheap first-stage judge and an expensive fallback improve reliability only if their errors complement each other where the cascade uses them. Architectural differences and useful confidence scores do not establish that complementarity. This study compares decision models with generative rubric judges against human labels, then replays cascades to measure how much accuracy the fallback actually adds.

## Method / Evidence

Read: arXiv v3 abstract and full paper (local text extraction, 2026-11-01).

- Jev and Perplexity's Decider receive the same criterion texts as GPT-5.6 Luna, Gemini 3.8 Flash, and DeepSeek V4.1 Flash. The main population has 5,003 unit-criterion pairs across nine panels from seven human-labeled benchmarks. LLM judging is tested both per criterion and with whole rubrics; decision models read each unit's criteria together.
- Across the tested judging setups, LLM judges cost 16 to 357 times as much and take 5 to 350 times as long, while each decision model trails significantly in at most 6 of 27 comparisons. These are measured comparisons under the paper's pricing, concurrency, models, and rubric constructions, not permanent service economics.
- In the main per-criterion confident-error analysis, Jev's 12 most confident errors per ordinal panel supply 84 pairs and 252 LLM verdicts. Of those verdicts, 242 (96.0%) repeat Jev's wrong answer, against 50.3% under the criterion-and-label-conditioned independence baseline. For Decider, 218 of 252 verdicts (86.5%) repeat its answer against 47.9% expected. Different model designs do not deliver independent errors here.
- In the main cross-fitted cascade analysis, no Jev-first average gain over the best single judge exceeds 1.5 points; cascades trail it on six of nine panels. Across flash-tier conditions, the largest oracle gain is 2.7 points. With higher-tier fallbacks, no Jev-first cascade exceeds either tier's strongest single judge by more than 1.7 points. Oracle thresholds are selected on the evaluated pairs and are optimistic rather than prospective validation.
- Checkability: stored verdicts, labels, confidence values, and threshold rules allow recomputation of repeated-error rates and cascade performance. Cross-fitting separates threshold selection from evaluation halves. These mechanisms do not establish that human labels express the intended standard, identify why errors correlate, or guarantee performance on a new task distribution.
- Reproducibility signals: the authors state that they release every judge's verdict records so paper numbers can be recomputed without model API requests; the artifact appendix identifies calculations requiring other inputs. No records were executed in this text-only review.
- Authority signals: the arXiv manuscript lists University of Pennsylvania affiliations and no stated peer-reviewed acceptance. The authors state that they are not incentivized by the decision-model vendors or competitors. Those are confidence considerations and do not move the evidence grade.

## Limitations

The explanation of shared rating conventions is exploratory: the study does not intervene with exemplars or rewritten level descriptions to identify a cause. Human raters can disagree, and benchmark labels are not infallible. Confidence-selected error samples describe a particular slice, not all errors. Cross-fitted halves can contain as few as 12 units, while oracle thresholds overfit the evaluated population. Costs are replay estimates and exclude live deferrals caused by first-stage abstention. Tested vendor tiers, effort settings, and request formats constrain generalization to other cascades.

## Suggested Update

Disposition: fold-a-narrow-warning. For principles 2 and 7, measure conditional fallback correctness and shared errors before treating a cheap-to-expensive cascade as additional verification. This narrows "2. Independence Between Generation and Verification" in the synthesis. It is an expand-on challenge to research/reviewed/2026-08-19-nonuniformity-human-ai-coworking.md: review allocation also needs evidence that the selected reviewer can correct the work it receives. These results concern automated-judge cascades and do not replicate or refute human oversight scheduling. Hold broad accuracy and cost endorsements pending independent corroboration. Expand-on: yes. Seed topics: complementary errors in judge cascades; conditional fallback accuracy measurement; human oversight correction complementarity.

## Claims Needing Human Review

- Review whether the automated-cascade challenge to the nonuniformity note is useful without implying a direct test of human scheduling assumptions.
- Confirm that the main cross-fitted result and the across-condition oracle maximum remain clearly distinguished.
- Confirm grade C given extensive benchmark coverage but no independent replication or causal test of the shared-error explanation.
