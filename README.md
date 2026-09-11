# Verification Design

Patterns and principles for verifying the work of AI agents. Published at [verificationdesign.com](https://verificationdesign.com).

## The problem

Agentic systems fail in a recognizable way: the agent says done, and the work is not done. Asking the model to review its own output does not fix this; the review inherits the blind spots that produced the error. Reliable systems route verification through external, executable signals instead: tests, comparators, baselines, and judges that are themselves measured. The evidence behind that position, with citations, lives in [`verification_design.md`](verification_design.md).

## What is here

- [`verification_design.md`](verification_design.md): nine principles for verification design, presented as a curated position paper. Every empirical claim carries an inline citation and a matching row in the References table. New evidence is held in `research/synthesis.md` until folded by the maintainer.
- [`ai-design-patterns/`](ai-design-patterns/): a catalog of 17 pattern cards in three families (Context and State, Verification, Orchestration). Cards follow the canonical Problem, Forces, and Solution pattern form, with GoF's Intent and Related Patterns. Each card pairs a Pattern with an Antipattern, names the failure it controls, and states the observable signal it produces. Pattern code is Python, standard library only, and must execute.
- [`verificationdesign/`](verificationdesign/): the Astro site that publishes both. The site reads cards directly from the catalog; there is no second copy of the content.
- [`skills/`](skills/README.md): two operator-invoked Agent Skills, `verification-design` and `verification-audit`, that apply the principles and cards to your own work from a pinned catalog snapshot. Explicit invocation only by default.
- [`research/`](research/): the supply chain for the principles. Mechanical arXiv discovery, first-pass triage, and graded source reviews, in that order, before anything reaches the canonical doc.

## The repo enforces its own rules

The thesis here is that "looks good" is not verification, so this project does not get to use "looks good" on itself.

- [`ai-design-patterns/constitution.json`](ai-design-patterns/constitution.json) defines the editorial rules: required card sections, a closed vocabulary for determinism claims, and a banned-words list for vague language.
- [`ai-design-patterns/scripts/lint_patterns.py`](ai-design-patterns/scripts/lint_patterns.py) fails any card that breaks those rules.
- [`ai-design-patterns/scripts/run_card_code.py`](ai-design-patterns/scripts/run_card_code.py) executes every card's Pattern code block under a bare Python 3.13 and fails unless a load-bearing assertion actually runs.
- [`scripts/verify.py`](scripts/verify.py) checks link liveness, citation and reference balance, provenance of every dated update, and that the synthesis holding area is append-only.
- CI runs all of the above and refuses to deploy the site on any failure. A deployed site is a passing site by construction.

## Running the checks

```
make check         # full repo verification + full site verification
make verify-local  # mechanical checks without network
```

The full runbook, including the research workflow and site verification loop, is in [`MAINTAINING.md`](MAINTAINING.md).

## License

Code is MIT. Written content (the principles, the cards, the research notes) is CC BY 4.0, attributed to "Verification Design (verificationdesign.com)". Code samples inside the pattern cards are CC0: paste them without attribution. Details in [`LICENSE-CONTENT.md`](LICENSE-CONTENT.md).
