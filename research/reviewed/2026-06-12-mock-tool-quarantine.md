# Evaluating Mock Tool Quarantine for Untrusted Judge Inputs

Reviewed: 2026-06-12
Reviewer: Human + Codex
Source: https://arxiv.org/abs/2605.30521
Evidence grade: B
Grade confidence: medium

## Why It Matters

This paper is directly relevant to the repo's judge-robustness thread. It treats the judge prompt itself as an attack surface: untrusted candidate content is string-formatted into prompts for LLM-as-a-judge tasks, and adversarial strings can influence the grading model rather than the system under evaluation.

The key result is negative. The paper tests whether wrapping untrusted candidate content as a mock tool result, which should be low authority under provider instruction hierarchies, reduces attack success. Across the tested models and tasks, that role-based quarantine is not a verified defense and often moves in the wrong direction. For this repo, the design lesson is to red-team judge input handling on the deployed task and model rather than assuming that a chat role boundary enforces trust separation.

## Method / Evidence

The reviewed source was the full arXiv HTML for arXiv 2605.30521 v1, dated 2026-05-28. The paper studies three LLM-as-a-judge tasks: GSM8K answer grading as a binary task, MT-Bench scoring as a scalar task, and Arena-Hard-Auto v2 as a pairwise task. It tests seven victim models under prompt conditions including UserOnly, UserSys, ToolWrapped, SystemDistrust, and ToolDistrust.

The premise is that provider instruction hierarchies distinguish more and less trusted message roles. The paper cites the OpenAI Model Spec chain of command as System over User over Tool and notes that tool messages are described as having no authority. The tested hypothesis is that placing untrusted candidate content inside a mock tool result should reduce adversarial susceptibility relative to inline user or system-plus-user prompt layouts.

The attack method is automated red-teaming with a PAIR-like search over static attack strings. The paper reports mean attack success rate across 18 attacker and seed branches transferred to disjoint held-out items, with bootstrap confidence intervals for deltas.

The headline finding is that tool-wrapping does not consistently help. The authors report 60 analyzed deltas after excluding 3 Haiku-4.5 MT-Bench cells for format parsing issues. In 29 deltas, tool-wrapping has a higher attack success rate than a non-tool-wrapped condition; in only 1 delta there is inconsistent evidence of help; and 30 cells are inconclusive.

The clearest result is on GSM8K grading. Table 1 reports ToolWrapped minus UserOnly deltas of +31.6 percentage points for GPT-5.4 with 95% confidence interval +13.1 to +49.9, +26.1 for GPT-5.4-mini with interval +15.4 to +37.6, +33.7 for Sonnet-4.6 with interval +10.4 to +52.1, and +48.7 for Haiku-4.5 with interval +36.9 to +59.9. The authors summarize this as an inversion of the expected instruction-hierarchy direction for the binary task.

The scalar and pairwise tasks are more mixed. For MT-Bench, the authors caution that an initial read can make Haiku-4.5 look helped by tool-wrapping, but they exclude those cells because Haiku-4.5 often fails the expected rating format and parse rates vary sharply across conditions. Arena-Hard is the most defendable of the three tasks, yet Table 1 still reports increased attack success for several victims under tool-wrapping. Distrust-prose effects are task and model dependent rather than a reliable fix.

The paper includes a code and data release statement, pointing to https://github.com/AlignmentResearch/tool_robust_exploration.

The evidence grade is B because the paper is a directly relevant negative result with a clear experimental method, multiple tasks, seven tested victim models, confidence intervals, and a code/data release. It is not grade A because it is a v1 preprint, the attack search is static and not claimed optimal, the task set is limited, and transfer from the tested 2026 model snapshots to deployed judge systems still requires task-specific verification.

## Limitations

The paper's own limitations are material. It covers only three judge tasks, and the authors explicitly describe task coverage as limited. The attack discovery method is PAIR-like but non-optimal. The attacks are static strings rather than dynamic adaptive interactions. The evaluations use default completion API settings, and the authors show that changing reasoning effort can change attack success and the degree of inversion. The prompt-engineering space is large, including possible production agent-harness variants that were not tested.

Reviewer-level caveats: the strongest result is the binary GSM8K inversion; scalar and pairwise results are mixed and model dependent. The paper does not show that tool quarantine can never work. It shows that the tested role-based quarantine cannot be assumed robust, and that in several tested settings it increases attack success.

## Suggested Update

Proposed principle home: Principle 7's judge thread, because the finding is specifically about LLM-as-a-judge robustness and extends the gaming-the-judge discussion from chain-of-thought or answer manipulation to the judge input surface itself. Principle 2 is a secondary possible home if the maintainer wants the update framed around adversarial input surfaces more generally.

Hold for maintainer adjudication before any canonical edit.

## Claims Needing Human Review

- Whether this belongs under Principle 7's judge thread or Principle 2.
- Whether any attack-success delta numbers should be quoted in the canonical document, or whether the canonical note should keep the result qualitative.
- Whether the claim "do not assume provider instruction hierarchies hold under adversarial judge inputs" is supportable as a general statement or must stay scoped to the three tested tasks and seven tested victim models.
