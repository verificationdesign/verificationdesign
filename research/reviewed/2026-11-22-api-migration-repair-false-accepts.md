# Accepted but Wrong: Silent Failures of LLM Code Repairs after API Migrations

Reviewed: 2026-11-22
Reviewer: Codex draft; human review pending
Source: https://arxiv.org/abs/2611.08269
Evidence grade: C
Grade confidence: high

## Why It Matters

A migration can pass executable assertions on familiar inputs while violating the obligation that motivated the repair. The study measures what a release gate lets through against withheld contracts. It also shows how the measured miss rate depends on which wrong repairs are available to test.

## Method / Evidence

Read: arXiv v2 abstract and full paper (arXiv HTML, local text extraction, 2026-11-22).

- Population and design. The authors build 73 tasks on CPython, Node.js, and SQLite, with 66 affected tasks in 60 documented-change clusters. The test partition has 52 affected tasks in 49 clusters. The main stages exhaustively execute finite menus of author-written fragment combinations. Visible consumer assertions decide release. Withheld inputs and contracts assess output correctness and file preservation. The tables report task means for exhaustive results, while preregistered tests use documented-change cluster means.
- First menu. In the descriptive summary across affected test tasks, the task-mean share of hidden-wrong procedures released over the complete repair space is 0.410 on typical inputs and 0.065 with one author-written release-note edge input. False rejection among hidden-correct procedures stays at 0.010. The corresponding cluster means for false acceptance are 0.406 and 0.064. The preregistered contrast on 15 new test clusters yields 0.471 to 0.061, strict Holm p 0.002 and frozen-code p below 0.001. Its result was known at the initial freeze.
- Hard menu. The preregistered overall edge-input test is positive, with task-mean false acceptance of 0.058 across hidden-wrong procedures in the complete hard menu. In the narrower descriptive subset of 23 test tasks with hard wrong programs, the task mean is 0.168. The post hoc pooled share is 0.104, or 31 of 297 hard wrong test programs. These programs match legacy outputs on typical inputs by construction.
- Fragment model repairs. With 456 test attempts per arm and model, cluster means of wrong releases per attempt fall from 0.233 to 0.057 for Qwen3-8B and from 0.181 to 0.020 for gpt-oss-20b in the confirmatory first-menu edge-input contrasts. The qwen3.6-35b-a3b and GPT-5.6-luna fragment results are descriptive. Self-test inputs fail the preregistered replication criterion. The smallest adjusted p is 0.132 under strict Holm and 0.088 under frozen code, both for gpt-oss-20b.
- Free-form addendum. Over clean-running, hidden-wrong model-written candidates, cluster-mean false acceptance falls from 0.517 to 0.114 for confirmatory gpt-oss-20b, based on 43 candidates in 22 clusters (Holm p 0.001). The directional test is supported and the predicted ceiling of 0.10 is missed. The secondary qwen3.6-35b-a3b contrast is 0.653 to 0.113 on 65 candidates in 25 clusters. Descriptive GPT-5.6-luna results are 0.713 to 0.481 on 23 candidates in 9 clusters. The authors call comparison to the exhaustive fragment rates coarse because the candidate populations differ. Decoding and revision protocols also differ.
- Checkability. Given the finite menus, pinned runtimes, and withheld contracts, replay can enumerate candidate outcomes and independently recompute each gate decision and residual miss rate. This checks coverage against the declared benchmark oracle. The intended consumer obligation and transfer to repairs outside that menu require separate evidence.
- Reproducibility signals. The authors offer task specifications, withheld contracts, pinned sources, code, freeze records, and call and verdict logs on request. The paper says the materials are unavailable on a public code host. The package was outside the materials inspected here.
- Authority signals. The arXiv preprint lists university and industry affiliations and shares all four authors with the related study identified below. These facts tune confidence. The grade rests on the method and the two studies share an author group, so they provide no independent corroboration of each other.

## Limitations

The authors construct the repair menus and the visible and hidden cases. Their edge-input quality rule requires visible failure of the stale procedure. The audit flagged 34 of 73 contracts and the predeclared strong-evidence criterion failed. Human review of assertion strictness was post hoc and leaves the class-label objections unresolved. The task and cluster averages depend on the menu composition. The free-form addendum conditions false acceptance on parsed candidates that run cleanly, with small wrong-candidate populations and an analysis script written after the runs.

## Suggested Update

Disposition: fold-a-narrow-warning. For principles 4 and 6, derive executable checks from the documented behavior change and measure the residual false-pass rate using plausible wrong repairs and withheld checks. Visible release checks pass repairs that fail the withheld contracts, an example of "A deterministic or automated gate can satisfy its surface metric while missing the failure class it is meant to detect." The hard-menu result measures release-check coverage in the tested migration setting. A general effectiveness claim needs independent corroboration. Expand-on: yes. Seed topics: migration contract coverage; held-out behavioral changes; repair-menu composition sensitivity.

## Claims Needing Human Review

- Check the triage's conversion to percentages against the source's decimal task means and distinguish those from the cluster-level tests and per-attempt estimates.
- Check the weight assigned to the known-at-freeze result and the unresolved contract objections before folding the warning.
- The present study and arXiv:2611.07483 share all authors. Confirm the relationship between their task sets before citing both as evidence.
