# Script fixtures

These fixtures exercise deterministic record validation, failure routing and rendering.
They do not establish the truth of agent judgments or replace blind host tests.

- `design-sound`: two applied cards, complete 17-card coverage, no unknowns, and rejections including one for absent applicability.
- `design-applicability-violation`: a holding exclusion rejects Comparator; five negatives isolate exclusion, absent applicability, unknown exclusion, missing condition and reordered condition failures.
- `design-resolved`: Comparator applied; Executable Analog undecided at spec stage, with a later build resolution and four resolution negatives.
- `audit-known-defect`: one self-review defect under principle 2, routed via the failure map.
- `audit-missing-evidence`: unavailable deployed behavior stays insufficient-evidence; a sound claim without evidence fails.

Each directory contains a small raw artifact, a filled record and expected markdown.
Negative records have a sibling expected JSON file with `exit_code` and exact `rules`.
The checker validates all five positive records, compares all rendered bytes and checks all twenty-two negatives.

Version 1.1.0 also covers assumptions, priority, measurements, unavailable sources,
instantiation, six audit statuses and unfilled scaffold rejection. Individual READMEs
name each new positive field and negative boundary.

Version 1.2.0 adds post-plan resolution and a referenced measurement to the undecided
Executable Analog in design-resolved, plus four resolution negatives
for an applied card, invalid date, unknown measurement id and extra key.

Design records require a `plan` with design prose and numbered checks serving applied patterns; four design-sound negatives cover a missing plan, an unserved applied card, a cited non-applied card, and a requirement id gap.
