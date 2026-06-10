# Triage Digest

Scope: compact reading queue from triage notes. Not a source review.
Decision filter: promote
Input summary:
2026-06-05 local triage of 68 arXiv OAI-PMH scout candidates from the 2026-06-01 to 2026-06-04 metadata window

Total candidates shown: 12
Total candidates available after filter: 24

## 1. Reassessing Extractive QA Datasets at Scale: LLM-as-a-Judge and In-Depth Analyses

- Source: https://arxiv.org/abs/2504.11972
- Read priority: 1
- Suggested decision: promote
- Suggested label: challenges
- Topic cluster: judge reliability
- Potential doc impact: may challenge or sharpen an existing principle
- Evidence type: benchmark or eval
- Why read this: The abstract_excerpt directly addresses evaluation methodology for extractive QA, which is central to the project focus on verification through external, executable signals.
- Abstract gist: Extractive question answering datasets are typically evaluated using Exact Match and F1-score, but these metrics often fail to capture true model performance.
- Key data or claims: Exact Match and F1-score are insufficient for evaluating extractive QA performance.; Large language models can be used as judges in extractive QA evaluation.
- Credibility flags: no flags in triage note
- Human question: Whether the LLM-as-a-judge approach in the paper implements independent verification and executable checks.

## 2. Diagnosing the Reliability of LLM-as-a-Judge via Item Response Theory

- Source: https://arxiv.org/abs/2602.00521
- Read priority: 1
- Suggested decision: promote
- Suggested label: challenges
- Topic cluster: judge reliability
- Potential doc impact: may challenge or sharpen an existing principle
- Evidence type: benchmark or eval
- Why read this: The abstract_excerpt directly engages with the reliability of LLM judges, which is central to the project focus on external, executable verification over self-review.
- Abstract gist: This paper addresses the limited understanding of LLM judges' reliability in automated evaluation by proposing a two-phase diagnostic framework to assess their stability and consistency as measurement tools.
- Key data or claims: LLM-as-a-judge lacks sufficient validation through observed outputs alone.; LLM judges may not function as stable and reliable measurement instruments.
- Credibility flags: no flags in triage note
- Human question: Whether the two-phase diagnostic framework actually implements executable verification or step-level checkpoints.

## 3. Deterministic Inference across Tensor Parallel Sizes That Eliminates Training-Inference Mismatch

- Source: https://arxiv.org/abs/2511.17826
- Read priority: 1
- Suggested decision: promote
- Suggested label: extends
- Topic cluster: judge reliability
- Potential doc impact: may add adjacent technique or scope
- Evidence type: system or method
- Why read this: The abstract_excerpt explicitly mentions LLM-as-a-judge, which is a direct match to the project_focus's emphasis on verification through external signals.
- Abstract gist: Deterministic inference is becoming essential for large language model applications like LLM-as-a-judge, multi-agent systems, and reinforcement learning.
- Key data or claims: Deterministic inference is critical for LLM applications including LLM-as-a-judge, multi-agent systems, and RL.; Existing LLM serving frameworks exhibit non-deterministic behavior under varying system configurations like tensor parallelism sizes.
- Credibility flags: no flags in triage note
- Human question: Whether the proposed method for deterministic inference actually supports external, executable verification as required by the project focus.

## 4. Advantage Collapse in Group Relative Policy Optimization: Diagnosis and Mitigation

- Source: https://arxiv.org/abs/2605.21125
- Read priority: 1
- Suggested decision: promote
- Suggested label: challenges
- Topic cluster: verifiable rewards
- Potential doc impact: may challenge or sharpen an existing principle
- Evidence type: system or method
- Why read this: The abstract_excerpt directly addresses GRPO, a method within the RLVR framework, which is central to the project focus on verification via external, executable signals.
- Abstract gist: Group Relative Policy Optimization (GRPO), used in the Reinforcement Learning from Verifiable Rewards (RLVR) framework to enhance large language models' (LLMs) reasoning, suffers from advantage collapse; where rewards within a group become identical; leadin...
- Key data or claims: GRPO is prone to advantage collapse; Advantage collapse occurs when rewards within a group become homogeneous
- Credibility flags: no flags in triage note
- Human question: Whether the proposed mitigation for advantage collapse supports external, executable verification

## 5. Improving Small Language Models for Code Generation with Reinforcement Learning from Verification Feedback

- Source: https://arxiv.org/abs/2605.30478
- Read priority: 1
- Suggested decision: promote
- Suggested label: extends
- Topic cluster: verifiable rewards
- Potential doc impact: may add adjacent technique or scope
- Evidence type: benchmark or eval
- Why read this: The abstract_excerpt explicitly mentions 'programmatically checkable signals such as unit-test outcomes' and 'direct optimization for functional correctness,' which directly align with the project focus on external, executable signals for verification.
- Abstract gist: This paper explores the use of reinforcement learning with verifiable rewards (RLVR) to train small language models for code generation, leveraging programmatically checkable signals like unit-test results to directly optimize for functional correctness.
- Key data or claims: RLVR uses programmatically checkable signals like unit-test outcomes to train language models.; RLVR enables direct optimization for functional correctness in code generation.
- Credibility flags: no flags in triage note
- Human question: Whether the verification signals are truly independent from generation and not influenced by ambient state.

## 6. Auditing LLM Benchmarks with Item Response Theory

- Source: https://arxiv.org/abs/2605.30504
- Read priority: 1
- Suggested decision: promote
- Suggested label: challenges
- Topic cluster: judge reliability
- Potential doc impact: may challenge or sharpen an existing principle
- Evidence type: benchmark or eval
- Why read this: The abstract_excerpt directly addresses benchmark contamination, a core concern in verification methodology, and introduces a method to detect mislabels; directly challenging the reliability of benchmark labels, which are foundational to evaluation.
- Abstract gist: LLM benchmark labels are static and may contain errors that propagate silently into downstream benchmarks.
- Key data or claims: LLM benchmark labels are frozen at release and propagate errors silently.; An Item Response Theory-based indicator can detect likely mislabels with 95% precision in top 200 examples.
- Credibility flags: no flags in triage note
- Human question: Verify that the method's use of model responses constitutes external, executable verification as defined by project_focus.

## 7. Fully Open Meditron: An Auditable Pipeline for Clinical LLMs

- Source: https://arxiv.org/abs/2605.16215
- Read priority: 1
- Suggested decision: promote
- Suggested label: extends
- Topic cluster: adjacent or unclear
- Potential doc impact: may add adjacent technique or scope
- Evidence type: system or method
- Why read this: The abstract_excerpt directly addresses the opacity of LLM-based CDSS, which aligns with the project_focus on verification through external signals.
- Abstract gist: Clinical decision support systems (CDSS) need transparent and auditable pipelines to ensure rigorous and reproducible validation.
- Key data or claims: Current LLM-based CDSS are largely opaque despite being labeled 'open'.; Open-weight models often withhold data provenance, curation procedures, and generation pipelines.
- Credibility flags: no flags in triage note
- Human question: Whether the pipeline described is truly executable and independent from ambient state.

## 8. Evaluating using Mock Tool Calls to Quarantine Untrusted Prompt Inputs

- Source: https://arxiv.org/abs/2605.30521
- Read priority: 1
- Suggested decision: promote
- Suggested label: challenges
- Topic cluster: tool and prompt isolation
- Potential doc impact: may challenge or sharpen an existing principle
- Evidence type: system or method
- Why read this: The abstract_excerpt explicitly discusses LLMs processing untrusted inputs under adversarial pressure, which directly aligns with the project_focus on adversarial framing and verification through external signals.
- Abstract gist: Large language models often process untrusted inputs, such as evaluating responses from other models or performing tasks like spam and harm classification under adversarial conditions.
- Key data or claims: LLMs frequently process untrusted inputs in adversarial settings.; Untrusted inputs are often formatted directly into prompt templates.
- Credibility flags: no flags in triage note
- Human question: Whether the paper proposes an external, executable verification mechanism

## 9. Generating and Refining Dynamic Evaluation Rubrics for LLM-as-a-Judge

- Source: https://arxiv.org/abs/2605.30568
- Read priority: 1
- Suggested decision: promote
- Suggested label: extends
- Topic cluster: judge reliability
- Potential doc impact: may add adjacent technique or scope
- Evidence type: benchmark or eval
- Why read this: The abstract_excerpt directly addresses LLM-as-a-Judge, a core component of the project focus, and proposes a method to generate rubrics without human annotation, which aligns with the principle of external signals over self-review.
- Abstract gist: The paper proposes a method to automatically generate detailed evaluation rubrics for LLM-as-a-Judge without requiring any human-annotated data, such as reference answers or expert-crafted rubrics.
- Key data or claims: The method generates fine-grained evaluation rubrics automatically without human annotation.; The method is training-free and produces dataset-specific and instance-specific rubrics.
- Credibility flags: no flags in triage note
- Human question: Whether the generated rubrics support executable verification and explicit pass/fail criteria.

## 10. Reward Bias Substitution: Single-Axis Bias Mitigations Redirect Optimization Pressure

- Source: https://arxiv.org/abs/2605.27996
- Read priority: 1
- Suggested decision: promote
- Suggested label: challenges
- Topic cluster: reward and preference failures
- Potential doc impact: may challenge or sharpen an existing principle
- Evidence type: unclear from abstract
- Why read this: The abstract_excerpt directly addresses 'sycophancy' and 'LLM judge'; key terms in the project_focus; and discusses how bias mitigation efforts can fail by redirecting optimization pressure, which directly challenges the principle of external verification b...
- Abstract gist: Single-axis fixes for reward model biases; such as reducing dependence on length, sycophancy, or style; can redirect optimization pressure toward related proxies instead of eliminating bias, a phenomenon the paper calls reward bias substitution, enabled by...
- Key data or claims: Single-axis bias mitigations can redirect optimization pressure to correlated proxies.; Reward bias substitution occurs due to a measurement-versus-optimization gap between audit and policy-induced distributions.
- Credibility flags: no flags in triage note
- Human question: Whether the paper's proposed solution to reward bias substitution supports external, executable verification.

## 11. Combinatorial Synthesis: Scaling Code RLVR via Atomic Decomposition and Recombination

- Source: https://arxiv.org/abs/2605.31058
- Read priority: 1
- Suggested decision: promote
- Suggested label: extends
- Topic cluster: verifiable rewards
- Potential doc impact: may add adjacent technique or scope
- Evidence type: unclear from abstract
- Why read this: The abstract_excerpt directly references RLVR and LLMs, both central to the project focus.
- Abstract gist: Reinforcement Learning with Verifiable Rewards (RLVR) is central to developing the coding capabilities of Large Language Models (LLMs), but its scalability is limited by the lack of sufficiently challenging verifiable code tasks that test the model's limits.
- Key data or claims: RLVR is foundational for enhancing LLM coding abilities.; Scarcity of challenging verifiable code tasks limits RLVR scalability.
- Credibility flags: no flags in triage note
- Human question: Whether the paper provides executable verification signals for code tasks.

## 12. "I Strongly Suspect This Website Is a Scam": Benchmarking PII Leakage and Detection without Defense in Autonomous Web Agents

- Source: https://arxiv.org/abs/2606.00497
- Read priority: 1
- Suggested decision: promote
- Suggested label: challenges
- Topic cluster: benchmark design
- Potential doc impact: may challenge or sharpen an existing principle
- Evidence type: benchmark or eval
- Why read this: The abstract_excerpt directly addresses PII leakage in autonomous web agents, which aligns with the project focus on verification through external, executable signals.
- Abstract gist: This paper examines how social-engineering attacks, which deceive autonomous web agents into leaking personally identifiable information (PII) to malicious endpoints, are highly effective at extracting sensitive data.
- Key data or claims: Social-engineering attacks are highly effective at extracting critical-tier PII from autonomous web agents.; Autonomous web agents can be manipulated into submitting users' PII to attacker-controlled endpoints.
- Credibility flags: no flags in triage note
- Human question: Whether the paper defines and uses executable verification signals in its evaluation
