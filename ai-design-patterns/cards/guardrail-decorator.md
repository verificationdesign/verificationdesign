# Guardrail Decorator

*(Context Pattern)*

## Name

**Guardrail Decorator**

Also known as: Policy Decorator, Policy Hook, Callback Guardrail, Boundary Decorator.

## Intent

Wrap a model call, tool call, or other model-output boundary in a policy decorator that can deny, replace, sanitize, or convert errors, so policy lives in code at the boundary the model crosses instead of in prompt prose the model is asked to obey.

The decorator is the layer around the call. It is not the prompt instruction telling the model how to behave. A prompt that says "never call delete_file without confirmation" can still be useful. It does not create the guardrail.

## Problem

Policy is often written as a sentence the model is expected to remember.

That can look disciplined in code:

* the system prompt says "do not call `delete_file` unless the user confirms";
* the assistant persona says "never reveal API keys";
* the model decides whether the action satisfies the same policy it is about to cross;
* when a policy gap appears, the fix is another paragraph in the prompt.

The verifier failure is that enforcement and judgment share the same sampled output. Prompt-only policy asks the model to take the action and decide whether the action is policy compliant. `verification_design.md` Principle 1 rejects that shape: external signals beat self-review. Principle 6 gives the repair direction: put the check in executable structure.

Policy that matters belongs at a boundary the model cannot rationalize past.

## Forces

* **Prompt-encoded policy vs. callback-encoded policy.** A prompt rule drifts through summarization, paraphrase, persona tests, and context compaction. A registered callback survives because it is code at the boundary.
* **Pre-call enforcement vs. post-call enforcement.** Blocking before the call avoids side effects entirely. Sanitizing after the call recovers when blocking would be too blunt. A decorator gives the boundary both seats.
* **Decorator vs. type adapter.** A Tool Adapter normalizes call shape. A Guardrail Decorator enforces call policy. The wrapper surface can look similar, so name the job.
* **Reversibility vs. side effects.** Some calls, such as delete, send, charge, and deploy, cannot be undone after execution. The before-call hook is the only safe veto seat.
* **Centralized policy vs. scattered prompts.** One decorator registered at agent setup beats ten policy paragraphs spread across prompt templates.
* **Latency vs. auditability.** A callback adds a small hop, but it produces a decision artifact. Prompt rules leave no policy decision to inspect.

## Solution

Put the policy at the boundary the model crosses, not in the prompt the model receives.

A Guardrail Decorator wraps the call site with three hooks:

* **Before-call hook:** can deny the call, replace it with a substitute response, or pass through.
* **After-call hook:** can sanitize, replace, annotate, or pass through.
* **Error hook:** can convert errors to recoverable responses, or re-raise.
* **Decision contract:** each hook returns either `None` for pass-through or a structured override. The first non-`None` return short-circuits later hooks in the chain.

The prompt may still tell the model to be careful. The decorator is what blocks `delete_file` when policy denies the call.

## Mechanism

1. **Identify call boundaries.** Name the model, tool, retriever, or output boundary that needs policy.
2. **Define policy functions.** Give each hook explicit return semantics: `None` to pass, structured override to short-circuit.
3. **Register policies at setup.** Wire the callbacks into the agent or framework, not into the prompt.
4. **Order the policies.** Document precedence, usually first-non-`None`-wins.
5. **Log every decision.** Record the policy, hook, original args, original response if the call ran, and override.

## Pattern / Antipattern

The same task: put policy around a call boundary the model can cross. The antipattern side is intentionally uncovered for this catalog pass. The pattern side shows the minimal wrapper shape and the decision object a verifier can inspect.

### Antipattern: uncovered no-op instance

No credible Guardrail Decorator antipattern was promoted from the OSS bench surveyed for this catalog.

The natural candidate is a no-op callback registration: a decorator-shaped interface that always returns `None`, so the type signature says "guardrail" while the boundary never fires. Sweep D inspected ADK plugin examples and AutoGPT's `validate_url` decorator without finding that instance. We mark the Antipattern as uncovered rather than inventing one.

Prompt-only policy is a real production failure, but it belongs more naturally under **Constitution**: criteria belong in code, not prose. Guardrail Decorator is narrower. It asks whether a call boundary has an executable policy hook that can stop, replace, sanitize, or recover.

When a strict no-op callback instance is mined, re-author this section around a concrete assertion: `before_call(args) is None and not policy.called`.

### Pattern: policy hook around the call

The structured implementation wraps the call site and returns the decision boundary with the result.

```python
from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
from typing import Literal


Decision = Literal["pass", "deny", "replace", "sanitize", "recover"]
Hook = Literal["before", "after", "on_error", "none"]


@dataclass(frozen=True)
class Override:
    decision: Decision
    response: dict


@dataclass(frozen=True)
class CallResult:
    decision: Decision
    fired_policy: str
    hook: Hook
    original_args: dict
    original_response: dict | None
    override: Override | None

    @property
    def response(self) -> dict | None:
        if self.override is not None:
            return self.override.response
        return self.original_response


@dataclass
class RecordingPolicy:
    name: str
    calls: list[dict] = field(default_factory=list)

    def before(self, args: dict) -> Override | None:
        self.calls.append(dict(args))
        if args.get("path") == "/etc/passwd":
            return Override(
                decision="deny",
                response={
                    "error": "destructive operation requires explicit confirmation"
                },
            )
        return None

    def after(self, args: dict, response: dict) -> Override | None:
        return None

    def on_error(self, args: dict, error: Exception) -> Override | None:
        return None


class Guardrail:
    def __init__(self, policies: Iterable[RecordingPolicy]):
        self.policies = tuple(policies)

    def wrap(self, call: Callable[..., dict]) -> Callable[[dict], CallResult]:
        def guarded(args: dict) -> CallResult:
            for policy in self.policies:
                override = policy.before(args)
                if override is not None:
                    return CallResult(
                        decision=override.decision,
                        fired_policy=policy.name,
                        hook="before",
                        original_args=dict(args),
                        original_response=None,
                        override=override,
                    )

            try:
                original_response = call(**args)
            except Exception as error:
                for policy in self.policies:
                    override = policy.on_error(args, error)
                    if override is not None:
                        return CallResult(
                            decision=override.decision,
                            fired_policy=policy.name,
                            hook="on_error",
                            original_args=dict(args),
                            original_response=None,
                            override=override,
                        )
                raise

            for policy in self.policies:
                override = policy.after(args, original_response)
                if override is not None:
                    return CallResult(
                        decision=override.decision,
                        fired_policy=policy.name,
                        hook="after",
                        original_args=dict(args),
                        original_response=original_response,
                        override=override,
                    )

            return CallResult(
                decision="pass",
                fired_policy="none",
                hook="none",
                original_args=dict(args),
                original_response=original_response,
                override=None,
            )

        return guarded


calls_recorded: list[dict] = []

def real_delete(path: str) -> dict:
    calls_recorded.append({"path": path})
    return {"deleted": path}

confirm_destructive = RecordingPolicy(name="confirm_destructive")
guard = Guardrail(policies=[confirm_destructive])
result = guard.wrap(real_delete)({"path": "/etc/passwd"})

assert result.decision == "deny"
assert result.fired_policy == "confirm_destructive"
assert result.hook == "before"
assert result.override is not None
assert calls_recorded == []
assert confirm_destructive.calls == [{"path": "/etc/passwd"}]
```

The six assertions carry the pattern. A guardrail must name a decision, attribute it to a policy, attribute it to a hook, carry a structured override, prevent the original call from running on a deny, and prove the named policy actually saw the original args. Without the last two assertions, a pass-through wrapper or fabricated attribution string can look like enforcement.

ADK gives this shape at both boundaries. Its plugin manager routes model calls through `before_model_callback`, `after_model_callback`, and `on_model_error_callback`; a non-`None` callback return halts later callbacks and propagates up. The same framework routes tool execution through `before_tool_callback` and `after_tool_callback`; a before-tool callback can supply a response and skip the tool call, while an after-tool callback can replace the result. The minimal code shows the mechanic. ADK shows it in framework code across model and tool boundaries.

## Determinism Move

Guardrail Decorator constrains `tool_boundary_ambiguity` by making the policy decision live at the call boundary the model crosses. The tool boundary is where policy is enforced, not merely where the next cursor entry appears.

It constrains `criteria_drift` by anchoring policy in code that survives prompt rewrites, persona changes, summarization, and context compaction.

The move is policy at the boundary, not in the prose.

## Observable Signal

Every Guardrail Decorator report should include:

* call site, such as model identity, tool name, or retriever name;
* registered policies in precedence order;
* hook fired (`before`, `after`, `on_error`, or `none`);
* policy that fired, or `none`;
* decision (`pass`, `deny`, `replace`, `sanitize`, `recover`);
* args;
* original_response, or `not_invoked` if a before-hook denied;
* override_response, or `none` for pass-through.

A useful report names the blocked call:

```text
call_site: tool:delete_file
policies: [confirm_destructive, scope_guard, audit_logger]
hook_fired: before
policy: confirm_destructive
decision: deny
args: {"path": "/etc/passwd"}
original_response: not_invoked
override_response: {"error": "destructive operation requires explicit confirmation"}
```

## Failure Modes

* **Prompt-Only Policy:** the policy text lives in the system prompt, and model compliance is the only enforcement. Move the rule into a registered callback at the call boundary.
* **No-Op Hook:** a decorator exists but always returns `None`. The interface is policy-shaped, the implementation is pass-through. Add a positive deny-path test and assert the original call was not invoked.
* **Hook Without Decision Log:** the wrapper short-circuits silently. Stamp which policy fired, which hook fired, and what override was returned.
* **Adapter Mistaken For Guardrail:** a type-conversion wrapper is labeled "guardrail" but does not enforce policy. Type adaptation belongs on Tool Adapter. Rename the wrapper to match its job.

## Use When

Use this pattern when:

* the framework supports lifecycle hooks at model, tool, retriever, or output boundaries;
* policy enforcement gates side effects such as file writes, network calls, deletions, charges, sends, or deploys;
* policy needs to survive prompt rewrites, persona tests, and context compaction;
* audit requires a decision log per call;
* the policy can be expressed as a deterministic decision function rather than a subjective judgment.

## Do Not Use When

Do not reach for Guardrail Decorator when:

* the policy is genuinely subjective and a **Judge Harness** is the right verifier;
* the framework's call boundaries cannot be wrapped;
* a one-off conditional in the call site is clearer than registering a decorator;
* shape normalization is the actual need, which belongs on Tool Adapter.

If hook surfaces are unavailable, label the policy as advisory and add a separate executable check downstream. Do not imply enforcement that does not exist.

## Evidence

* **Verification Design Principle 1:** the design doc names external signals over self-review. Prompt-only policy has the same failure shape: the model judges the policy it is asked to obey.
* **Verification Design Principle 6:** the design doc treats executable checks as the strongest verification move. A registered callback is the policy-side analog: executable enforcement instead of verbal instruction.
* **[ADK](https://github.com/google/adk-python) plugin model callbacks:** the guardrail causal sweep records model-boundary callbacks with before, after, and error hooks. Non-`None` returns halt later callbacks and propagate upward.
* **ADK plugin tool callbacks:** the same sweep records tool-boundary callbacks where a before-tool callback can skip the tool call and an after-tool callback can replace the result.
* **No-credible-antipattern result:** the antipattern cleanup sweep inspected ADK plugin examples and [AutoGPT](https://github.com/Significant-Gravitas/AutoGPT) `validate_url` without finding a no-op callback instance to promote.

## Related Patterns

* **Constitution:** defines the rubric the guardrail enforces. Criteria source and boundary enforcement compose.
* **Tool Adapter:** normalizes call shape. Guardrail Decorator enforces call policy. Same wrapper surface, different job.
* **Causal Tag:** callback context carries IDs that make the decision log queryable. The guardrail decision becomes another stamped event on the trace.
* **Trajectory Cursor:** cursor and policy hooks share the same boundary. The cursor advances after the policy permits, not before.
* **Adversarial Frame:** post-call sanitization can execute default-no rejection rules on tool or model outputs.
