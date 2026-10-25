# Research Scouts

Scout files are mechanical discovery artifacts. They are generated from explicit arXiv categories, keyword groups, and date windows; they are not evidence reviews and contain no model judgment.

`config.json` is the project profile shared by verify, scout, and digest. Its top-level keys are `anchor_phrases`, `expand_on`, `categories`, `keyword_groups`, `principles`, `canonical_docs`, and `digest_heuristics`.

Use `python3 -m research_tools scout` to generate a scout file, then decide which candidates deserve reviewed source notes under `research/reviewed/`.

## Review Labels

- `challenges`: contradicts or undermines something currently believed.
- `narrows`: adds a caveat or boundary condition to an existing belief.
- `extends`: adds a new method or result without overturning the current position.
- `operational technique`: directly usable method, eval, recipe, or metric for checking agent work. A system that performs a task an agent might do (an access decision, a search, an extraction) is not one, even when it is well specified.
- `ignore`: out of scope, low signal, or duplicate.

Keep the raw scout output intact when possible. Put judgment in a separate review note or decision log.

## Relevance Rule

The lens is verification of agent work: checking whether what an agent produced or did is correct, safe
and within scope, and deciding how that checking is designed, allocated and trusted. The principle
headings and prose of `verification_design.md` (principles 1 to 9) and the `expand_on` entries in
`research/scouts/config.json` record the current beliefs.

Core rule: keep an entry when its finding is about the check. Drop it when its finding is about the thing
being checked or trained. Shared vocabulary (verifier, reward, sandbox, routing, budget) is not relevance.

The independent-variable test asks: what does the paper vary or stress-test, and what does it hold
constant?

1. Verifiable rewards, RLVR, process reward models, execution feedback.
   - Drop: the verifier, reward or sandbox is held constant as a fixed environment, and the paper varies
     the training algorithm, credit assignment, exploration, distillation, data, or policy architecture.
   - Keep: the paper varies or evaluates the verifier itself, measures its false passes, false fails or
     coverage gaps, or studies how a policy exploits or games the check.
   - A training reward counts as the check only if the paper measures the reward's accuracy as a check
     (false passes, false fails, coverage). Redesigning a reward so the policy trains better, and reporting
     only the trained policy's results, is learner-side: drop.
2. Test-time search guided by a verifier (best-of-N, tree search, verifier-guided decoding).
   - Drop: the verifier or PRM is taken as given and the paper innovates only on the search algorithm or
     inference efficiency.
   - Keep: the paper studies how verifier errors, calibration or granularity degrade or bound the search
     or selection.
3. Routing, allocation, delegation, budgets.
   - Drop: choosing which generator model or how much compute answers a request, to trade cost against
     answer quality; orchestration or coordination methods that improve task capability.
   - Keep: choosing whether to verify, which verifier or judge to invoke, how to cascade cheap checks to
     expensive ones, when to escalate to a human, or how much autonomy or authority to grant an agent
     based on uncertainty or risk; and handing work to agents under oversight.
4. Sandboxes, permissions, authorization.
   - Drop: "sandbox" meaning a benchmark game, simulation or environment used to measure capability.
   - Keep: a containment boundary, permission scope or execution isolator that is specified or tested.
   - Attack automation, working exploits and jailbreak payloads stay out of this repo regardless; a paper
     whose contribution is an attack is `ignore` unless its finding is a verification or mitigation result
     stated at methodology level.
5. Everything else on the lens (judges and their reliability, self-correction limits, independence and
   cross-family checking, step-level checks, sycophancy, explicit criteria and rubrics, debate, state
   isolation, CoT faithfulness, the expand-on topics): keep when the finding bears on how agent work is
   checked; drop domain benchmarks that only measure capability.

Label briefs should quote or reference this section instead of restating the lens.

Calibration: on 2026-10-25, this repo measured labeling relevance agreement in a blind three-family
calibration on 40 entries. On the 30 entries where the earlier codex and claude labels split, the
three-labeler Fleiss kappa rose from -0.38 (earlier codex and claude labels plus the agy tie-break) to
0.58 under this rule; over all 40 it was 0.71. A 662-entry relabel under the clarified rule gave
codex-agy kappa 0.74. These are this repo's own labeling measurements, not research claims. The rule
was adopted by maintainer decision on 2026-10-25.
