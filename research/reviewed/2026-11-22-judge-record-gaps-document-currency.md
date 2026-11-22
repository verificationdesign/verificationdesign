# What Do LLM Judges Actually Verify? Matched Controls and Record Gaps for Document Currency

Reviewed: 2026-11-22
Reviewer: Codex draft; human review pending
Source: https://arxiv.org/abs/2611.01311
Evidence grade: C
Grade confidence: high

## Why It Matters

A judge can perform well with a complete reference record and miss a replaced citation when the record omits a link it needs. Matched cases test how an incomplete record changes use of the available documents. Separate controls for valid older citations and updates help distinguish currency checks from a preference for newer documents.

## Method / Evidence

Read: arXiv v1 abstract and full paper (arXiv HTML, local text extraction, 2026-11-22).

- Population and planned comparisons: the test uses 48 replacement links from the IETF RFC index to construct replaced citations, successor citations, citations valid at an earlier date, and update-only decoys. The planned tests compare text-only catches with matched decoy false alarms, authoritative omission with texts alone, and alternate presentations with the authoritative damaged record. With an intact record the judges catch 47/48 or 48/48, and the lookup catches all faults. On gap faults the lookup catches 0/24 by construction.
- Seed 0 paired comparison: from texts alone with no record to the authoritative damaged record, Gemini 3.1 Pro falls from 23/24 to 1/24, GPT-5.5 from 23/24 to 9/24, Claude Opus 4.5 from 17/24 to 9/24, and Gemma 4 26B from 13/24 to 0/24. The authors report Holm-adjusted p below .001 for Gemini, GPT and Gemma and .008 for Claude. Each comparison uses the same judge on the same gap faults.
- Planned presentations: the reworded line stating "no replacement recorded" leaves the record present and fails to restore text-only catch levels. The unverified note and the incompleteness warning recover catches for Gemini and GPT-5.5 after Holm correction. Claude reaches 17/24 under either presentation, with raw p .008 and Holm-adjusted p .062 for each. Gemma reaches 2/24 with the note and 5/24 with the warning, compared with 13/24 from texts alone. On update-only decoys GPT-5.5 flags 10/48 with the note and 8/48 with the warning, against 8/48 from texts alone and zero with the authoritative record.
- Robustness and exploratory comparisons: seed 1 again shows a decline for every judge. It shares 12 of 24 gap faults and all text-only replies with seed 0. The authors added this robustness check after seed 0 results existed for three judges and before any seed 1 requests. The conflict-code context, overlap splits and direct comparison of the reworded line with texts alone are exploratory. Gemini used the conflict code on 14 of 24 gap faults and recorded 0/24 right-reason catches in that context.
- Checkability: a separate implementation can reconstruct matched cases from versioned RFC links, verify the omissions, score saved replies, and recompute paired changes in catches and false alarms. These checks measure behavior on the selected replacements and decoys. They leave the judge's reason for deferring to the record unresolved.
- Reproducibility signals: the paper describes a public release of code, sampled items, judge replies, metadata, and the retrieved RFC index. The repository was not opened. Pre-specification is a private timestamped record with amendments and a released provenance description. The text identifies it as internal and gives no public registration. An AI coding assistant from the same developer as one judge drafted the plan, wrote the harness, analyzed the replies and drafted the manuscript.
- Authority signals: the arXiv preprint describes independent work and lists university educational affiliations. The text states no peer-reviewed acceptance. These facts inform confidence and leave the grade determined by design and coverage.

## Limitations

The controlled result covers whole-document replacement in one family, RFCs, using titles, dates, and abstracts. Random omissions may differ from systematic gaps in production records. Decoys match title resemblance, but abstract overlap remains imbalanced. Some update decoys introduce newer protocol versions a reader could reasonably prefer. The appended rooftop-solar case study is descriptive because its answer key and scorer agreement failed the planned quality checks, which were replaced with reporting before the test runs. The private planning history and assistant provenance matter for assessing how independently the test was specified. The paper describes author review and amendment of the plan. Hosted judges ran once per prompt through a proxy with undisclosed temperature and seed, which constrains exact reruns, and the overlapping draws provide partly reused evidence. Changes following the note or warning are compatible with a return to text-only behavior because catches and update false alarms return together.

## Suggested Update

Disposition: fold-a-narrow-warning. For principles 4 and 5, include matched record omissions and update-only controls when judging whether RFC citations remain in force, and report misses and false flags separately. This narrows "Explicit rubrics remain sensitive to how criteria are presented and executed." The comparison supports testing record completeness and presentation before relying on an evaluator's currency score. Evidence for a generally effective warning requires independent corroboration. Expand-on: yes. Seed topics: matched record omission controls; currency checks across document families; judge calibration under incomplete records.

## Claims Needing Human Review

- Confirm whether the narrower wording about recovery and false alarms preserves the triage finding for both presentation variants and all tested judges. Claude's raw presentation result does not survive correction.
- Confirm the limits of the private timestamped provenance and the strength of the seed-1 robustness check given shared gap faults and replies.
- Confirm whether the warning should apply only to RFC currency tasks until a different document family yields a comparable controlled result.
