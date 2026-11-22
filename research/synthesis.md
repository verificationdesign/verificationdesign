# Evidence Synthesis by Claim

This additive accumulator gathers reviewed evidence under claims rather than sources. It has no authority over `verification_design.md` and does not modify or replace canonical material. Status describes the evidence currently recorded here; it does not prescribe action. Claims remain scoped to the settings described in their reviewed notes.

Section headings are filing locations for new evidence, not commentary on the principles they mirror. A principle's own supporting evidence lives in `verification_design.md`; a claim filed under a section sits beneath that principle and neither supports nor qualifies it. An empty section means that principle has no unfolded evidence here, not that it is unsupported.

Seeded: 2026-08-19
Header clarified: 2026-08-23
Migrated legacy Update notes: 2026-09-04
Source: dated Update notes from `verification_design.md`, preserved verbatim below.

## 1. External Signals Over Self-Review

At seeding (2026-08-19):

No claims recorded yet.

### Self-correction outcomes depend on the intervention, model, and task rather than defining one uniform capability.

Status: single-source

Evidence:
- arXiv:2510.16062, grade ungraded (legacy migration, no reviewed note), CorrectBench reports model- and task-dependent correction gains, with efficiency tradeoffs and competitive direct chain-of-thought baselines.

Tension: The note qualifies the canonical warning about self-review by distinguishing intrinsic, external, and fine-tuned correction.
What would move this: Independent comparisons across intervention types, model families, and tasks with matched compute budgets would change the Status.

Migrated callouts:
> **2026-05-30 Update**: Treat "self-correction" as a family of interventions, not a single capability. CorrectBench separates intrinsic, external, and fine-tuned correction, and reports that self-correction can help on some complex reasoning tasks while remaining strongly model- and task-dependent, efficiency-sensitive, and often competitive with a direct chain-of-thought baseline. The strongest warning in this doc applies to naive intrinsic self-review: the same model re-reading its own answer without new external information. Source: [arXiv:2510.16062](https://arxiv.org/abs/2510.16062)

### Framing an identical error as external can improve correction relative to framing it as the model's own output.

Status: single-source

Evidence:
- arXiv:2507.02778, grade ungraded (legacy migration, no reviewed note), Self-Correction Bench reports a self-correction blind spot in controlled error injection across 14 open-source non-reasoning models.

Tension: The reported setting does not establish whether the same framing effect holds for naturally occurring errors or reasoning models.
What would move this: Independent replication on naturally occurring errors and reasoning models would change the Status.

Migrated callouts:
> **2026-05-30 Update**: Self-Correction Bench offers a mechanism for weak intrinsic review: models can correct identical errors more reliably when the error is framed as external than when it is their own output. In the paper's controlled error-injection setup over 14 open-source non-reasoning models, this "self-correction blind spot" supports the practical rule to prefer independent reviewers or external verifiers; when self-review is unavoidable, force explicit reconsideration rather than a single-pass critique. Source: [arXiv:2507.02778](https://arxiv.org/abs/2507.02778)

### Reasoning text can raise false-positive trajectory judgments while actions and observations remain fixed.

Status: single-source

Evidence:
- arXiv:2601.14691, grade ungraded (legacy migration, no reviewed note), Gaming the Judge reports increased false-positive judgments after reasoning-only changes, especially fabricated progress.

Tension: The reported intervention isolates reasoning text, but the note does not establish reliability for judgments grounded in external execution evidence.
What would move this: Independent trajectory evaluations comparing reasoning-based judgments with action- and environment-grounded checks would change the Status.

Migrated callouts:
> **2026-05-30 Update**: An agent's chain-of-thought is not an external signal. Gaming the Judge shows that changing only the reasoning text while holding actions and observations fixed can substantially increase false-positive trajectory judgments, especially when the CoT fabricates progress. Treat CoT as an unverified claim stream: useful for hypotheses, but not evidence until checked against observed actions, tool outputs, and environment state. Source: [arXiv:2601.14691](https://arxiv.org/abs/2601.14691)

## 2. Independence Between Generation and Verification

### Agent authorization can separate probabilistic interpretation or action proposal from a deterministic runtime decision, conditional on the completeness of the decision evidence and mediation boundary.

Status: corroborated
Also bears on: Principle 9

Evidence:
- arXiv:2607.27267, grade C, FAVA lowers an LLM-derived permission representation into a graph for an SMT-backed decision before effectful actions in authored benchmark cases.
- arXiv:2606.22916, grade C, IGAC places a certificate-based server-side gateway between an untrusted model proposal and the action pipeline in synthetic runtime tasks.
- arXiv:2610.27620, grade C, in finite models of declassification-based purpose policies and synthetic judge scenarios, local authorization left relational violations unobservable to a per-trace monitor, while paired execution evidence let judges detect them in the tested scenarios.

Tension: The studies use different authorization representations and deterministic mechanisms, but both depend on author-specified semantic bounds and complete mediation that their evaluations do not independently establish.
What would move this: An independent evaluation using naturally occurring requests and effects, with measured extraction errors and executable mediation-bypass probes, would change the evidence description.

### Cheap and expensive rubric judges in a cascade can share confident errors, limiting the reliability gain expected from independent errors.

Status: single-source

Evidence:
- arXiv:2609.29769, grade C, across human-labeled benchmark panels, generative judges repeated high-confidence decision-model errors more often than a criterion-and-label-conditioned independence baseline predicted, and cross-fitted cascades added little over the best single judge.

Tension: The overlap estimate uses a confidence-selected slice, and cascade performance depends on the labels, tested model tiers, and threshold-fitting protocol.
What would move this: Independent held-out benchmark or live evaluations measuring fallback accuracy on routed cases across model tiers would change the Status.

## 3. Step-Level Checkpoints

### Under a declared stochastic objective and cost proxy, oversight checkpoints can be scheduled as an executable budget-allocation problem.

Status: single-source

Evidence:
- arXiv:2607.16530, grade C, a discrete algorithm globally minimizes the paper's oversight objective under stated assumptions and exposes review count, stage indices, gap sequence, proxy cost, and computed loss.
- arXiv:2610.09667, grade C, on synthetic customer-request audits, a reasoning model came close to the requested review rate while selection remained predictable from identifiers, exposing a sampling implementation issue outside the evaluation of schedule optimality.

Tension: The experiments use model-simulated reviewers, and stage or artifact-length cost proxies do not measure human attention, fatigue, interruption cost, or review time.
What would move this: A different group testing checkpoint schedules with measured human review time or cognitive cost, plus sensitivity analysis for stage-dependent error growth, would change the Status.

> **2026-11-22 Update**: The arXiv:2610.09667 entry qualifies sampling implementation and leaves schedule optimality untested. Its finding is filed under the audit sampler claim below. Source: 2026-11-22 cards and site review (lookout-cards-site-1122-report.md).

### A model-based audit sampler can approach its requested rate while its selections remain predictable from identifiers.

Status: single-source

Evidence:
- arXiv:2610.09667, grade C, on synthetic customer requests with random UUIDv4 identifiers and a requested 1% review rate, one tested model selected 0.89% of requests and its selections were predictable from identifier features. The other tested models selected fewer requests.

Tension: The isolated synthetic decisions and sparse selections limit what the study establishes about predictability in deployment.
What would move this: Independent repeated audits with identifier interventions and externally supplied draws, measuring both realized rare-event rates and predictability on operational inputs, would change the Status.

### Tool-use verification can evaluate local action errors separately from failures in multi-step rollouts.

Status: corroborated

Evidence:
- arXiv:2601.12294, grade ungraded (legacy migration, no reviewed note), ToolPRMBench uses interaction history, tool metadata, and correct versus plausible incorrect actions for offline and online PRM evaluation.
- arXiv:2610.17633, grade C, replay and fresh continuations on selected SWE-bench Verified coding-agent failures showed that many steps flagged by judges had no measured drop in success, with localization relative to the reconstructed state, fixed policy, and remaining budget.
- arXiv:2611.02978, grade C, in multi-turn BFCL simulator replays, checking calls against benchmark-defined effects exposed collateral actions missed by final-state scoring, with the reference trajectories and effect labels setting the scope of the distinction.

Tension: A benchmark structure does not by itself establish that deploying checkpoints improves end-to-end task success.
What would move this: Independent deployment comparisons measuring local error detection and final task outcomes would change the Status.

Migrated callouts:
> **2026-05-29 Update**: Tool-agent verification is becoming a step-level problem in its own right, not just an application of reasoning-chain PRMs. ToolPRMBench frames tool-use PRM evaluation around interaction history, a correct action, a plausible incorrect alternative, and tool metadata, with offline sampling for local single-step errors and online sampling for multi-step rollout failures. For systems, this supports checking tool choice, argument validity, and observed tool-state transitions at each action boundary rather than waiting for final task success. Source: [arXiv:2601.12294](https://arxiv.org/abs/2601.12294)

## 4. Adversarial Framing

### Assigning untrusted candidate text a lower-authority chat role does not reliably quarantine prompt injection against an LLM judge.

Status: single-source
Also bears on: Principle 7

Evidence:
- arXiv:2605.30521, grade B, mock-tool-result wrapping failed to consistently reduce attack success and often worsened it across the paper's tested judge models and tasks.

What would move this: Replication on different judge families and task datasets, with executable controls that isolate role placement from prompt formatting, would change the Status.

## 5. Explicit Criteria

### Explicit rubrics remain sensitive to how criteria are presented and executed.

Status: corroborated
Also bears on: Principle 7

Evidence:
- arXiv:2602.02219, grade B, randomized rubric option and criterion ordering changed judgments and altered the selected best response on 16% to 39% of prompts in the tested rubric-judging setup.
- arXiv:2606.29920, grade B, per-rubric verification accuracy varied by task, category, prompt, and batching, with batching losses becoming steep on long agent trajectories.
- arXiv:2610.13303, grade C, label-free clarification raised inter-judge agreement on held-out SummEval items without a detectable gain in human agreement, while HealthBench and USR failed to meet the registered improvement criteria.
- arXiv:2611.01311, grade C, on matched IETF RFC currency cases, an authoritative record with missing replacement links reduced judge detection relative to document text alone, and warning presentations recovered some catches with judge-dependent tradeoffs in false flags.
- arXiv:2611.18471, grade C, across frozen AgentProcessBench, ATBench, PlanRewardBench, and AgentDojo executions, simulated abstraction turned some native-correct verdicts into wrong answers or unusable verdicts under unchanged criteria, with exact provenance restoring many of those judgments.

Tension: One study manipulates presentation order while the other measures rubric execution and batching, so they agree on instability without identifying one shared mechanism.
What would move this: Independent evaluation combining balanced presentation permutations with per-rubric reliability measurements on deployed agent trajectories would change the evidence description.

### Model-generated criteria can improve externally anchored benchmark outcomes while leaving criteria provenance model-internal during refinement.

Status: single-source

Evidence:
- arXiv:2605.30568, grade C, one model generated rubrics and another selected among them without human labels inside the refinement loop, while final performance was evaluated against benchmarks with human annotations.

Tension: The external benchmark anchor makes the reported outcome interpretable, but an annotation-scarce deployment may not supply an equivalent anchor.
What would move this: A different group comparing generated and expert-authored criteria on a dataset with withheld human annotations would change the Status.

### Checklist content can set the effective pass standard, and model-driven rubric revisions can remove checks that uniquely catch failures.

Status: single-source

Evidence:
- arXiv:2610.24971, grade C, in the synthetic Recon report experiments, hand-written and generated checklists accepted different shares of correct reports, and model-driven revisions deleted checks with unique catches on labeled flaws.

Tension: The revision studies use authored reports and one model family, and the gate evaluation largely replays stored per-check judgments.
What would move this: Independent rubric-revision tests across model families on new, externally labeled tasks with live regrading would change the Status.

## 6. Executable Verification Is King

### Partially verifiable tasks can route individual criteria to deterministic checkers or semantic judges instead of using one checker for the whole task.

Status: single-source
Also bears on: Principle 5

Evidence:
- arXiv:2605.30244, grade C, a vision-language reinforcement-learning study extracted rubric criteria, deterministically checked verifiable ones, judged fuzzy ones, and hid answer-bearing information from checkers.

Tension: The evidence comes from one reinforcement-learning setting, and ordinary-response accuracy did not expose the same exploitable false positives as constructed failure cases.
What would move this: Independent criterion-routing results on non-vision agent tasks, with executable failure-case audits and checker information-ablation tests, would change the Status.

### A deterministic or automated gate can satisfy its surface metric while missing the failure class it is meant to detect.

Status: corroborated
Also bears on: Principle 1

Evidence:
- arXiv:2111.09525, grade B, a reviewed cluster of summarization-faithfulness evaluations found that overlap, entailment, question-answering, and generated-reference checks have documented blind spots and can reward unsupported summaries.
- arXiv:2605.23215, grade C, only 22 of 110 FastKernels model deployments of agent-generated GPU kernel winner sets ran correctly unchanged, exposing integration failures beyond isolated checks.
- arXiv:2610.15938, grade C, on FRANK summarization, adding a reference summary to the source reduced balanced accuracy under the principal judge's generous matching rule, with the corresponding HaluEval question-answering comparison showing improvement.
- arXiv:2611.08269, grade C, on CPython, Node.js, and SQLite migration tasks, visible assertions still released repairs that failed withheld contracts after adding an edge input, with the observed rate dependent on the authored repair menu and the oracle audit leaving contract objections unresolved.
- arXiv:2611.19237, grade C, in selected n8n workflow replays, rejection still produced the protected effect in 4 of 59 policy-comparable pairs with a visible approval gate, demonstrating a coverage gap in those workflows.
- arXiv:2611.20595, grade C, in AgentOrchBench catalog count tasks, enforcing failed invariant checks reduced wrong releases relative to warnings partly through abstention and reduced correct answers on faulted runs, with procedural passages excluded from the source review.
- arXiv:2611.14581, grade C, on tau2-bench airline and retail tasks, a transcript judge repeatedly agreed with itself yet passed human-confirmed premature writes that an expected-versus-logged write check detected, with detection partly reflecting a criterion shared with the annotators.
- arXiv:2611.02676, grade C, hash-matching evaluation packets for selected AgentProcessBench trajectories from BFCL and tau2 omitted every structured call, and restoring calls changed error flagging in one judge configuration, with supplementary tables unavailable to the review.
- arXiv:2610.38691, grade C, in sampled Into the Unknown research-agent submissions, most unsupported numerical claims referred to a value found under the wrong source context by the population-weighted estimate, exposing a gap in value-only matching.

Tension: This pre-LLM-judge source cluster supports a general validity distinction, but it does not directly test current agent-verification gates.
What would move this: Independent modern evaluation that injects known failures into an agent or LLM-judge workflow and measures which passing gates detect them would change the Status.

> **2026-11-22 Update**: The Tension and What would move this lines above describe the earlier evidence state. The evidence list now includes the gate evaluations filed on 2026-11-22. The observed misses depend on the tested workflows, fixtures, and reference judgments, and independent evaluations with known-good and known-wrong cases and separately checked reference judgments would clarify detection, false rejections, and abstentions. Source: 2026-11-22 cards and site review (lookout-cards-site-1122-report.md).

### Executable benchmark checks can pass against erroneous labels or construction rules that miss intended correctness.

Status: corroborated

Evidence:
- arXiv:2605.30504, grade ungraded (legacy migration, no reviewed note), An IRT audit of seven benchmarks reports likely label errors and 95% precision among its top 200 flagged items against consensus-plus-hand-inspection labels.
- arXiv:2611.10063, grade C, hardening the grader for stored mechanical CAD task attempts changed 18 of 519 verdicts from pass to fail, while an ambiguous task specification accounted for many silent failures in the separate primary study.

Tension: The reported precision concerns selected flagged items and its reference-label procedure, not all benchmark labels.
What would move this: Independent label audits with separately established reference judgments and measured downstream effects would change the Status.

Migrated callouts:
> **2026-06-09 Update**: Executable checks inherit the validity of their oracle. An IRT-based audit of seven preference and multiple-choice benchmarks (20986 items, responses from 114 models) surfaced likely label errors, with its authors reporting 95% precision in the top 200 flagged items against consensus-plus-hand-inspection reference labels. The error sources are instructive for verification design: mechanical construction rules that mark answers correct for satisfying the letter of a format rather than the intent, upstream annotation errors inherited unchanged across downstream variants, and items with no defensible single answer. A test that does not care what the agent thinks is still confidently wrong when its expected value is wrong. Design implication: expected values, labels, and fixtures need their own audit path; "the check passed" is conditional on oracle validity. Source: [arXiv:2605.30504](https://arxiv.org/abs/2605.30504)

### Deterministic extractive-QA comparators can disagree with human correctness judgments when gold answers or matching criteria are inadequate.

Status: single-source

Evidence:
- arXiv:2504.11972, grade ungraded (legacy migration, no reviewed note), Ho et al. report weak Exact Match and F1 correlations, discarded incorrect gold answers, and task-specific blind spots in an LLM judge.

Tension: Higher reported judge correlation does not remove the need to audit ambiguous answers or the comparison target.
What would move this: Independent extractive-QA evaluations with audited gold answers and disaggregated comparator and judge errors would change the Status.

Migrated callouts:
> **2026-06-13 Update**: A deterministic comparator can be reliable yet invalid when its oracle under-specifies correctness. In an extractive-QA setting, Ho et al. report that Exact Match and F1 had average correlations with human judgment of 0.220 and 0.404, while an LLM judge reached up to 0.85; they also discarded 39 of 200 sampled instances because the gold answer itself was wrong. The judge is not a free substitute for oracle audit: its own job-title answer correlation was 0.352, a blind spot tied to ambiguous multi-job answers. This strengthens the 2026-06-09 oracle-validity note: executable comparators and learned judges both need evidence that the target they compare against actually represents correctness. [arXiv:2504.11972](https://arxiv.org/abs/2504.11972)

### Lean compilation can accept a formalization that changes the requested meaning, and an added semantic judge can reject a faithful translation.

Status: single-source

Evidence:
- arXiv:2606.31002, grade C, on university-level natural-language-to-Lean statements, human review of the tool-augmented agent's rejected compiling outputs found both genuine mistranslations and faithful translations rejected by the semantic criterion.

Tension: Human auditing covers selected systems and subsets of textbook tasks, leaving broader translation fidelity and acceptance-error rates uncertain.
What would move this: Independent Lean evaluations with blinded human audits of both accepted and rejected outputs on fresh tasks would change the Status.

## 7. Cross-Family Beats Self-Verification

### Candidate-aware cross-family judges can share exploitable false-positive basins when their judgments track plausibility rather than correctness.

Status: single-source

Evidence:
- arXiv:2607.05904, grade B, optimization exploited reference-based judges in tested low-accuracy regimes, while candidate-independent blind-solve signals reduced the shared reward-hacking channel.

Tension: Low organic cross-judge error overlap reported in arXiv:2606.29920 suggests that optimization-induced candidates and ordinary rubric-verification errors may have different correlation structures.
What would move this: A different group comparing candidate-aware and candidate-independent judges across both optimized adversarial outputs and ordinary trajectories would change the Status.

### Tightening judge criteria can change abstention behavior without improving discrimination.

Status: single-source

Evidence:
- arXiv:2606.15610, grade C, a judge-datasheet protocol found that criterion changes could suppress false preferences by increasing abstention rather than improving discrimination.

Tension: The authors present the result as measurement groundwork rather than evidence of broad downstream effects.
What would move this: Ecological replication on deployed evaluation tasks that separately reports discrimination, abstention, and coverage would change the Status.

### LLM-judge reliability can vary across benchmarks and perturbations even when the judge comes from a different model family.

Status: corroborated

Evidence:
- arXiv:2603.05399, grade ungraded (legacy migration, no reviewed note), Judge Reliability Harness reports that no evaluated judge was uniformly reliable across its benchmarks and perturbation types.
- arXiv:2610.07359, grade C, across authored agent-action corpora, LLM judge pairs had correlated misses and clean-provenance comparisons found no cross-vendor advantage, with joint coverage sensitive to whether escalation counted as stopping the action.
- arXiv:2610.12778, grade C, on the synthetic Oracle PL/SQL migration specification benchmark, judges from different families showed no detectable binary detection advantage over a specification-length threshold despite executable controls excluding ground-truth leakage.
- arXiv:2611.04090, grade C, on Arena system comparisons, requiring cross-provider agreement increased precision among called directions while lowering coverage for pairings involving Luna and leaving co-occurring disagreement against a single preference vote per battle.

Tension: The note challenges treating model-family separation as sufficient validation, without establishing a universally reliable replacement.
What would move this: Independent harness results across additional judge families and deployed task formats would change the Status.

Migrated callouts:
> **2026-05-29 Update**: Cross-family LLM judges are not automatically reliable verification signals; they need their own validation harness. Judge Reliability Harness evaluates judge consistency and discrimination across free-response and agentic task formats, and its authors report that no evaluated judge was uniformly reliable across their benchmarks and perturbation types. For systems, this suggests treating LLM judges as calibrated instruments: use perturbation tests, report observed judge behavior, and prefer executable checks for claims that can be made verifiable. Source: [arXiv:2603.05399](https://arxiv.org/abs/2603.05399)

### Mitigations for chain-of-thought manipulation can leave residual judge errors while removing reasoning text can reduce recall.

Status: single-source

Evidence:
- arXiv:2601.14691, grade ungraded (legacy migration, no reviewed note), Gaming the Judge reports incomplete mitigation from prompts, rubrics, and extra compute, alongside recall costs from removing chain-of-thought.

Tension: Reducing reasoning exposure and retaining useful detection signals can pull precision and recall in different directions.
What would move this: Independent comparisons reporting precision and recall for mitigations with external action and environment evidence would change the Status.

Migrated callouts:
> **2026-05-30 Update**: Cross-family judging does not make chain-of-thought safe as a verification surface. Gaming the Judge reports that manipulation-aware prompts, rubric changes, and extra judge compute reduce but do not eliminate CoT manipulation, while removing CoT can reduce recall. The design implication is not "never show CoT"; it is to ground any CoT-derived judgment in action logs, tool results, and environment evidence, and to report the resulting precision/recall tradeoff. Source: [arXiv:2601.14691](https://arxiv.org/abs/2601.14691)

### Judge debiasing validated on a static audit distribution can leave or redirect bias under subsequent optimization.

Status: single-source

Evidence:
- arXiv:2605.27996, grade ungraded (legacy migration, no reviewed note), Reward Bias Substitution reports indistinguishable audit observables for different mitigation outcomes and empirical proxy shifts under optimization.

Tension: The reported identifiability result and tested optimization settings do not validate a general replacement debiasing method.
What would move this: Independent evaluations tracking multiple bias features under the distributions induced by optimization would change the Status.

Migrated callouts:
> **2026-06-09 Update**: "Debias the judge" is not a dependable fix. Reward Bias Substitution proves that under any audit-distribution scoring, even with oracle access to the true reward, successful mitigation, bias substitution, and overcorrection produce identical observables; single-axis fixes for length, sycophancy, or style can rotate optimization pressure onto correlated proxies instead of removing it. Empirically, a length penalty under GRPO compressed responses while driving the policy into overconfidence and lower free-form accuracy, and a published length-debiasing operator that zeroed reward-length correlation on the audit set reintroduced the bias under best-of-N selection on three of four reward models tested. The transfer to verification design: a debiased judge is only certified under the distribution the optimized system actually induces, with multiple bias features tracked at once, and a single-axis debiasing claim validated on a static audit set is an unverified claim. This strengthens the existing stance: prefer executable checks over patched judges. Source: [arXiv:2605.27996](https://arxiv.org/abs/2605.27996)

### Judge reliability measurements can depend on task-specific consistency under perturbation before human alignment is assessed.

Status: single-source

Evidence:
- arXiv:2602.00521, grade ungraded (legacy migration, no reviewed note), An IRT framework measures intrinsic consistency before human alignment and reports different reliability outcomes for summarization and dialogue scoring across seven judges.

Tension: The framework supplies a measurement order, but the note does not establish universal acceptance thresholds across tasks.
What would move this: Independent task-level replication with prespecified consistency thresholds and separate human-alignment measurements would change the Status.

Migrated callouts:
> **2026-06-09 Update**: Judge validation is becoming a measurement discipline. An Item Response Theory framework formalizes judge reliability in two ordered phases: intrinsic consistency first (stability of the judge's latent quality estimates under typo, line-break, and paraphrase perturbations, with explicit acceptance thresholds), then human alignment, which is only meaningful for judges that pass the consistency phase. Across seven judges, reliability varied sharply by task: summarization judging held up while dialogue understandability scoring fell well below the framework's reliability threshold. For harness design this sharpens the 2026-05-29 note: perturbation tests with stated thresholds come before any alignment claim, and validation is per task, not per judge. Source: [arXiv:2602.00521](https://arxiv.org/abs/2602.00521)

## 8. Simulate Debate

No claims recorded yet.

### The effect of agent discussion can depend on who judges and how judgments are collected, and shared discussion can increase wrong unanimity relative to private judgment.

Status: corroborated

Evidence:
- arXiv:2610.28539, grade C, on author-written science and technology statements, pre/post accuracy shifts differed across human and model supervisors, and homogeneous and diverse model panels moved in different directions during deliberation under the tested protocols.
- arXiv:2610.35930, grade C, on fully parsed non-numeric MAD Bench questions with reference labels, homogeneous model groups reached wrong unanimity more often after peer discussion than after round-matched independent reflection, with a separate debate judge outside the tested protocol.
- arXiv:2606.02282, grade C, on TradingAgents failure-attribution trials, sharing a common summary lowered exact-match accuracy for the affected backbones and increased unanimity relative to private voting, with scoring dependent on the supplied true culprit count.

Tension: The studies use different supervisor populations, tasks, and protocols, with authored or benchmark-defined labels and limited evidence about adversarial debate with a separate judge.
What would move this: Independently labeled tasks that compare debate, private revision, and separate-judge protocols at matched budgets across supervisor populations would change the evidence description.

## 9. Isolate Verification from Ambient State

### Operator-facing approval, cancellation, timeout, and authorization controls govern external effects only when the enforcement path completely mediates those effects.

Status: corroborated
Also bears on: Principle 2

Evidence:
- arXiv:2607.14166, grade B, deterministic probes across pinned agent frameworks reproduced cases where a control-flow primitive paused or terminated one path while a related external effect still committed.
- arXiv:2607.27267, grade C, a permission-graph solver can decide over represented evidence, while missed labels, sinks, dependencies, or gateway bypasses remain outside its guarantee.
- arXiv:2606.22916, grade C, certificate-based narrowing constrains proposed calls only under correct effect bounds, gateway logic, and complete mediation.

Tension: The framework probes directly exercise shipped control primitives, while the authorization papers evaluate authored prototypes and synthetic cases; none establishes complete mediation in production deployments.
What would move this: Independent end-to-end probes that compare each control decision with realized external effects across framework-local and structural enforcement boundaries would change the evidence description.

### Task-completion context can alter an agent's permission decisions even when the permission dialog is held fixed.

Status: single-source
Also bears on: Principle 4

Evidence:
- arXiv:2608.04755, grade C, controlled fixed-popup comparisons found task-context-conditioned permission grants and showed that some prompt mitigations lowered wrongful grants by also suppressing legitimate grants.

Tension: The dialogs and application distribution were narrow, and separation of task execution from authorization remains unevaluated.
What would move this: Independent replication using naturally triggered dialogs, more applications and permission types, and joint legitimate-grant and wrongful-grant measurements would change the Status.

### Output-only checks and checks of agent-editable records can leave execution identity unresolved, and independently held records can preserve evidence whose coverage and interpretation still require checks.

Status: corroborated

Evidence:
- arXiv:2610.21135, grade C, in controlled DIB-Bench deployment changes, output scoring often accepted altered stacks, while manifest checks detected measured changes under an assumed trustworthy measurement path and missed changes to undeclared components.
- arXiv:2611.23335, grade C, on single-function coding tasks, a host-signed record preserved events omitted from an altered transcript in a scripted demonstration, and detectors differed on recorded violations, with procedural passages excluded from the source review.

Tension: Deployment manifest coverage and signing key isolation are study assumptions, and the edited-transcript comparison used scripted agents and keyword stand-ins.
What would move this: Independent comparisons on live systems with audited capture coverage, custody, and separately calibrated interpretation would change the evidence description.

## Unassigned

### Human involvement in a verification or decision workflow does not by itself establish scrutiny or uptake of available evidence.

Status: corroborated

Evidence:
- DOI:10.1177/0018720810376055, grade B, a systematic review of human automation studies found automation bias and omission or commission errors across decision-support settings, with accountability among the reported mitigations.
- arXiv:2512.01241, grade C, an abstract-only medical study reported that AI-assisted physicians omitted valuable recommendations and that omission accounted for more than 80% of severe errors in its consultation setting.

Tension: The systematic review predates current LLM workflows, while the medical preprint does not expose arm denominators or distinguish inattention from disagreement, workflow friction, or justified rejection.
What would move this: Observable attention and uptake measures in an LLM workflow, with controls separating non-attention from deliberate rejection, would change the Status and clarify whether the claim attaches to Principle 1 or Principle 3.

### Returning content to its human source is the closest qualitative-research analog to source-based fidelity checking, but its efficacy is contested.

Status: single-source

Evidence:
- DOI:10.1177/1049732316654870, grade B, a critical review of member checking describes several forms of returning findings to participants and records conflicting views about validity benefits, epistemic fit, burden, and possible distortion.

Tension: The reviewed literature does not support treating participant confirmation as reliable positive fidelity evidence, and qualitative member checking is not an agent-verification experiment.
What would move this: A controlled study that defines fidelity independently and compares source confirmation with other verification signals would change the Status and clarify whether the claim attaches to Principle 1.
