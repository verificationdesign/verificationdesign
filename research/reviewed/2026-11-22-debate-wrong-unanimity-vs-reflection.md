# Who Convinced Whom? Tracing How LLMs Change Their Minds in Multi-Agent Systems

Reviewed: 2026-11-22
Reviewer: Codex draft; human review pending
Source: https://arxiv.org/abs/2610.35930
Evidence grade: C
Grade confidence: medium

## Why It Matters

Peer discussion can change both majority accuracy and the dependence of individual judgments. This study distinguishes improvement over an initial vote from improvement over the same number of rounds spent revising independently. It also measures how often every agent agrees on a reference-discordant answer, a failure mode that majority accuracy alone can obscure.

## Method / Evidence

Read: arXiv v1 abstract and full paper (arXiv HTML, local text extraction, 2026-11-22).

- Population: MAD Bench contains 2,400 English text questions, of which 1,700 have a reference target. The accuracy and wrong-unanimity comparisons use fully parsed, non-numeric, reference-labelled questions. All agents had to produce parseable answers at round 0 and at the end of both conditions. The text gives the labelled pool size and leaves the exact filtered count unspecified. Groups consist of three copies of one model: Qwen3.5-9B, Llama-3.1-8B-Instruct, or Gemma-4-E4B-it.
- Accuracy against the round-0 majority vote: after three rounds of peer discussion, Qwen moves from 88.0% to 89.2%, Llama from 77.3% to 77.8%, and Gemma gains 1.2 percentage points. Llama's interval covers zero. The appendix reports only the change for Gemma.
- Accuracy against round-matched independent reflection: peers' answers are removed in the control. The paper reports a larger benefit for Llama because independent revision reduced its accuracy. Qwen and Gemma remain inconclusive in this contrast. Figure 3 compares these differences, but its caption and Table 13 supply no numeric debate-versus-reflection accuracy differences.
- Wrong unanimity against round-matched independent reflection: the reported increases are 3.1 percentage points for Qwen, 7.4 for Llama, and 3.6 for Gemma. The outcome requires unanimous agreement on an answer that differs from the reference. When the initial majority is wrong, Qwen and Llama end unanimous on that wrong answer in 76% of debate cases, compared with 54% and 43% under reflection, respectively. After twelve rounds on the 600-question long-horizon subset, initially contested, reference-labelled questions yield 1.02 to 1.07 effective independent voters in debate and 1.70 to 2.10 in reflection. These estimates describe homogeneous groups. At each round the two conditions use the same scored questions, with eligibility allowed to change across rounds.
- Checkability: with item labels and saved round-level answers, a separate implementation can reproduce parsing, votes, wrong unanimity, and the within-question correlation of correctness. Those checks establish agreement with supplied labels and observed dependence. Label validity and generalization to other panel designs remain separate questions.
- Reproducibility signals: the paper names open-weight checkpoints and describes companion data containing prompts, conditions, and annotations. The text gives no companion download link and the artifacts were not opened. The paper text read for this review does not state whether code or data are released.
- Authority signals: the arXiv preprint lists university affiliations and an independent researcher. The text reports no peer-reviewed acceptance. These facts inform confidence, and the grade follows the study design and coverage.

## Limitations

Small open-weight models, a single English benchmark and one fully connected peer protocol constrain transfer. Reference targets include normative annotations and behavioral targets alongside factual answers. Constructed labels were assigned at construction, without independent human adjudication. Unparseable responses occur most often at the initial vote, so unrestricted accuracy would penalize that baseline disproportionately. The fully parsed analysis conditions on successful parsing in both arms. Scenario variants and persuasion items share underlying scenarios or claims. The reported intervals resample questions, and the benchmark appendix recommends resampling those related items together.

## Suggested Update

Disposition: fold-a-narrow-warning. For principles 2 and 8, compare peer discussion with both the initial vote and round-matched private revision, and report wrong unanimity alongside accuracy. The result supports the protocol-specific caution in the debate-supervisor review of 2026-11-01, which also found losses in homogeneous model deliberation. Its peer-only setup leaves principle 8's two-sided debate with a separate judge untested. An effectiveness claim for that format still needs independent corroboration. Expand-on: yes. Seed topics: wrong unanimity under peer discussion; compute-matched private revision controls; independent judging of adversarial debate.

## Claims Needing Human Review

- The raw text defines the filtered population in Figure 3 and the methods. Table 13 supplies no per-model counts. Check whether per-model counts and the debate-versus-reflection accuracy differences can be recovered from the original figure or companion data. The stated 1,700 labelled questions describe the parent pool. The introduction and discussion describe the vote as compute-matched, while the methods specify round-0 voting and round-matched reflection.
- Table 13 reports Qwen wrong unanimity at 6.6% and 9.8%, with a stated increase of 3.1 points. This note uses the printed increase. Verify the underlying precision if the levels are needed.
- The unused committed-at-read gap appears as 43.1 in Table 9 and 43.0 in the prose and control row. The filler gap is 47.3 in the table and 47 points in the caption. The decision-token-preserving control is described as 9% in prose, while Table 12 gives 8.6 for Qwen and 9.1 for Llama. The unqualified 69% reasoning share is Qwen's all-items value in Table 10. The unnamed twelve-turn wrong-unanimity figures are omitted.
