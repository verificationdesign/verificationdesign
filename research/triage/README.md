# Research Triage

Triage files are the judgment layer between mechanical scouts and reviewed source notes.

Use triage when a scout result looks potentially relevant but has not yet earned a full reviewed note. Triage may include paraphrases, key findings, initial labels, and possible impact on the canonical doc. It is not a citation source for `verification_design.md`.

Use controlled decision values so promotion signals are machine-readable: `promote`, `keep-in-triage`, `keep-in-scout`, or `ignore`.

## Flow

1. `research/scouts/`: mechanical retrieval. What exists?
2. `research/triage/`: first-pass judgment. What might matter, and why?
3. `research/reviewed/`: source review. What do we believe after inspection?
4. `verification_design.md`: canonical synthesis. What changes in the principles?
