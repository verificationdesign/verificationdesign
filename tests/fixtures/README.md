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
