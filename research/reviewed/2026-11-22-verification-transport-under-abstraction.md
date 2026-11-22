# Do Verifier Judgments Survive Abstraction? Measuring Verification Transport for LLM Agent Evaluation

Reviewed: 2026-11-22
Reviewer: Codex draft; human review pending
Source: https://arxiv.org/abs/2611.18471
Evidence grade: C
Grade confidence: high

## Why It Matters

A verifier calibrated on complete traces can lose access to the evidence needed to apply the same criterion after an execution is summarized. This study tests whether a judgment survives a change in its evidence view while holding the trajectory, outcome, and criterion fixed. For step-level checkpoints, this makes the evidence available at the checkpoint part of the evaluation design.

## Method / Evidence

Read: arXiv v1 abstract and full paper (arXiv HTML, local text extraction, 2026-11-22).

- Population and design. The authors use 250 AgentProcessBench trajectories with a designated step label, 758 ATBench tool-use trajectories, 441 PlanRewardBench pairwise comparisons, and 754 AgentDojo trajectories. They construct matched native, abstracted, and restored views of eligible frozen executions and use ground truth inherited from each benchmark. Seven backbones from the Gemini, GPT-OSS, Gemma, and Llama families run direct, evidence-grounded, provenance-seeking, and deliberative protocols.
- Transport failures. Among native-correct judgments pooled over the benchmarks, backbones, and protocols, 31.0% fail under macro abstraction, 30.9% under delegation, and 20.3% under compaction. A wrong judgment and a missing usable verdict, including abstention, both count as failures. In macro views, the direct protocol yields 15.8% wrong verdicts and 0.7% no verdict, the evidence-grounded protocol 10.6% and 24.0%, and the deliberative protocol 9.4% and 39.9%, each as shares of that protocol's native-correct judgments.
- Restoration. Exact provenance recovers 85.5% of pooled abstraction-induced failures. Restoration degrades 5.2% of pooled native-correct judgments that survived abstraction. In the AgentProcessBench fidelity ablation with Gemini-2.5-Flash, recovery among abstraction-induced failures is 22.5% on requery, 42.8% with lossy provenance, and 80.0% with exact provenance. The fidelity ablation uses AgentProcessBench and ATBench with Gemini-2.5-Flash and GPT-OSS-120B.
- Checkability. Matched views can be regenerated from the frozen event records, and restored events can be checked against the original events for the corresponding boundary. The conditioned rates can be recalculated from paired verdicts and benchmark labels. The checks establish evidence identity and measured verdict changes. Benchmark label validity and live-system evidence capture require separate validation.
- Reproducibility signals. The paper reports public code on GitHub and includes representative verifier templates. The repository was unopened for this review.
- Authority signals. The arXiv preprint lists university affiliations and a workshop title. The staged abstract metadata reports workshop acceptance. These facts tune grade confidence while the evidence grade depends on the method and its scope.

## Limitations

The abstractions are deterministic transformations of frozen benchmark trajectories. Real macro tools, sub-agents, and compaction systems may produce different evidence, and exact restoration assumes original events remain available. The study sums eligible numerators and denominators across cells and gives no per-cell denominators. Native-view accuracy is low in many cells, and the native-correct subset can be a minority and can differ across backbones and protocols. The pooled transport rates therefore measure stability on different selected subsets. Bootstrap interval endpoints are available only in a figure and could not be read from the staged text.

## Suggested Update

Disposition: fold-a-narrow-warning. For principles 3 and 5, test checkpoint criteria with the evidence view available at use time and track wrong verdicts separately from missing verdicts. This narrows "Explicit rubrics remain sensitive to how criteria are presented and executed" by showing that changing the execution evidence alone can destabilize a previously correct judgment. Hold the effectiveness of live provenance restoration pending independent corroboration. Expand-on: yes. Seed topics: verifier calibration on live compacted histories; delegation evidence preservation; matched trace provenance restoration.

## Claims Needing Human Review

- Whether the triage headline makes the two conditioned populations and the simulated nature of the abstractions sufficiently clear. Its label of narrows fits the experiment.
- Whether pooling obscures operationally important protocol differences. The printed rounded macro components and totals can differ in their last digit, and the underlying cell counts are unavailable in the text.
- Whether the warning belongs under both principles when the benchmarks vary in what they evaluate and only AgentProcessBench supplies a designated step label.
