# Scout 2026-06-09

Query window: 2026-06-04 to 2026-06-09
Window semantics: OAI-PMH metadata datestamp, not original submission date
Sources: arXiv OAI-PMH
Categories: cs.AI, cs.CL, cs.LG, cs.SE, cs.CR, cs.HC, stat.ML
Keyword groups: core_self_correction, external_judges, independent_verification, step_level_verification, sycophancy, explicit_criteria, executable_verification, cross_family_judges, debate_oversight, state_isolation, cot_faithfulness
Anchor phrases: LLM, large language model, language model, AI agent, LLM agent

## Review Queue

Add judgment outside the mechanical generation step. Suggested labels: challenges, narrows, extends, operational technique, ignore.

- [ ] Aligning Deep Implicit Preferences by Learning to Reason Defensively ([arXiv:2510.11194](https://arxiv.org/abs/2510.11194))
  - Label: ignore
  - Reason: The excerpt focuses on a domain application or capability benchmark rather than verification of agent work.

- [ ] Demystifying Multi-Agent Debate: The Role of Confidence and Diversity ([arXiv:2601.19921](https://arxiv.org/abs/2601.19921))
  - Label: challenges
  - Reason: The excerpt says vanilla multi-agent debate can underperform majority vote and isolates confidence and diversity as reliability conditions for debate oversight.

- [ ] PersistBench: When Should Long-Term Memories Be Forgotten by LLMs? ([arXiv:2602.01146](https://arxiv.org/abs/2602.01146))
  - Label: extends
  - Reason: The excerpt links persistent memory to safety risks and sycophancy-adjacent personalization failures, but it is about memory retention rather than verification design.

- [ ] SciDER: Scientific Data-centric End-to-end Researcher ([arXiv:2603.01421](https://arxiv.org/abs/2603.01421))
  - Label: ignore
  - Reason: The excerpt focuses on self-improvement or reasoning behavior inside the model rather than external verification evidence.

- [ ] FinTradeBench: A Financial Reasoning Benchmark for LLMs ([arXiv:2603.19225](https://arxiv.org/abs/2603.19225))
  - Label: ignore
  - Reason: The excerpt focuses on a domain benchmark or application that happens to use an LLM judge rather than judge reliability for verification.

- [ ] Efficiently Aligning Language Models with Online Natural Language Feedback ([arXiv:2605.04356](https://arxiv.org/abs/2605.04356))
  - Label: ignore
  - Reason: The excerpt focuses on RL training dynamics, reward shaping, or sample efficiency rather than evaluating completed agent work.

- [ ] Aryabhata 2: Scaling Reinforcement Learning for Advanced STEM Reasoning ([arXiv:2605.28829](https://arxiv.org/abs/2605.28829))
  - Label: ignore
  - Reason: The excerpt focuses on RL training dynamics, reward shaping, or sample efficiency rather than evaluating completed agent work.

- [ ] Adaptive Auto-Harness: Sustained Self-Improvement for Agentic System Deployment on Open-Ended Task Streams ([arXiv:2606.01770](https://arxiv.org/abs/2606.01770))
  - Label: operational technique
  - Reason: The excerpt uses execution feedback for open-ended auto-harness self-improvement, relevant to agent deployment but more about optimization than independent checking.

- [ ] LEAP: Supercharging LLMs for Formal Mathematics with Agentic Frameworks ([arXiv:2606.03303](https://arxiv.org/abs/2606.03303))
  - Label: ignore
  - Reason: The excerpt focuses on self-improvement or reasoning behavior inside the model rather than external verification evidence.

- [ ] From Answers to States: Verifiable Process-Level Evaluation of Chemical Reasoning in Large Language Models ([arXiv:2606.03660](https://arxiv.org/abs/2606.03660))
  - Label: extends
  - Reason: The excerpt directly targets process-level evaluation where final-answer chemistry scoring can hide invalid reasoning and LLM judges are hard to scale.

## Deduped Candidates
- Aligning Deep Implicit Preferences by Learning to Reason Defensively ([arXiv:2510.11194](https://arxiv.org/abs/2510.11194))
  - Appeared in: cs.AI
  - Created: 2026-06-03
  - Updated: 2026-06-04
  - OAI datestamp: 2026-06-04
  - Categories: cs.AI
  - Authors: Peiming Li, Zhiyuan Hu, Yang Tang, Shiyu Li, Xi Chen
  - Matched anchors: LLM, large language model, language model
  - Matched keywords: process reward model
  - Abstract excerpt: Personalized alignment is crucial for enabling Large Language Models (LLMs) to engage effectively in user-centric interactions. However, current methods face a dual challenge: they fail to infer users' deep implicit preferences (including unstated goals, semantic context and risk tolerances), and they lack the defensive reasoning required to navigate real-wo...

- Demystifying Multi-Agent Debate: The Role of Confidence and Diversity ([arXiv:2601.19921](https://arxiv.org/abs/2601.19921))
  - Appeared in: cs.AI, cs.CL
  - Created: 2026-06-03
  - Updated: 2026-06-04
  - OAI datestamp: 2026-06-04
  - Categories: cs.CL, cs.AI
  - Authors: Xiaochen Zhu, Caiqi Zhang, Yizhou Chi, Tom Stafford, Nigel Collier, Andreas Vlachos
  - Matched anchors: LLM, large language model, language model
  - Matched keywords: multi-agent debate
  - Abstract excerpt: Multi-agent debate (MAD) is widely used to improve large language model (LLM) performance through test-time scaling, yet recent work shows that vanilla MAD often underperforms simple majority vote despite higher computational cost. Studies show that, under homogeneous agents and uniform belief updates, debate preserves expected correctness and therefore cann...

- PersistBench: When Should Long-Term Memories Be Forgotten by LLMs? ([arXiv:2602.01146](https://arxiv.org/abs/2602.01146))
  - Appeared in: cs.AI
  - Created: 2026-06-02
  - Updated: 2026-06-04
  - OAI datestamp: 2026-06-04
  - Categories: cs.AI
  - Authors: Sidharth Pulipaka, Oliver Chen, Manas Sharma, Taaha S Bajwa, Vyas Raina, Ivaxi Sheth
  - Matched anchors: LLM, large language model, language model
  - Matched keywords: sycophancy
  - Abstract excerpt: Conversational assistants are increasingly integrating long-term memory with large language models (LLMs). This persistence of memories, e.g., the user is vegetarian, can enhance personalization in future conversations. However, the same persistence can also introduce safety risks that have been largely overlooked. Hence, we introduce PersistBench to measure...

- SciDER: Scientific Data-centric End-to-end Researcher ([arXiv:2603.01421](https://arxiv.org/abs/2603.01421))
  - Appeared in: cs.AI, cs.CL
  - Created: 2026-06-03
  - Updated: 2026-06-04
  - OAI datestamp: 2026-06-04
  - Categories: cs.AI, cs.CL
  - Authors: Ke Lin, Owais Aijaz, Yilin Lu, Yiyang Luo, Xuehang Guo, Preslav Nakov
  - Matched anchors: large language model, language model
  - Matched keywords: self-refine
  - Abstract excerpt: While large language models accelerate scientific discovery, existing agents face severe limitations in adaptability, domain generalization, and multimodal scalability, often struggling to autonomously process raw, domain-specific experimental data. To overcome these barriers, we introduce SciDER, a multi-agent system designed to flexibly automate the entire...

- FinTradeBench: A Financial Reasoning Benchmark for LLMs ([arXiv:2603.19225](https://arxiv.org/abs/2603.19225))
  - Appeared in: cs.AI, cs.CL
  - Created: 2026-06-03
  - Updated: 2026-06-04
  - OAI datestamp: 2026-06-04
  - Categories: cs.CE, cs.AI, cs.CL, cs.IR, q-fin.CP
  - Authors: Yogesh Agrawal, Aniruddha Dutta, Md Mahadi Hasan, Santu Karmaker, Aritra Dutta
  - Matched anchors: LLM, large language model, language model
  - Matched keywords: LLM judge
  - Abstract excerpt: Real-world financial decision-making is a challenging problem that requires reasoning over heterogeneous signals, including company fundamentals derived from regulatory filings and trading signals computed from price dynamics. Recently, with advances in Large Language Models (LLMs), financial analysts have begun to use them for financial decision-making task...

- Efficiently Aligning Language Models with Online Natural Language Feedback ([arXiv:2605.04356](https://arxiv.org/abs/2605.04356))
  - Appeared in: cs.AI, cs.LG
  - Created: 2026-06-02
  - Updated: 2026-06-04
  - OAI datestamp: 2026-06-04
  - Categories: cs.LG, cs.AI
  - Authors: Christine Ye, Joe Benton
  - Matched anchors: language model
  - Matched keywords: verifiable reward
  - Abstract excerpt: Reinforcement learning with verifiable rewards has been used to elicit impressive performance from language models in many domains. But, broadly beneficial deployments of AI may require us to train models with strong capabilities in "fuzzy", hard-to-supervise domains. In this paper, we develop methods to align language models in fuzzy domains where human exp...

- Aryabhata 2: Scaling Reinforcement Learning for Advanced STEM Reasoning ([arXiv:2605.28829](https://arxiv.org/abs/2605.28829))
  - Appeared in: cs.AI, cs.CL
  - Created: 2026-06-03
  - Updated: 2026-06-04
  - OAI datestamp: 2026-06-04
  - Categories: cs.CL, cs.AI, cs.CY
  - Authors: Ritvik Rastogi, Vishal Singh, Tejas Chaudhari, Sandeep Varma
  - Matched anchors: large language model, language model
  - Matched keywords: verifiable reward
  - Abstract excerpt: Competitive STEM examinations such as JEE and NEET require multi-step symbolic reasoning, precise numerical computation, and deep conceptual understanding across physics, chemistry, and mathematics. Recent large language models perform strongly on common reasoning benchmarks, yet they remain difficult to deploy at scale, where millions of student doubts dema...

- Adaptive Auto-Harness: Sustained Self-Improvement for Agentic System Deployment on Open-Ended Task Streams ([arXiv:2606.01770](https://arxiv.org/abs/2606.01770))
  - Appeared in: cs.AI, cs.LG
  - Created: 2026-06-03
  - Updated: 2026-06-04
  - OAI datestamp: 2026-06-04
  - Categories: cs.LG, cs.AI
  - Authors: Zewen Liu, Zhan Shi, Yisi Sang, Bing He, Minhua Lin, Tianxin Wei, +4 more
  - Matched anchors: LLM, LLM agent
  - Matched keywords: execution feedback
  - Abstract excerpt: Auto-harness systems such as A-Evolve, GEPA, and Meta-Harness improve LLM agents by optimizing prompts, skills, tools, memories, and supporting infrastructure from execution feedback, but they are typically evaluated on fixed offline benchmarks. Real deployments instead present open-ended task streams: histories grow without a fixed endpoint, heterogeneous t...

- LEAP: Supercharging LLMs for Formal Mathematics with Agentic Frameworks ([arXiv:2606.03303](https://arxiv.org/abs/2606.03303))
  - Appeared in: cs.AI
  - Created: 2026-06-03
  - Updated: 2026-06-04
  - OAI datestamp: 2026-06-04
  - Categories: cs.AI
  - Authors: Po-Nien Kung, Linfeng Song, Dawsen Hwang, Jinsung Yoon, Chun-Liang Li, Simone Severini, +7 more
  - Matched anchors: LLM, large language model, language model
  - Matched keywords: self-refine
  - Abstract excerpt: Large Language Models (LLMs) exhibit strong informal mathematical reasoning but struggle to generate mechanically verifiable proofs in formal languages like Lean. We present LEAP, an agentic framework that enables general-purpose foundation models to achieve state-of-the-art performance on automated formal theorem proving. LEAP leverages foundation model cap...

- From Answers to States: Verifiable Process-Level Evaluation of Chemical Reasoning in Large Language Models ([arXiv:2606.03660](https://arxiv.org/abs/2606.03660))
  - Appeared in: cs.AI
  - Created: 2026-06-03
  - Updated: 2026-06-04
  - OAI datestamp: 2026-06-04
  - Categories: cs.AI
  - Authors: Hongyu Guo, Hao Li, He Cao, Gongbo Zhang, Li Yuan
  - Matched anchors: LLM, large language model, language model
  - Matched keywords: LLM judge
  - Abstract excerpt: Large language models are increasingly used as chemistry assistants, yet most chemistry benchmarks still score only final answers. This masks a critical failure mode: a model may output the correct molecule, product, or option while its reasoning violates chemical logic. Existing process-level evaluators are hard to scale because LLM judges and human step-le...

## Category Results

### Category: `cs.AI` (set `cs:cs:AI`)
- Aligning Deep Implicit Preferences by Learning to Reason Defensively
  - arXiv: [2510.11194](https://arxiv.org/abs/2510.11194)
  - Created: 2026-06-03
  - Updated: 2026-06-04
  - OAI datestamp: 2026-06-04
  - Categories: cs.AI
  - Authors: Peiming Li, Zhiyuan Hu, Yang Tang, Shiyu Li, Xi Chen
  - Matched anchors: LLM, large language model, language model
  - Matched keywords: process reward model
  - Abstract excerpt: Personalized alignment is crucial for enabling Large Language Models (LLMs) to engage effectively in user-centric interactions. However, current methods face a dual challenge: they fail to infer users' deep implicit preferences (including unstated goals, semantic context and risk tolerances), and they lack the defensive reasoning required to navigate real-wo...
- Demystifying Multi-Agent Debate: The Role of Confidence and Diversity
  - arXiv: [2601.19921](https://arxiv.org/abs/2601.19921)
  - Created: 2026-06-03
  - Updated: 2026-06-04
  - OAI datestamp: 2026-06-04
  - Categories: cs.CL, cs.AI
  - Authors: Xiaochen Zhu, Caiqi Zhang, Yizhou Chi, Tom Stafford, Nigel Collier, Andreas Vlachos
  - Matched anchors: LLM, large language model, language model
  - Matched keywords: multi-agent debate
  - Abstract excerpt: Multi-agent debate (MAD) is widely used to improve large language model (LLM) performance through test-time scaling, yet recent work shows that vanilla MAD often underperforms simple majority vote despite higher computational cost. Studies show that, under homogeneous agents and uniform belief updates, debate preserves expected correctness and therefore cann...
- PersistBench: When Should Long-Term Memories Be Forgotten by LLMs?
  - arXiv: [2602.01146](https://arxiv.org/abs/2602.01146)
  - Created: 2026-06-02
  - Updated: 2026-06-04
  - OAI datestamp: 2026-06-04
  - Categories: cs.AI
  - Authors: Sidharth Pulipaka, Oliver Chen, Manas Sharma, Taaha S Bajwa, Vyas Raina, Ivaxi Sheth
  - Matched anchors: LLM, large language model, language model
  - Matched keywords: sycophancy
  - Abstract excerpt: Conversational assistants are increasingly integrating long-term memory with large language models (LLMs). This persistence of memories, e.g., the user is vegetarian, can enhance personalization in future conversations. However, the same persistence can also introduce safety risks that have been largely overlooked. Hence, we introduce PersistBench to measure...
- SciDER: Scientific Data-centric End-to-end Researcher
  - arXiv: [2603.01421](https://arxiv.org/abs/2603.01421)
  - Created: 2026-06-03
  - Updated: 2026-06-04
  - OAI datestamp: 2026-06-04
  - Categories: cs.AI, cs.CL
  - Authors: Ke Lin, Owais Aijaz, Yilin Lu, Yiyang Luo, Xuehang Guo, Preslav Nakov
  - Matched anchors: large language model, language model
  - Matched keywords: self-refine
  - Abstract excerpt: While large language models accelerate scientific discovery, existing agents face severe limitations in adaptability, domain generalization, and multimodal scalability, often struggling to autonomously process raw, domain-specific experimental data. To overcome these barriers, we introduce SciDER, a multi-agent system designed to flexibly automate the entire...
- FinTradeBench: A Financial Reasoning Benchmark for LLMs
  - arXiv: [2603.19225](https://arxiv.org/abs/2603.19225)
  - Created: 2026-06-03
  - Updated: 2026-06-04
  - OAI datestamp: 2026-06-04
  - Categories: cs.CE, cs.AI, cs.CL, cs.IR, q-fin.CP
  - Authors: Yogesh Agrawal, Aniruddha Dutta, Md Mahadi Hasan, Santu Karmaker, Aritra Dutta
  - Matched anchors: LLM, large language model, language model
  - Matched keywords: LLM judge
  - Abstract excerpt: Real-world financial decision-making is a challenging problem that requires reasoning over heterogeneous signals, including company fundamentals derived from regulatory filings and trading signals computed from price dynamics. Recently, with advances in Large Language Models (LLMs), financial analysts have begun to use them for financial decision-making task...
- Efficiently Aligning Language Models with Online Natural Language Feedback
  - arXiv: [2605.04356](https://arxiv.org/abs/2605.04356)
  - Created: 2026-06-02
  - Updated: 2026-06-04
  - OAI datestamp: 2026-06-04
  - Categories: cs.LG, cs.AI
  - Authors: Christine Ye, Joe Benton
  - Matched anchors: language model
  - Matched keywords: verifiable reward
  - Abstract excerpt: Reinforcement learning with verifiable rewards has been used to elicit impressive performance from language models in many domains. But, broadly beneficial deployments of AI may require us to train models with strong capabilities in "fuzzy", hard-to-supervise domains. In this paper, we develop methods to align language models in fuzzy domains where human exp...
- Aryabhata 2: Scaling Reinforcement Learning for Advanced STEM Reasoning
  - arXiv: [2605.28829](https://arxiv.org/abs/2605.28829)
  - Created: 2026-06-03
  - Updated: 2026-06-04
  - OAI datestamp: 2026-06-04
  - Categories: cs.CL, cs.AI, cs.CY
  - Authors: Ritvik Rastogi, Vishal Singh, Tejas Chaudhari, Sandeep Varma
  - Matched anchors: large language model, language model
  - Matched keywords: verifiable reward
  - Abstract excerpt: Competitive STEM examinations such as JEE and NEET require multi-step symbolic reasoning, precise numerical computation, and deep conceptual understanding across physics, chemistry, and mathematics. Recent large language models perform strongly on common reasoning benchmarks, yet they remain difficult to deploy at scale, where millions of student doubts dema...
- Adaptive Auto-Harness: Sustained Self-Improvement for Agentic System Deployment on Open-Ended Task Streams
  - arXiv: [2606.01770](https://arxiv.org/abs/2606.01770)
  - Created: 2026-06-03
  - Updated: 2026-06-04
  - OAI datestamp: 2026-06-04
  - Categories: cs.LG, cs.AI
  - Authors: Zewen Liu, Zhan Shi, Yisi Sang, Bing He, Minhua Lin, Tianxin Wei, +4 more
  - Matched anchors: LLM, LLM agent
  - Matched keywords: execution feedback
  - Abstract excerpt: Auto-harness systems such as A-Evolve, GEPA, and Meta-Harness improve LLM agents by optimizing prompts, skills, tools, memories, and supporting infrastructure from execution feedback, but they are typically evaluated on fixed offline benchmarks. Real deployments instead present open-ended task streams: histories grow without a fixed endpoint, heterogeneous t...
- LEAP: Supercharging LLMs for Formal Mathematics with Agentic Frameworks
  - arXiv: [2606.03303](https://arxiv.org/abs/2606.03303)
  - Created: 2026-06-03
  - Updated: 2026-06-04
  - OAI datestamp: 2026-06-04
  - Categories: cs.AI
  - Authors: Po-Nien Kung, Linfeng Song, Dawsen Hwang, Jinsung Yoon, Chun-Liang Li, Simone Severini, +7 more
  - Matched anchors: LLM, large language model, language model
  - Matched keywords: self-refine
  - Abstract excerpt: Large Language Models (LLMs) exhibit strong informal mathematical reasoning but struggle to generate mechanically verifiable proofs in formal languages like Lean. We present LEAP, an agentic framework that enables general-purpose foundation models to achieve state-of-the-art performance on automated formal theorem proving. LEAP leverages foundation model cap...
- From Answers to States: Verifiable Process-Level Evaluation of Chemical Reasoning in Large Language Models
  - arXiv: [2606.03660](https://arxiv.org/abs/2606.03660)
  - Created: 2026-06-03
  - Updated: 2026-06-04
  - OAI datestamp: 2026-06-04
  - Categories: cs.AI
  - Authors: Hongyu Guo, Hao Li, He Cao, Gongbo Zhang, Li Yuan
  - Matched anchors: LLM, large language model, language model
  - Matched keywords: LLM judge
  - Abstract excerpt: Large language models are increasingly used as chemistry assistants, yet most chemistry benchmarks still score only final answers. This masks a critical failure mode: a model may output the correct molecule, product, or option while its reasoning violates chemical logic. Existing process-level evaluators are hard to scale because LLM judges and human step-le...
### Category: `cs.CL` (set `cs:cs:CL`)
- Demystifying Multi-Agent Debate: The Role of Confidence and Diversity
  - arXiv: [2601.19921](https://arxiv.org/abs/2601.19921)
  - Created: 2026-06-03
  - Updated: 2026-06-04
  - OAI datestamp: 2026-06-04
  - Categories: cs.CL, cs.AI
  - Authors: Xiaochen Zhu, Caiqi Zhang, Yizhou Chi, Tom Stafford, Nigel Collier, Andreas Vlachos
  - Matched anchors: LLM, large language model, language model
  - Matched keywords: multi-agent debate
  - Abstract excerpt: Multi-agent debate (MAD) is widely used to improve large language model (LLM) performance through test-time scaling, yet recent work shows that vanilla MAD often underperforms simple majority vote despite higher computational cost. Studies show that, under homogeneous agents and uniform belief updates, debate preserves expected correctness and therefore cann...
- SciDER: Scientific Data-centric End-to-end Researcher
  - arXiv: [2603.01421](https://arxiv.org/abs/2603.01421)
  - Created: 2026-06-03
  - Updated: 2026-06-04
  - OAI datestamp: 2026-06-04
  - Categories: cs.AI, cs.CL
  - Authors: Ke Lin, Owais Aijaz, Yilin Lu, Yiyang Luo, Xuehang Guo, Preslav Nakov
  - Matched anchors: large language model, language model
  - Matched keywords: self-refine
  - Abstract excerpt: While large language models accelerate scientific discovery, existing agents face severe limitations in adaptability, domain generalization, and multimodal scalability, often struggling to autonomously process raw, domain-specific experimental data. To overcome these barriers, we introduce SciDER, a multi-agent system designed to flexibly automate the entire...
- FinTradeBench: A Financial Reasoning Benchmark for LLMs
  - arXiv: [2603.19225](https://arxiv.org/abs/2603.19225)
  - Created: 2026-06-03
  - Updated: 2026-06-04
  - OAI datestamp: 2026-06-04
  - Categories: cs.CE, cs.AI, cs.CL, cs.IR, q-fin.CP
  - Authors: Yogesh Agrawal, Aniruddha Dutta, Md Mahadi Hasan, Santu Karmaker, Aritra Dutta
  - Matched anchors: LLM, large language model, language model
  - Matched keywords: LLM judge
  - Abstract excerpt: Real-world financial decision-making is a challenging problem that requires reasoning over heterogeneous signals, including company fundamentals derived from regulatory filings and trading signals computed from price dynamics. Recently, with advances in Large Language Models (LLMs), financial analysts have begun to use them for financial decision-making task...
- Aryabhata 2: Scaling Reinforcement Learning for Advanced STEM Reasoning
  - arXiv: [2605.28829](https://arxiv.org/abs/2605.28829)
  - Created: 2026-06-03
  - Updated: 2026-06-04
  - OAI datestamp: 2026-06-04
  - Categories: cs.CL, cs.AI, cs.CY
  - Authors: Ritvik Rastogi, Vishal Singh, Tejas Chaudhari, Sandeep Varma
  - Matched anchors: large language model, language model
  - Matched keywords: verifiable reward
  - Abstract excerpt: Competitive STEM examinations such as JEE and NEET require multi-step symbolic reasoning, precise numerical computation, and deep conceptual understanding across physics, chemistry, and mathematics. Recent large language models perform strongly on common reasoning benchmarks, yet they remain difficult to deploy at scale, where millions of student doubts dema...
### Category: `cs.LG` (set `cs:cs:LG`)
- Efficiently Aligning Language Models with Online Natural Language Feedback
  - arXiv: [2605.04356](https://arxiv.org/abs/2605.04356)
  - Created: 2026-06-02
  - Updated: 2026-06-04
  - OAI datestamp: 2026-06-04
  - Categories: cs.LG, cs.AI
  - Authors: Christine Ye, Joe Benton
  - Matched anchors: language model
  - Matched keywords: verifiable reward
  - Abstract excerpt: Reinforcement learning with verifiable rewards has been used to elicit impressive performance from language models in many domains. But, broadly beneficial deployments of AI may require us to train models with strong capabilities in "fuzzy", hard-to-supervise domains. In this paper, we develop methods to align language models in fuzzy domains where human exp...
- Adaptive Auto-Harness: Sustained Self-Improvement for Agentic System Deployment on Open-Ended Task Streams
  - arXiv: [2606.01770](https://arxiv.org/abs/2606.01770)
  - Created: 2026-06-03
  - Updated: 2026-06-04
  - OAI datestamp: 2026-06-04
  - Categories: cs.LG, cs.AI
  - Authors: Zewen Liu, Zhan Shi, Yisi Sang, Bing He, Minhua Lin, Tianxin Wei, +4 more
  - Matched anchors: LLM, LLM agent
  - Matched keywords: execution feedback
  - Abstract excerpt: Auto-harness systems such as A-Evolve, GEPA, and Meta-Harness improve LLM agents by optimizing prompts, skills, tools, memories, and supporting infrastructure from execution feedback, but they are typically evaluated on fixed offline benchmarks. Real deployments instead present open-ended task streams: histories grow without a fixed endpoint, heterogeneous t...
