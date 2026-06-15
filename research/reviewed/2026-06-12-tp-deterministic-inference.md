# Deterministic Inference Across Tensor Parallel Sizes

Reviewed: 2026-06-12
Reviewer: Human + Codex
Source: https://arxiv.org/abs/2511.17826
Evidence grade: C
Grade confidence: medium
Disposition: folded + expand-on (2026-06-14)

## Why It Matters

This paper is relevant to the reproducibility floor underneath judge-based verification. Principle 7 treats judge calibration as an operational practice, but this paper shows that there is a lower-level infrastructure condition: the same model, same input, and greedy decoding can still produce different outputs when serving configuration changes.

For LLM-as-a-judge evaluation, that means inconsistent verdicts can arise before bias, rubric quality, or prompt wording are considered. The practical lesson is to pin and record inference configuration as part of judge calibration, or to aggregate repeated judgments when infrastructure determinism is not guaranteed.

## Method / Evidence

The reviewed source was the arXiv v2 full text, dated 2026-05-29 in the local copy. The paper argues that existing LLM serving frameworks can produce different outputs for identical inputs when tensor-parallel size or batch size changes, even under greedy decoding. It attributes the mechanism to IEEE 754 floating-point non-associativity and inconsistent reduction orders, including continuous batching, Split-K kernels, collective all-reduce, and tensor-parallel sharding.

The introduction names LLM-as-a-judge as the first motivating context. The authors state that if a judge model produces inconsistent evaluation for the same inputs, comparisons become unreliable. The paper does not run a judge-task experiment; its relevance to judge verification is the motivating framing plus the underlying inference mechanism.

For the benchmark-evaluation problem, Section 3.2 evaluates the same AIME24 prompts under tensor-parallel settings 1, 2, 4, and 8. The paper reports that the outputs are all different across those configurations and that solely changing tensor-parallel size leads to over 4% accuracy variation on AIME24 for Qwen3-8B. The introduction also cites prior work by Yuan et al. 2025a for up to 9% accuracy variation on AIME; that 9% number is attributed to the cited prior work, not to this paper's own experiment.

The contribution is Tree-Based Invariant Kernels, or TBIK. TBIK enforces a fixed binary-tree reduction order for both intra-GPU matrix multiplication and inter-GPU all-reduce, so arithmetic order stays consistent across tensor-parallel sizes. The authors implement TBIK in Triton and integrate it into vLLM and FSDP. The paper claims bit-wise deterministic inference across tensor-parallel sizes and zero probability divergence between rollout and training engines in RL pipelines.

Section 5 evaluates reproducibility across four models from different families: Qwen3-8B, Qwen3-32B, Mistral-7B-Instruct-v0.3, and Llama-3.1-8B-Instruct. It uses AIME24 and AMC23 under combinations of tensor-parallel sizes and batch sizes, with Qwen3-32B evaluated under fewer tensor-parallel settings because of GPU memory limits. Under vanilla BF16, changing runtime configuration produces many unique outputs. BIO reduces some batch-size variation but does not handle tensor-parallel variation. BIO plus TBIK reduces the average count of unique outputs to one and yields strictly zero average maximum probability divergence across the reported settings.

The paper also characterizes costs and RL effects. Fully deterministic inference with BIO plus TBIK introduces end-to-end latency overhead relative to BF16. The fine-grained breakdown reports Tree-Based MatMul overhead of 2% to 25% and Tree-Based All-Reduce overhead up to 10%. In the RL setting, the paper reports zero KL divergence between rollout and training engines and higher final Pass@1 for TBIK than BIO or BF16 in its GSM8K GRPO experiment.

The evidence grade is C because this is a v2 preprint and the repo-relevant claim is mostly an operational problem statement rather than a direct judge-evaluation experiment. The systems evidence for nondeterminism and the proposed kernel fix is concrete and broad enough to track, but transfer to judge workflows remains inferential.

## Limitations

The paper does not run an LLM-as-a-judge task experiment. Judge relevance comes from the paper's motivating context and the general inference mechanism.

The fix requires custom kernels and integrations rather than configuration changes available in ordinary serving stacks.

The motivating over-4% accuracy-variation example is a single-model, single-benchmark result: Qwen3-8B on AIME24. The Section 5 reproducibility evaluation is broader, spanning four models and two benchmarks, AIME24 and AMC23, under multiple runtime configurations.

The performance tradeoff is material. The paper reports end-to-end latency overhead for full deterministic inference and describes its current implementation as a demonstration that tensor-parallel-invariant deterministic inference is achievable.

## Suggested Update

Append a dated operational note under Principle 7: judge calibration should record inference configuration, including serving engine, tensor-parallel size, batch regime, decoding settings, and determinism controls. When that configuration cannot be pinned, repeated judgments or aggregation should be treated as part of the calibration design rather than as optional polish.

2026-06-14: Folded into `verification_design.md` as an Anti-Pattern entry. The maintainer chose anti-pattern framing over the originally proposed Principle 7 operational note.

2026-06-14: Disposition is folded + expand-on. Registered seed topics in `research/scouts/config.json`: deterministic inference, nondeterministic inference, batch-invariant inference, batch invariant inference, tensor-parallel invariant, tensor parallel invariant, bitwise reproducibility, bit-wise deterministic, serving configuration determinism, LLM judge reproducibility, judge consistency.

## Claims Needing Human Review

- Whether an infrastructure paper belongs in the canonical document's References at all, or should remain background for an operational practice.
- Whether the over-4% AIME24 accuracy-variation number may be quoted in the canonical document.
- 2026-06-14: Resolved by maintainer approval to quote the over-4% AIME24 number and include the paper in `verification_design.md` References.
