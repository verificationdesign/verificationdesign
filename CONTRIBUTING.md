# Contributing

This repository is a research-notes layer: principles and pattern cards for verifying the work of AI agents, published at [verificationdesign.com](https://verificationdesign.com). It enforces its own rules mechanically, so most of this document is about the checks your change must pass.

## The easiest contribution: report an error

Every pattern card page on the site has a "Report an error" link that opens a GitHub issue. Use it for anything: a wrong claim, a dead link, code that does not run, a citation that does not say what the card says it says. An issue with a specific quote and a source beats a vague impression.

## Scope: what belongs here

In scope: verification methodology, evaluation technique, design patterns for checking agent work, and evidence about those topics.

Not in scope, and closed to contribution:

- Product-specific designs tied to other codebases.
- Offensive or dual-use material: working exploits, jailbreak payloads, attack automation. Failure classes may be described at the level needed to motivate verification, never as usable instructions.
- Marketing claims that outpace the cited evidence.

When in doubt, open an issue and ask before writing.

## Evidence standards

- Every empirical claim carries an inline citation (e.g. `[arXiv:2309.11495]`) and a matching row in that document's References table. The verifier checks both directions; an orphan in either fails.
- Claims about what a paper found should survive someone reading the paper. If you are proposing a new source, include the link; characterizing it correctly is reviewed by a human, not a script.
- Design judgment is welcome but must be presented as judgment, not research fact.

## Editing rules

- `verification_design.md` is append-only. Findings update through dated notes (ISO 8601) keyed to a principle or section; prior state is never rewritten and numbering never shifts.
- No em dashes in repo prose. Use a colon, semicolon, comma, parentheses, or a new sentence.
- Pattern cards follow the schema in `ai-design-patterns/constitution.json`: required sections, a closed vocabulary for determinism claims, and a banned-words list for vague language. The linter enforces all of it.
- Card Pattern code is Python, standard library only, and must execute as pasted under a bare Python 3.13 with a load-bearing assertion. The card-code runner fails anything else.
- The site reads cards directly from `ai-design-patterns/cards/`; never copy card prose into `verificationdesign/`.

## The gates

CI runs every check below on each push and refuses to deploy the site on any failure. Run them locally before opening a pull request:

```
make check         # full repo verification + full site verification
make verify-local  # mechanical checks without network
```

That covers:

1. `python3 ai-design-patterns/scripts/lint_patterns.py`: card schema, banned words, citation presence.
2. `python3 ai-design-patterns/scripts/run_card_code.py`: executes every card's Pattern block.
3. `python3 scripts/verify.py`: link liveness, citation and reference balance, append-only discipline, provenance.
4. `cd verificationdesign && npm run verify`: site build, type check, card lint, accessibility smoke check.

A green run is necessary, not sufficient: whether a claim is correctly characterized is a human call, and substantive changes will be reviewed slowly.

## Licensing

By contributing you agree your contribution is licensed as the repository is: code under MIT, written content under CC BY 4.0, code samples inside pattern cards under CC0. Details in [`LICENSE-CONTENT.md`](LICENSE-CONTENT.md).
