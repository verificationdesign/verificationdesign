# Research Scouts

Scout files are mechanical discovery artifacts. They are generated from explicit arXiv categories, keyword groups, and date windows; they are not evidence reviews and contain no model judgment.

Use `scripts/scout.py` to generate a scout file, then decide which candidates deserve reviewed source notes under `research/reviewed/`.

## Review Labels

- `challenges`: contradicts or undermines something currently believed.
- `narrows`: adds a caveat or boundary condition to an existing belief.
- `extends`: adds a new method or result without overturning the current position.
- `operational technique`: directly usable method, eval, recipe, or metric.
- `ignore`: out of scope, low signal, or duplicate.

Keep the raw scout output intact when possible. Put judgment in a separate review note or decision log.
