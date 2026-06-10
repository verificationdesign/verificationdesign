# Triage Ranking: Design Note

Date: 2026-06-05
Status: draft, pre-implementation
Scope: Pass 2 calibration on top of existing Pass 1 triage notes. Defines the contract for `scripts/rank_triage.py` and the anchor fixture it reads. Does not authorize any automated promotion to `research/reviewed/` or any edits to `verification_design.md`.

## Why this layer exists

Pass 1 (scout plus triage) produces per-candidate judgment with a `Decision:` value and an `Initial label:`. The current digest (`scripts/digest_triage.py`) then applies keyword-based read-priority scoring. That scoring does not discriminate, as the 2026-06-05 digest review observed: all 12 candidates landed at priority 1.

Pass 2 replaces keyword priority with anchor-calibrated comparative ranking. Each candidate is compared to a small set of human-tagged anchors. The output is a bucket (a reading priority), not an evidence grade. Buckets are aggregated across multiple shuffled runs; runs that mis-order the anchors are dropped.

## 1. Anchor file format

Location: `research/triage/anchors.md`.

Each anchor is a regular triage record (same fields as `research/triage/TEMPLATE.md`) with two added required fields and a provenance line:

- `Anchor role: strong | adjacent | weak`
- `Anchor source: reviewed | triage | external`. Records whether the underlying material has a full source review in `research/reviewed/`, only a triage note, or comes from outside the repo. Lets the ranker distinguish anchors backed by full review from anchors chosen purely for calibration behavior.
- `Anchor rationale:` one short paragraph, human-written, explaining why this record fills that role. Dated.
- `Tagged by:` human name and ISO date.

Constraints:

- All anchors live in one file so they are reviewed as a fixture.
- At least one record per role is required. The ranker fails closed if any role is missing.
- Anchors are slow-moving. Changes to the anchor set are a separate reviewable diff, not a side effect of running the ranker.
- Model-generated anchor rationale is not allowed. The ranker must refuse to run if `Tagged by:` or `Anchor rationale:` is missing.

## 2. Ranking input schema

Per candidate (parsed from existing triage notes, no re-fetch):

- `title`, `source`
- `abstract_paraphrase`, `key_findings`
- `triage_decision`, `triage_label` (carried through, not overwritten)

Anchor set: parsed once at start of run from `anchors.md`.

Run config:

- `runs: int` (default 3)
- `seed: int` per run; controls anchor adjacency order and candidate presentation order
- `model: str` recorded in the digest header, not chosen by the ranker

## 3. Output schema, per (candidate, run)

```
candidate_id: stable hash of source
run_id: int
seed: int
skip_reason: string, may be "none"
principle_touched: "none" | "principle-<N>" | "new-candidate"
abstract_claim: short exact phrase from candidate abstract
principle_claim: short exact phrase from the relevant principle, or "none"
versus_weak: weaker | comparable | stronger
versus_adjacent: weaker | comparable | stronger
versus_strong: weaker | comparable | stronger
```

`principle_touched` is constrained on purpose. `none` means the candidate does not engage a current principle. `principle-<N>` references an existing numbered principle in `verification_design.md`. `new-candidate` means the candidate may motivate a new principle and a human should inspect. Free-form principle language is not allowed; a small model can otherwise invent principle wording that reads plausible but does not exist in the doc.

Intra-bucket ranking is deferred. v1 collects buckets only; ranking within a bucket adds failure surface before the anchor comparison itself is shown to work.

Comparison framing is asymmetric. The prompt asks "is this weaker than the weak anchor", "is this comparable to the adjacent anchor", "is this stronger than the strong anchor" so the model has explicit permission to reject in each direction. The earlier "beats anchor: yes/no" framing is rejected because it invites yes-bias, the same Principle 4 confirmation failure visible in the 2026-06-05 digest.

Bucket derivation from the three comparisons (per candidate, per run):

- `above-strong` if `versus_strong = stronger`
- `strong-adjacent` if `versus_strong != stronger` and `versus_adjacent in {comparable, stronger}`
- `adjacent-weak` if `versus_adjacent = weaker` and `versus_weak != weaker`
- `below-weak` if `versus_weak = weaker`
- otherwise `unclassified` and treated as missing for aggregation

## 4. Inversion rules

Before aggregating any candidate buckets, anchors are themselves passed through the same three comparisons within the same run. The implied ordering must satisfy `strong > adjacent > weak`. If it does not, the run is dropped: every candidate's assignment from that run is discarded before aggregation.

Dropped runs are still recorded in the digest under a `dropped_runs` section, with the specific inversion that caused the drop. The point of the inversion check is to surface model failure on a known-ordered set; suppressing the failure defeats the check.

If all runs are dropped, the digest reports no buckets at all and surfaces only the inversions and run config.

No retries on inversion. A contaminated run stays dropped; we do not re-prompt to "fix" it.

## 5. Aggregated digest fields

Per candidate, across surviving runs:

- `median_bucket`: median across surviving runs, using the order `above-strong > strong-adjacent > adjacent-weak > below-weak`
- `bucket_distribution`: full list across runs, e.g. `[above-strong, strong-adjacent, strong-adjacent]`
- `bucket_disagreement: bool`: true if not all surviving runs agree
- `principles_touched`: union across runs, drawn from the constrained vocabulary in section 3
- `runs_used: int`
- `runs_dropped: int`

Digest header:

- Anchor file path, content hash, and date.
- Model name and full run config.
- Total candidates, total runs attempted, total runs dropped, list of inversions.

Reading buckets presented to a human:

- `above strong anchor`: read now
- `between strong and adjacent`: likely read
- `between adjacent and weak`: maybe later
- `below weak`: probably skip

Sort within the digest is by `median_bucket` then by `bucket_disagreement` descending (disagreements surface higher within a bucket, since they need a human eye more than agreement does).

## 6. Explicitly not automated

- No promotion to `research/reviewed/`. Bucket is reading priority, not evidence quality.
- No edits to `verification_design.md`.
- No re-derivation of triage `Decision:` values. Pass 1 still owns that.
- No model-generated anchors and no model-edited anchor rationale.
- No self-reported confidence anywhere. The ranker does not ask the model how sure it is, and the digest does not display a confidence number.
- No retries on inversion.
- No network fetches by the ranker beyond model calls. Abstracts come from the triage notes already on disk.

## Open questions, deferred to first run

- Anchor refresh policy. When and how does the anchor set roll? Not specified here; revisit once the first ranked digest exposes friction.
- Whether `intra_bucket_rank` should be added back in v2. Decision for v1: deferred. Buckets plus disagreement are enough.
- How the ranker is wired to the existing digest. v1 expectation: the existing keyword digest stays as a fallback; ranked digest is a separate output file, dated, parallel to it.
