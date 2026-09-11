# Triage: LLM Judge Scout Batch

Date: 2026-05-31
Source scout: research/scouts/scout-2026-05-29.md
Reviewer: Human + Codex

## Candidate: Reinforcement Learning with Robust Rubric Rewards

Source: https://arxiv.org/abs/2605.30244
Initial label: operational technique
Confidence: medium

### Abstract Paraphrase

The paper extends RLVR from fully verifiable tasks to partially verifiable vision-language tasks by using rubrics with multiple criteria. It routes criteria either through an extractor plus deterministic verifier or through an LLM judge when the criterion cannot be made deterministic, then masks information to reduce exploitable scoring shortcuts.

### Key Findings

- Proposes criterion-level verification rather than only task-level reward.
- Separates deterministic criteria from non-verifiable criteria handled by an LLM judge.
- Uses minimal exposure to hide ground truth from extractors and images from judges.
- Reports better performance than RLVR across 15 benchmarks, plus controlled audits showing fewer exploitable false positives.

### Why It Might Matter

This is directly relevant to the current question of pairing executable verification with rubric or judge-based evaluation. It may give a concrete design pattern: split rubric criteria by verifiability, route each criterion to the strongest available checker, and deliberately hide information that would let the checker exploit shortcuts.

### What Would Change In The Doc

Potentially refine Principle 6 or Principle 7 with a note that hybrid verification should be criterion-level, not just task-level. This could add nuance to "executable verification is king" by describing how to handle partially verifiable tasks.

### Decision

Decision: promote

Promote to reviewed note after reading more than the abstract. This is the strongest candidate from this scout batch.

## Candidate: Personalized Turn-Level User Conversation Satisfaction Benchmark

Source: https://arxiv.org/abs/2605.29711
Initial label: ignore
Confidence: medium

### Abstract Paraphrase

The paper builds a personalized evaluator for turn-level user satisfaction. It combines compact user memories with target-turn context, calibrates scores, and uses the evaluator to compare generic and memory-augmented assistant systems without collecting new human labels for every model.

### Key Findings

- Generic response-quality evaluation may miss personalized satisfaction.
- User memory and score calibration improve agreement with human satisfaction annotations.
- Replay with fixed state enables controlled comparison of personalized systems.

### Why It Might Matter

It is evaluation work, but its target is user satisfaction and personalization rather than verification of agent work. The memory and replay setup is adjacent to controlled evaluation, but not central to the current verification principles.

### What Would Change In The Doc

Probably nothing. At most it is background for "evaluation target must match the property being measured," but that is not a current weak spot in the doc.

### Decision

Decision: keep-in-scout

Do not promote. Revisit only if the repo later expands into personalized assistant evaluation.

## Candidate: Code-QA-Bench: Separating Code Reasoning from Documentation Memorization in Repository-Level QA

Source: https://arxiv.org/abs/2605.29277
Initial label: operational technique
Confidence: medium

### Abstract Paraphrase

The paper proposes an automated benchmark-generation method for repository-level code QA. A tool-equipped agent first explores code to produce verified answers, then questions are derived from those answers. It compares closed-book, code-only, and documented-repository conditions to separate real code understanding from documentation recall or memorization.

### Key Findings

- Uses answer-first generation so tasks are grounded in repository structure.
- Uses three evaluation conditions: no repository, code without docs, and full repository.
- Reports that code access dominates performance, while documentation adds smaller gains on doc-dependent tasks.
- Uses an LLM judge for accuracy, completeness, and specificity.

### Why It Might Matter

The answer-first design is relevant to executable verification and benchmark construction: create verified ground truth before writing prompts or questions. The three-condition setup is a useful pattern for isolating whether a model used the actual artifact or relied on memorized/documentation knowledge.

### What Would Change In The Doc

Potentially add a benchmark-design note under Principle 1 or Principle 2: generate tasks from verified observed state first, then derive questions, and include ablation conditions that remove likely shortcut channels.

### Decision

Decision: keep-in-triage

Promote only if we want a broader section on benchmark design for code/repository agents.

