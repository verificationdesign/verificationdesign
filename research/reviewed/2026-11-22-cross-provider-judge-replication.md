# Swapping the Judge Changes the Ranking: A Preregistered Study of Cross-Provider Replication in LLM-Judged System Comparisons

Reviewed: 2026-11-22
Reviewer: Codex draft; human review pending
Source: https://arxiv.org/abs/2611.04090
Evidence grade: C
Grade confidence: high

## Why It Matters

Requiring multiple judges to agree can change which conclusions an evaluation reports. This study measures both agreement with the external preference reference and the number of comparisons left unresolved. The result makes judge selection, reference quality and coverage relevant to interpreting replicated rankings.

## Method / Evidence

Read: arXiv v1 abstract and full paper (arXiv HTML, local text extraction, 2026-11-22).

- Population and protocol: five proprietary judges from three providers score 4,000 confirmation battles across nine systems and 33 observed system pairs. Anthropic supplies three judges. The cross-provider replication analysis uses one economy judge per provider: Haiku, Luna and Flash-Lite. Each battle has one Arena user's preference vote. Judges see both response orders, and order disagreements or ties resolve to a tie.
- Agreement with Arena votes: across the five judges and 4,000 battles, median verdict Cohen's kappa is 0.217 and system rank Kendall tau-b ranges from 0.167 to 0.889, with median 0.667. These figures describe preference alignment at different units: battle verdicts and rankings of systems derived from those verdicts.
- Pairwise replication: among the 23 system pairs with a significant preference direction in Arena votes, replicated mean precision is 0.902 versus 0.804 for the single economy judges. The abstract reports a gain of +0.10 precision. Luna alone matches the Arena direction on 7/14 called pairs with 0.61 coverage. Pairing Luna with either other economy judge yields 7/8 and 0.35 coverage. Haiku and Flash-Lite each reach 22/23 with full coverage, and their combination also reaches 22/23. The precision denominator counts pairs with a called direction, while coverage uses all eligible pairs.
- Sample requirements: for the 23 pairs selected by a human preference gap of at least 0.1, Sonnet, Opus and Luna fail to recover the full-data voter direction reliably on 6, 8 and 16 pairs, respectively, on the tested grid. The registered 200-verdict grid point exceeded every confirmation pair size, and 100 verdicts were unavailable for five pairs.
- Co-occurrence: on the 2,351 battles where all economy judges give non-tie verdicts, all disagree with the Arena vote on 15.8% of battles versus 3.5% expected under independence, with Holm-adjusted p = 0.002. Shared disagreement is measured against one preference vote per battle, so it can reflect shared judge bias, noisy votes, or both.
- Checkability: pinned battle identifiers and saved verdicts allow independent order resolution, paired resampling, ranking, and recalculation of direction, precision, and coverage. These calculations can assess correspondence with Arena votes. They cannot establish answer correctness or disentangle disagreement caused by voter noise from shared evaluator bias.
- Reproducibility signals: the preprint describes ancillary files with verdicts, battle identifiers, analysis code, a hashed and frozen preregistration, and a deviation record. No public registry is named. The files were not opened. The authors recorded deviations after seeing partial confirmation results from the Anthropic judges, including dropping the planned open-weight judge and changing the majority rule. The majority rule affects a reported comparison outside the hypothesis criteria. The planned prediction-powered baseline was omitted.
- Authority signals: the arXiv preprint lists a business school affiliation and states no peer-reviewed acceptance. These facts inform confidence and leave the grade determined by study design and coverage.

## Limitations

The cross-provider subset represents one economical model per provider, and the full panel includes three models from a single provider. Provider diversity cannot isolate training or judgment independence. The paper uses one English judging prompt and one rule for reconciling response order, with different reasoning settings across providers. Luna ran with reasoning off, while Opus and Sonnet ran with low-effort reasoning. The settings complicate attribution of Luna's lower voter agreement to the model itself, and the replication gain depends on pairings with Luna. The sample excludes tie and both-bad votes, and some older battle texts may have appeared in judge training. Proprietary models may be retired. A single vote per battle gives a noisy preference reference and no separate correctness annotation.

## Suggested Update

Disposition: fold-a-narrow-warning. For principles 2 and 7, report preference alignment, co-occurring disagreement and coverage when replicated judging supports a ranking. This narrows "LLM-judge reliability can vary across benchmarks and perturbations even when the judge comes from a different model family." The result licenses a scoped warning that a replication rule can suppress conclusions and retain shared disagreement. A general effectiveness claim requires independent corroboration with additional providers, comparable reasoning settings, and repeated reference judgments. Expand-on: yes. Seed topics: reference vote reliability in judging; coverage of cross-provider replication; reasoning settings and judge alignment.

## Claims Needing Human Review

- The triage language about shared errors is too strong. Confirm the distinction between co-occurring disagreement with single Arena votes and common incorrect judgments.
- Check the frozen materials and deviations before leaning on the preregistration. The deviations were recorded after some confirmation outputs were examined.
- Keep the significant-direction pairs for the precision analysis distinct from the equally sized sample-requirement set. Their selection criteria differ and the paper does not establish identical membership.
