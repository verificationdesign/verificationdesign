# Automation Bias and Overreliance

Reviewed: 2026-06-30
Reviewer: Human + Codex
Source: https://doi.org/10.1177/0018720810376055
Evidence grade: B
Grade confidence: high
Disposition: held (2026-06-30)

## Why It Matters

This note gives design support to the rubber-stamp antipattern, as a judgment about verification design rather than a direct LLM finding. A human gate that does not actually scrutinize the output has the same failure shape as the determinism-not-validity antipattern: the gate passes by default and does not catch its target failure class. Automation bias is why human approval has to be a semantic gate, not ceremony.

It also gives qualified support to the interview pattern's cost premise. Checking against a held reference is cheaper and more reliable than verifying truth from scratch, but only when the reviewer actually holds the reference. The interview pattern is the favorable case because the human is the source.

Source anchoring is therefore double-edged. It can lower verification cost or breed rubber-stamping, depending on whether it really reduces the reviewer's cost and whether the reviewer has an independent reference. "Anchoring makes the human review tractable" is not a clean claim.

Accountability remains a useful mitigation to carry forward. A signed-approve and land gate is an accountability mechanism, which counts in its favor.

## Method / Evidence

The core automation-bias evidence is robust and well-replicated in classic human-factors settings. In a false-fire-warning task, commission errors were near 100%, omission errors were about 55%, and unaided participants outperformed imperfectly-aided monitors [doi:10.1006/ijhc.1999.0252]. In a wrong automated diagnosis task, about 35 to 50% followed the wrong diagnosis, with commission rates of 42.9%, 50%, and 35.7% across automation levels, versus 92.9% correct in the unaided control [doi:10.1177/1555343411433844].

The failure was not simply failure to inspect the data. Of 18 participants who followed the wrong recommendation, 11 had checked all parameters needed to detect the contradiction, which supports a looking-but-not-seeing interpretation [doi:10.1177/1555343411433844] [doi:10.1177/0018720810376055]. Automation bias appears in experts as well as novices and is not removed by simple practice, training, or instructions [doi:10.1177/0018720810376055]. Incorrect automation is more harmful than automation merely absent [doi:10.1177/0018720815581940]. Social accountability lowers both omission and commission errors [doi:10.1006/ijhc.1999.0349].

The verification-cost evidence supports the cost premise, with care. Vasconcelos et al. model overreliance as a strategic cost-benefit decision: explanations reduce overreliance only when they lower verification cost, and the most salient visual-provenance explanation drove average overreliance to 0% in a simulated-AI maze task with N=731 [doi:10.1145/3579605]. The caveat is that the task used simulated AI, not real LLM output.

Zhang, Buchner, Liu, and Butz found that feature explanations reduced agreement with a wrong AI on EASY decisions, where a reference was available, but increased it on HARD decisions, where no reference was available. The easy main effect was OR=2.99 [1.3, 6.83], and the difficulty by explanation interaction was OR=0.11 [0.02, 0.64], with N=200 [doi:10.1145/3670653.3670660]. This directly supports the design premise that checking against a given reference is cheaper and more reliable than verifying truth from scratch.

The provenance and anchoring evidence is double-edged and weaker, so it should be treated as C/medium in-text support rather than the load-bearing basis for a fold. In a RAG confabulation study, humans added no value, with 0.572 versus system 60%; detection was poor at 0.211; reliance barely differed between correct and wrong answers, at 0.812 versus 0.789; and reliance was sometimes higher on confabulated answers. Reinhard et al. 2025 report N=97, with a late-breaking, non-significant ANOVA result [doi:10.1145/3706599.3720249]. A survey also reports that fluent, confident, polished style is conflated with reliability, raising over-trust [arXiv:2509.08010]. That survey is C/medium support whose direction is corroborated.

## Limitations

The classic automation-bias evidence is human-factors work in aviation and process-control monitoring. Transfer to LLM-mediated authoring and review is by analogy, which is why this note is graded B, with A-grade classics in a distant domain, rather than A.

Reinhard et al. 2025 is late-breaking with a non-significant ANOVA, so it is C/medium support. arXiv:2509.08010 is a survey whose direction is corroborated, also C/medium.

Vasconcelos et al. 2023 uses a simulated-AI maze task, not real LLM output.

## Suggested Update

Disposition is held. Do not fold this yet. Treat it as corroboration material for a future canonical treatment of the rubber-stamp or human-approval-as-semantic-gate antipattern, a sibling of the parked determinism-not-validity fold. The accountability mitigation, especially a signed-approve gate, is a point in favor.

Per the fold-in bar, the LLM-transfer effectiveness claims need independent corroboration in an LLM setting before folding. The classic human-factors claims are strong but domain-distant. Held, not expand-on this cycle.

## Claims Needing Human Review

Whether grade B rather than C is right given the domain-transfer gap from human-factors monitoring to LLM-mediated review.

Which of these sources, if any, belong in the canonical document when the rubber-stamp or human-gate antipattern is written up.

Whether design-implication #1, mapping automation bias onto the determinism-not-validity failure shape, is a fair characterization or an overreach.
