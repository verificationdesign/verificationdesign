# Can LLMs Correct Themselves? A Benchmark of Self-Correction in LLMs

Reviewed: 2026-05-30
Reviewer: Human + Codex
Source: https://arxiv.org/abs/2510.16062
Evidence grade: B
Grade confidence: medium

## Why It Matters

CorrectBench narrows the doc's core self-correction claim by separating intrinsic, external, and fine-tuned correction. It supports replacing blanket language about self-correction with a more precise claim: naive intrinsic self-review is unreliable and model/task dependent, while external feedback remains the more durable verification signal.

## Method / Evidence

The arXiv abstract describes a benchmark evaluating self-correction across commonsense, mathematical, and code reasoning tasks, using intrinsic, external, and fine-tuned correction strategies. It reports that self-correction can improve accuracy on complex reasoning tasks, but depends strongly on model and task, carries efficiency tradeoffs, and gives limited additional benefit for reasoning models. It also reports that a direct chain-of-thought baseline can be competitive.

## Limitations

The reviewed source was the arXiv abstract page, not a full paper or artifact audit. The source updates the framing of self-correction but does not overturn the doc's preference for external, executable signals. Details such as benchmark construction, model set, and task mix should be checked before stronger claims are added.

## Suggested Update

Append a dated note under the core finding stating that "self-correction" should be decomposed into intrinsic, external, and fine-tuned correction, and that the strongest warning applies to naive intrinsic self-review without new information.

## Claims Needing Human Review

- Whether to change the bolded core finding sentence or leave it as-is with a narrowing update note.
- Whether the doc should distinguish "self-correction" from "self-review" throughout.
- Whether CorrectBench should receive grade A after full paper/artifact review.
