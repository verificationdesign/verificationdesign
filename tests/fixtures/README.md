# Captured record fixtures

Date: 2026-09-11

`scout-sample.md` is a verbatim selection from the local, untracked
`research/scouts/scout-2026-06-09.md`: its complete header, first ten Review Queue
and Deduped Candidates entries, and matching entries in its first three category
sections (`cs.AI`, `cs.CL`, `cs.LG`). IDs in order: 2510.11194, 2601.19921,
2602.01146, 2603.01421, 2603.19225, 2605.04356, 2605.28829, 2606.01770,
2606.03303, 2606.03660. The header describes the original full run. No capped or
per-category overflow markers occur in any of the six local artifacts. Synthetic
parser tests exercise the current renderer's capped heading syntax separately.

`triage-sample.md` contains the complete header and first three candidate blocks
from tracked `research/triage/2026-05-31-llm-judge-scout.md`: Reinforcement Learning
with Robust Rubric Rewards, Personalized Turn-Level User Conversation Satisfaction
Benchmark, and Code-QA-Bench. None of the four tracked notes contains an extra
third-level section. A synthetic extension in the parser tests checks preservation.

These are format fixtures copied as source excerpts, not newly reviewed evidence.
Expected fields in the tests were transcribed from these excerpts independently
of parser output. Trimming only removes entire entries or sections.

`config-sample.json` is synthetic marine-biology topic data. It intentionally
orders principle IDs differently from their numeric order and uses relative paths
that do not exist, to check ordering and the absence of path resolution.

## OAI and scout port fixtures, 2026-09-12

`oai-listrecords-sample.xml` was captured by the architect from the arXiv
OAI-PMH ListRecords endpoint on 2026-09-12 (responseDate 00:11:20 UTC),
with set `cs:cs:AI`, from/until `2026-09-08`, metadataPrefix `arXiv`.
It contains the real records 2609.01788 and 2609.02746, no deleted record,
and no resumption token. The record fields asserted in `test_arxiv_oai.py`
were transcribed from the XML, including the complete abstracts.

`oai-norecordsmatch.xml` is the architect's original far-future-window capture
(responseDate 2026-09-12 00:11:30 UTC). Despite the filename, its actual error
is `badArgument`, with reason `until date too late`. It remains unchanged.
The test asserts that error. A separate test changes just the envelope error
code/text to synthetic `noRecordsMatch`. Pagination and deletion tests likewise
wrap the captured record bodies in synthetic envelopes; the test helpers label
these edits. HTTP 503/429 responses and Retry-After headers are synthetic.

`scout-rendered-golden.md` was generated before removing the legacy scout
script at revision `a73d9ec`: its code was copied to a tempfile, imported with
`importlib.util`, and its `parse_record` and `render_markdown` were run offline.
Both XML captures above were read; only the ListRecords capture contributes
records. Fixed inputs: from/until `2026-09-08`, category `cs.AI`, group
`fixture_topics`, anchors `llm` and `AI`, topics `evaluation` and `prediction`,
no expand-on entries, no ledger, no caps, and both IDs new. Legacy substring
matching supplied the match lists. Records are in capture order and each has
`appeared = ["cs.AI"]`. `test_scout.render_inputs` reproduces these inputs with
literal match lists; tests compare render bytes to the golden and round-trip
those bytes through the shared scout parser and renderer.

The expected dry-run lines in `test_scout.py` were captured from the old command
with the real config and fixed start/end `2026-09-08` before removal. The matching
table in `test_matching.py` was written before `matching.py`; its accepted
inflection suffixes are `s`, `es`, `ed` and `ing`, widened from `s` and `es` on 2026-09-12
after a live scout run showed `sandboxed` missing the `sandbox` keyword.

## Digest port fixture, 2026-09-12

`digest-golden.md` was generated with the legacy digest script at revision
`f2c6d00`, before its removal, using `/Users/home/.local/bin/python3.13`.
Arguments: `--input tests/fixtures/triage-sample.md --outfile
tests/fixtures/digest-golden.md --decision all --source-label fixture`.
The output contains all three fixture candidates. The permanent test compares
new command output bytes to this captured output, without regenerating it.
The synthetic marine profile also supplies ordered digest heuristics; tests
reverse overlapping entries to check first-match precedence.
