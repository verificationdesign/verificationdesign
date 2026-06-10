# AI Design Patterns

A catalog of 17 pattern cards for verifying the work of agentic systems, in three families:

- **Context and State**: what exists before the model acts.
- **Verification**: how claims about agent work are checked against external, executable signals.
- **Orchestration**: how roles, models, and verifiers are arranged so checking stays independent of doing.

The cards are published at [verificationdesign.com](https://verificationdesign.com/patterns/). The source of truth is [`cards/`](cards/); the site reads the cards directly and keeps no second copy.

## Card form

Each card follows the canonical Problem, Forces, and Solution pattern form, with GoF's Intent and Related Patterns. Every card pairs a Pattern with an Antipattern, names the determinism move it makes, and states the observable signal it produces. Pattern code is Python, standard library only, and must execute.

## How the catalog enforces its own rules

- [`constitution.json`](constitution.json) defines the editorial rules: required card sections, a closed vocabulary for determinism claims, and a banned-words list for vague language.
- [`scripts/lint_patterns.py`](scripts/lint_patterns.py) fails any card that breaks those rules.
- [`scripts/run_card_code.py`](scripts/run_card_code.py) executes each card's Pattern code block under a bare Python 3.13 and fails unless an assertion actually runs.

Empirical claims in cards carry citations; the evidence trail runs through the research workflow described in the repository root [`README.md`](../README.md) and [`MAINTAINING.md`](../MAINTAINING.md).
