# Cross-Family

*(Orchestration Pattern)*

## Name

**Cross-Family**

Also known as: Cross-Provider Verification, Independent-Family Judge, Family-Diverse Evaluation.

## Intent

Run high-leverage generation and assessment on deliberately different model families and record both identities. Reduce exposure to shared training-data biases and shared latent priors, and make any residual correlated error attributable to the named models.

Cross-Family has two complementary roles. At verification time, the judge comes from a different family than the generator. At optimization time, the teacher or proposer comes from a different family than the model being shaped. Both roles serve the same mechanic: break same-family blind spots where one model's confidence becomes another model's evidence.

## Problem

An LLM produces an answer. A second LLM is asked whether the answer looks right. Both are sampled from the same provider, often the same family, sometimes the same model.

That can look independent in code:

* one object is called `apprentice` and another object is called `grader`;
* one prompt says "write" and another prompt says "review";
* one agent is a manager and another agent is a researcher;
* the framework exposes a configurable judge slot.

But the verification boundary may still collapse. The same blind spot that produced the error can also fail to detect it. Separate roles do not create independent evidence when the generator and verifier share the same model family.

Common shapes:

* one configured client is reused for both apprentice and grader;
* separate clients are created, but both are `gpt-*`, both are `claude-*`, or both are the same Llama family;
* role-diverse agents are wired together, but the judge defaults to whichever provider the framework imported first;
* the verifier argument is left at `model=None`, and the framework silently chooses the default family.

`verification_design.md` Principle 7 names the design rule: cross-family verification beats self-verification. The Judge Harness update narrows the claim: family diversity is necessary, not sufficient. A different-family judge still needs perturbation, repetition, and calibration around it.

## Forces

* **Verification-time independence vs. operational simplicity.** One client per app is easy to configure; family-diverse verification adds providers, secrets, and routing.
* **Provider availability vs. provider lock-in.** Verifier diversity assumes more than one provider is reachable.
* **Cost vs. independence.** Cross-family verification pays for two providers; same-family verification pays for one.
* **Role diversity vs. verifier diversity.** Different agent roles inside one family do not equal cross-family verification. The seam that matters is generator to verifier.
* **Optimization-time vs. verification-time.** A teacher/student split can break same-family bias during prompt optimization; a different-family judge can break it during evaluation.
* **Recorded identity vs. implicit identity.** A run that does not log generator and verifier identities cannot be audited for same-family bias.

## Solution

At every leverage point where one model's output becomes another model's input as evidence, require that the two models come from different families, and stamp both identities into the artifact the verifier produces.

"Different family" is a configured choice, not an accident of which client was imported first.

The pattern lives at three layers:

* **Configuration:** generator and verifier clients are constructed as separate objects, with explicit family or provider attributes.
* **Routing:** the verification call site reads the verifier from configuration, not from a module-level default.
* **Reporting:** the verdict object carries `generator_model`, `generator_family`, `verifier_model`, and `verifier_family`.

A verdict that does not name both identities is not auditable.

## Mechanism

1. **Name the leverage points.** Identify calls where model output becomes load-bearing evidence: judge calls, optimization advice, debate adjudication, escalation arbitration.
2. **Construct distinct clients.** Generator and verifier clients are separate objects. Each carries provider and family metadata.
3. **Assert at routing time.** Before invoking the verifier, assert that `verifier.family != generator.family`.
4. **Carry both identities into the verdict.** The report contains generator identity and verifier identity.
5. **Wrap the verifier in a Judge Harness.** Cross-family is necessary, not sufficient. Consistency, perturbation, and calibration checks belong around the judge.

## Pattern / Antipattern

The same task: ask a model to answer, then ask a model to grade the answer. The antipattern uses one family and treats the verdict as independent. The pattern requires family diversity at that boundary and records both identities.

### Antipattern: same-client grader

The naive implementation stores one chat client on the grader and uses it for both answer extraction and correctness judgment.

```python
from dataclasses import dataclass


@dataclass(frozen=True)
class ChatClient:
    model: str
    family: str

    def complete(self, prompt: str) -> str:
        ...


class Grader:
    def __init__(self, client: ChatClient):
        self.client = client

    def extract_answer(self, transcript: str) -> str:
        return self.client.complete(
            "Extract the apprentice's final answer:\n" + transcript
        )

    def judge_correctness(self, question: str, answer: str) -> str:
        return self.client.complete(
            "Is this answer correct?\n"
            f"Question: {question}\n"
            f"Answer: {answer}\n"
            "Return PASS or FAIL."
        )


client = ChatClient(model="gpt-4o", family="gpt")
grader = Grader(client)

answer = grader.extract_answer(apprentice_transcript)
verdict = grader.judge_correctness(question, answer)
```

The object names imply a verifier, but there is no family boundary. The same client supplies the extraction and the judgment, and no assertion checks whether the verifier is independent from the generator.

AutoGen's task-centric memory grader has this shape: a grader utility stores one `ChatCompletionClient` and uses it to extract the answer and judge correctness. Same-client grading is not wrong in every context. As a lightweight sample it is fine. It becomes a Cross-Family antipattern when the same-client verdict is treated as independent verification.

The same failure family appears in other shapes. The zen pipeline uses same-family tiers for judge review, judge fix, and escalation. ChatArena shows that role-diverse agents can still leave the judge in the same family. DeepEval exposes an evaluation-model boundary, but a leaky default can leave callers with a same-family judge unless they choose otherwise.

### Pattern: uncovered verification-time instance

No strict verification-time Cross-Family Pattern instance was found in the OSS bench surveyed for this catalog. The closest OSS evidence is DSPy's teacher/student split, which applies the same mechanic at optimization time rather than verification time. We mark this Pattern as uncovered rather than promoting an analogy-grade instance to canonical.

DSPy still matters as supporting evidence. Its optimization code separates the model being shaped from the model proposing instructions, generating examples, or acting as teacher. That is the same independence move at a different leverage point: the optimization advice does not have to come from the model being optimized.

When a strict verification-time instance is mined or self-mined, this card should be re-authored with the load-bearing assertion `verifier.family != generator.family` in the canonical block.

## Determinism Move

Cross-Family constrains `same_family_bias` by requiring the verifier's family to be a configured value distinct from the generator's, recorded in the verdict so the boundary is auditable.

It constrains `self_review_bias` by treating "different agent, same family" as a softer form of self-review rather than independent verification. The verifier may have a separate prompt and role, but it can still share the generator's blind spots.

The determinism move is recorded family diversity at the verification boundary; if generator and verifier identities are not both in the verdict, the run is unauditable.

## Observable Signal

Every Cross-Family report should include:

* generator model and family;
* verifier model and family;
* family equality boolean (`generator_family == verifier_family`);
* verdict;
* verifier configuration source (`explicit_config`, `framework_default`, `module_singleton`);
* Judge Harness fields if wrapped, such as consistency, perturbation, and calibration, or `harness: none` if not.

A useful report names the model boundary:

```text
generator_model: claude-sonnet-4-5
generator_family: claude
verifier_model: gpt-4o
verifier_family: gpt
family_diverse: true
verdict: pass
verifier_config_source: explicit_config
harness: none
```

**Design judgment.** On the same labelled cases, report each checker's solo miss rate and the pair's joint-miss rate with a common denominator of cases the checks should catch. Compare the observed joint-miss rate with the product of the solo rates, which is the prediction under independence. When agreement is required to issue a verdict, report the share of eligible cases left without one.

## Failure Modes

Family inequality is a configuration fact; its effect on correlated error must be measured on the target workload, not assumed from the configuration.

* **Same-Client Grading:** one client object is used for both generator and verifier. No assertion enforces family diversity. Construct distinct clients and assert at routing time.
* **Leaky Default:** the framework exposes a configurable verifier slot, but the default resolves to the same family the application is built on. Refuse to construct the verifier when the family is unset.
* **Role Diversity Mistaken for Verifier Diversity:** players, writers, managers, and researchers are diverse across families, but the judge defaults to one family. Identify the verification boundary separately from role assignment.
* **Unrecorded Identities:** generation and verification use different families in practice, but the verdict does not name them. Stamp `generator_*` and `verifier_*` fields into every verdict.

* **Unmeasured Shared Misses (design judgment):** counting a second judge from another family as an independent layer without measuring how often both judges miss the same cases leaves the stack's joint coverage unknown.

## Use When

Use this pattern when:

* an LLM-based judge or evaluator is on the verification path;
* the same provider serves both generation and verification by default;
* the verification result gates promotion, training, deployment, or downstream automation;
* optimization-time advice steers a model being shaped;
* audit context requires verifier identity to be recorded.

## Do Not Use When

Do not reach for Cross-Family when:

* verification is fully executable, so an **Executable Analog** or **Comparator** can decide it without an LLM judge;
* only one provider is reachable and provider diversity cannot be added;
* the verification is low leverage and misattribution cost is negligible;
* the boundary cannot carry verifier identity metadata.

If only one family is reachable, label the result as informal and maximize executable checks.

When judges from both families see the candidate and score its plausibility, use family diversity alongside an external correctness check where available (design judgment). One study reports that different-family reference-free judges still accepted the same wrong answers in low-accuracy GSM8K tests. [arXiv:2607.05904](https://arxiv.org/abs/2607.05904)

## Evidence

* **Verification Design Principle 7:** the design doc names Cross-Family Beats Self-Verification and frames same-family review as weaker than independent verification.
* **Judge Reliability Harness update:** [the synthesis claim on LLM-judge reliability](https://github.com/verificationdesign/verificationdesign/blob/main/research/synthesis.md#llm-judge-reliability-can-vary-across-benchmarks-and-perturbations-even-when-the-judge-comes-from-a-different-model-family) records the caveat that judge reliability still needs perturbation, consistency, and calibration checks.
* **[AutoGen](https://github.com/microsoft/autogen) task-centric memory grader:** the antipattern cleanup sweep records a same-client grader that extracts and judges answers with one `ChatCompletionClient`.
* **zen same-family tiers:** the mining note records a provider-wide same-family pipeline where review, fix, and escalation stay inside the chosen family.
* **[ChatArena](https://github.com/Farama-Foundation/chatarena) and [DeepEval](https://github.com/confident-ai/deepeval):** the cross-family sweep records role-diverse or configurable evaluation surfaces that do not, by themselves, enforce family diversity.
* **[DSPy](https://github.com/stanfordnlp/dspy) teacher/student optimization:** the cross-family sweep records a partial Pattern instance at optimization time, where the teacher or proposer model is separate from the student model being shaped.

* One study reports 581 unanimously accepted wrong answers against 497 predicted under independence in its low-accuracy GSM8K tests with candidate-conditioned judges across model families. [arXiv:2607.05904](https://arxiv.org/abs/2607.05904)
* One study reports that rule-plus-judge pairs behaved closer to independence than judge pairs on authored agent-action block cases when escalation counted as a miss. The deterministic layer was a regular-expression rule engine. [arXiv:2610.07359](https://arxiv.org/abs/2610.07359)
* One study reports that per-criterion generative rubric judges repeated the selected high-confidence errors of a decision model (Jev) on human-labelled benchmarks in 96.0% of verdicts, against 50.3% under its criterion-and-label-conditioned independence baseline. [arXiv:2609.29769](https://arxiv.org/abs/2609.29769)
* One study reports that cross-provider economy judges jointly disagreed with single Arena preference votes more often than predicted under independence on battles where all judges picked a winner. Requiring agreement also lowered the share of system pairs with a called direction for pairings involving Luna. The reference is a preference vote for each battle. [arXiv:2611.04090](https://arxiv.org/abs/2611.04090)

### References

| Source | Study |
| --- | --- |
| [arXiv:2607.05904](https://arxiv.org/abs/2607.05904) | Self-Play Reward Hacking of Reference-Free LLM Judges |
| [arXiv:2610.07359](https://arxiv.org/abs/2610.07359) | Evaluate the Stack, Not the Layer: Do Deterministic and LLM Gates for Agent Actions Fail Independently? |
| [arXiv:2609.29769](https://arxiv.org/abs/2609.29769) | Decision Models vs. LLMs as Rubric Judges: Cheaper, Faster, and Wrong in the Same Places |
| [arXiv:2611.04090](https://arxiv.org/abs/2611.04090) | Swapping the Judge Changes the Ranking: A Preregistered Study of Cross-Provider Replication in LLM-Judged System Comparisons |

## Related Patterns

* **Judge Harness:** cross-family is necessary, not sufficient; the verifier still needs perturbation, repetition, calibration, and reporting around it.
* **Constitution:** a shared rubric makes cross-family verdicts comparable across runs.
* **Admissibility Gate:** same-family verification with a confirmatory prompt doubles the antipattern; adversarial framing on a cross-family judge is the additive form.
* **Blind Oracle:** Cross-Family addresses which model verifies; Blind Oracle addresses what the verifier is allowed to see.
* **Adversary:** an adversary role drawn from the same family as the proposer reproduces the Cross-Family antipattern at the role boundary.
