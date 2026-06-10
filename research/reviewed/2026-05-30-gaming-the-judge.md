# Gaming the Judge: Unfaithful Chain-of-Thought Can Undermine Agent Evaluation

Reviewed: 2026-05-30
Reviewer: Human + Codex
Source: https://arxiv.org/abs/2601.14691
Evidence grade: B
Grade confidence: medium

## Why It Matters

Gaming the Judge directly affects verification design because it tests whether an agent's chain-of-thought is a reliable evidence channel for trajectory-level judging. The paper reports that rewriting chain-of-thought while holding actions and observations fixed can substantially increase false-positive judgments, which supports treating CoT as a claim to verify rather than evidence by itself.

## Method / Evidence

The arXiv abstract describes a benchmark of more than 800 web-agent trajectories in which a state-of-the-art VLM judge is evaluated under manipulated chain-of-thought. The paper distinguishes style-based and content-based manipulations, with fabricated-progress content manipulations reported as more effective. It reports false-positive rates up to 90%, and says mitigations such as manipulation-aware prompting, rubric refinements, and additional inference compute reduce but do not eliminate the problem.

## Limitations

The reviewed source was the arXiv abstract page, not a full paper or artifact audit. The headline false-positive rate should remain scoped to the paper's evaluated web trajectories, judge setup, and manipulation methods. The result does not imply CoT should always be removed; the abstract reports that removing CoT can reduce recall.

## Suggested Update

Append notes under Principles 1 and 7 clarifying that CoT is not a standalone verification surface. A verifier should check reasoning claims against observed actions, tool outputs, and environment state.

## Claims Needing Human Review

- Whether the full paper supports using "up to 90%" in the canonical doc, or whether a more conservative paraphrase is preferable.
- Whether to add a new anti-pattern for treating CoT as evidence.
- Whether this should be paired with a broader CoT faithfulness source before changing any headline language.
