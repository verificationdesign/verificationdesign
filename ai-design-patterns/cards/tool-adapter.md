# Tool Adapter

*(Orchestration Pattern)*

## Name

**Tool Adapter**

Also known as: Tool Wrapper, Schema Adapter, Function Adapter.

## Intent

Normalize model-emitted tool calls at a typed boundary: derive or fetch a schema, validate arguments before invocation, call the tool with typed arguments, and return a typed observation.

## Problem

Models do not naturally emit Python function calls. They emit text or loosely shaped JSON that a runtime has to translate into code.

The fragile version spreads that translation across call sites:

* parse arguments out of a prompt with regexes or string splits;
* f-string the values into a function call;
* trust that the model used the expected names and types;
* reformat the observation inline for the next prompt;
* duplicate slightly different schemas in each tool call site.

That makes the boundary ambiguous. Is the tool contract the prompt text, the regex, the function signature, or the model's last answer? Malformed arguments can reach side-effectful tools before validation. A hand-copied schema can drift from the actual function. Observations return as raw strings and get reinterpreted differently at the next step.

`verification_design.md` Principle 6 names the stronger move: use executable checks instead of interpretation. Tool Adapter applies that principle at the tool boundary. Argument validation is an executable check that runs before the side effect.

## Forces

* **Inline conversion vs. typed adapter.** Inline conversion is quick for one script. A typed adapter centralizes the boundary when a model can call tools repeatedly.
* **Derived schema vs. hand-written schema.** Deriving from a typed function or fetching a protocol schema reduces drift. Hand-written schemas are sometimes necessary, but they need an owner.
* **Validate-before-invoke vs. trust-the-model.** Validation blocks malformed calls before side effects.
* **Function adapter vs. protocol adapter.** A local function adapter wraps typed code. A protocol adapter converts external tool schemas into the host framework.
* **Strict schema vs. permissive parsing.** Strictness catches bad calls early; permissive parsing can hide boundary errors until the tool runs.

## Solution

Put a single adapter at the tool boundary.

The adapter owns:

* tool registration;
* schema derivation or retrieval;
* model-facing schema exposure;
* argument validation;
* invocation with typed arguments;
* typed observation formatting;
* a call record with schema source, validation result, call id, and return type.

The model may propose a tool call. The adapter decides whether the call is valid enough to invoke.

## Mechanism

1. **Register the tool.** Store name, description, callable or protocol reference, and return type.
2. **Derive or fetch the schema.** Use the typed function signature or an external protocol schema.
3. **Expose the schema to the model.** The model sees a stable tool contract rather than prose-only instructions.
4. **Validate arguments before invocation.** Reject missing fields, unexpected fields, or type mismatches before the tool runs.
5. **Return a typed observation.** Record schema source, validated args, call id, observation type, and return value.

## Pattern / Antipattern

The same task: allow a model to call `create_ticket(title: str, priority: int)`. The antipattern parses a model string inline and invokes the function without validation. The pattern validates against a derived schema before invocation.

### Antipattern: inline string conversion

Ad-hoc conversion is not wrong in a one-off script. It becomes a verification antipattern when an untyped, unvalidated boundary carries model output into side-effectful calls.

```python
import re


created_tickets: list[dict] = []


def create_ticket(title: str, priority: int) -> dict:
    created_tickets.append({"title": title, "priority": priority})
    return {"ticket_id": "T-1", "title": title, "priority": priority}


def inline_tool_call(model_text: str) -> str:
    title = re.search(r"title=(.*?);", model_text).group(1)
    priority = re.search(r"priority=(.*)", model_text).group(1)

    result = create_ticket(title=title, priority=priority)
    return f"created ticket {result['ticket_id']}: {result['title']}"


observation = inline_tool_call("tool=create_ticket title=Prod outage; priority=urgent")
```

The call site has no schema and no validation. The model emitted `priority=urgent`; the tool received it even though the code-facing contract expects an integer. The bug is not regex itself. The bug is that parsing, validation, invocation, and observation formatting are scattered at the call site.

### Pattern: derived schema adapter

The structured implementation derives a schema from the function signature and validates model-emitted arguments before invoking the tool.

```python
from dataclasses import dataclass
from inspect import signature
import json
from typing import Any, get_type_hints
from uuid import uuid4


@dataclass(frozen=True)
class CallRecord:
    call_id: str
    tool_name: str
    schema_source: str
    validated: bool
    validated_args: dict[str, Any]
    observation_type: str
    value: Any
    validation_error: str | None


@dataclass(frozen=True)
class Observation:
    record: CallRecord


class FunctionToolAdapter:
    def __init__(self, name: str, fn, id_factory=None):
        self.name = name
        self.fn = fn
        self.signature = signature(fn)
        self.type_hints = get_type_hints(fn)
        self.id_factory = id_factory or (lambda: str(uuid4()))
        self.calls: list[CallRecord] = []

    @property
    def schema(self) -> dict[str, str]:
        return {
            name: getattr(self.type_hints.get(name, Any), "__name__", "Any")
            for name in self.signature.parameters
        }

    def validate(self, args: dict[str, Any]) -> dict[str, Any]:
        expected = set(self.signature.parameters)
        if set(args) != expected:
            raise ValueError(f"expected args {sorted(expected)}, got {sorted(args)}")

        validated: dict[str, Any] = {}
        for name, value in args.items():
            expected_type = self.type_hints.get(name, Any)
            if expected_type in {str, int, float, bool}:
                if type(value) is not expected_type:
                    raise TypeError(f"{name} must be {expected_type.__name__}")
            elif expected_type is not Any and not isinstance(value, expected_type):
                raise TypeError(f"{name} must be {expected_type.__name__}")
            validated[name] = value
        return validated

    def run_json(self, args: dict[str, Any]) -> Observation:
        call_id = self.id_factory()
        try:
            validated_args = self.validate(args)
        except (TypeError, ValueError) as error:
            self.calls.append(
                CallRecord(
                    call_id=call_id,
                    tool_name=self.name,
                    schema_source="typed_signature",
                    validated=False,
                    validated_args={},
                    observation_type="error",
                    value=None,
                    validation_error=str(error),
                )
            )
            raise

        value = self.fn(**validated_args)
        record = CallRecord(
            call_id=call_id,
            tool_name=self.name,
            schema_source="typed_signature",
            validated=True,
            validated_args=validated_args,
            observation_type=type(value).__name__,
            value=value,
            validation_error=None,
        )
        self.calls.append(record)
        return Observation(record=record)


def render_report(adapter: FunctionToolAdapter, record: CallRecord) -> str:
    validation_error = record.validation_error or "none"
    rendered_value = (
        json.dumps(record.value)
        if record.value is not None
        else "none"
    )
    return "\n".join(
        [
            f"tool_name: {record.tool_name}",
            f"schema_source: {record.schema_source}",
            f"schema_present: {str(bool(adapter.schema)).lower()}",
            f"args_validated: {str(record.validated).lower()}",
            f"validation_error: {validation_error}",
            f"call_id: {record.call_id}",
            f"observation_type: {record.observation_type}",
            f"return_value: {rendered_value}",
        ]
    )


created_tickets: list[dict[str, Any]] = []


def create_ticket(title: str, priority: int) -> dict[str, Any]:
    created_tickets.append({"title": title, "priority": priority})
    return {"ticket_id": "T-1", "title": title, "priority": priority}


def escalate(ticket_id: str, urgent: bool) -> dict[str, Any]:
    return {"ticket_id": ticket_id, "urgent": urgent}


call_ids = iter(["call-001", "call-002", "call-003"])
tool = FunctionToolAdapter("create_ticket", create_ticket, lambda: next(call_ids))
escalator = FunctionToolAdapter("escalate", escalate, lambda: "escalate-001")
observation = tool.run_json({"title": "Prod outage", "priority": 1})
escalation = escalator.run_json({"ticket_id": "T-1", "urgent": True})

try:
    tool.run_json({"title": "Prod outage", "priority": "urgent"})
except TypeError as error:
    string_error = str(error)

try:
    tool.run_json({"title": "Prod outage", "priority": True})
except TypeError as error:
    bool_error = str(error)

try:
    escalator.run_json({"ticket_id": "T-1", "urgent": 1})
except TypeError as error:
    int_error = str(error)

expected_report = """tool_name: create_ticket
schema_source: typed_signature
schema_present: true
args_validated: true
validation_error: none
call_id: call-001
observation_type: dict
return_value: {"ticket_id": "T-1", "title": "Prod outage", "priority": 1}"""

expected_rejected_report = """tool_name: create_ticket
schema_source: typed_signature
schema_present: true
args_validated: false
validation_error: priority must be int
call_id: call-002
observation_type: error
return_value: none"""

assert tool.schema == {"title": "str", "priority": "int"}
assert escalator.schema == {"ticket_id": "str", "urgent": "bool"}
assert escalation.record.validated is True
assert created_tickets == [{"title": "Prod outage", "priority": 1}]
assert string_error == "priority must be int"
assert bool_error == "priority must be int"
assert int_error == "urgent must be bool"
assert [call.validated for call in tool.calls] == [True, False, False]
assert tool.calls[1].validation_error == "priority must be int"
assert tool.calls[2].validation_error == "priority must be int"
assert render_report(tool, observation.record) == expected_report
assert render_report(tool, tool.calls[1]) == expected_rejected_report
```

AutoGen's `FunctionTool` and `BaseTool` have this function-adapter shape. `FunctionTool` wraps a Python function, derives an argument model from the typed signature, passes that model to `BaseTool`, exposes a JSON-like schema, validates JSON arguments through the argument model in `run_json`, and only then invokes the wrapped function.

CrewAI's MCP resolver is the protocol-adapter sibling. It fetches external MCP tool schemas, converts JSON schemas into local Pydantic argument models where possible, caches schemas by server URL, and wraps the result as a local `BaseTool`. That is the same adapter move applied to a remote tool protocol instead of a Python function signature.

The validator above is intentionally small for a pasted example. Production adapters usually delegate this work to an argument model or schema validator.

## Determinism Move

Tool Adapter constrains `tool_boundary_ambiguity` by making the model-to-tool boundary a typed, validated schema instead of an implicit string contract. Malformed model output fails at the door instead of inside the tool.

It also constrains `criteria_drift` because the schema is a single validation criterion derived from the tool or protocol. The call site does not maintain a hand-copied shape that can drift from the implementation.

The determinism move is making the tool contract a derived, validated schema at one boundary.

## Observable Signal

Every Tool Adapter report should include:

* tool name;
* schema source, such as `typed_signature` or `protocol_fetch`;
* schema-present boolean;
* args-validated boolean;
* validation error, or `none`;
* call id, deterministic in tests when an id factory is supplied;
* observation type;
* return value or error surface.

A useful report names the boundary:

```text
tool_name: create_ticket
schema_source: typed_signature
schema_present: true
args_validated: true
validation_error: none
call_id: call-001
observation_type: dict
return_value: {"ticket_id": "T-1", "title": "Prod outage", "priority": 1}
```

A rejected call should surface the same boundary with a validation failure:

```text
tool_name: create_ticket
schema_source: typed_signature
schema_present: true
args_validated: false
validation_error: priority must be int
call_id: call-002
observation_type: error
return_value: none
```

## Failure Modes

* **Inline String Conversion:** arguments are regex-parsed or split out of model text at the call site. Move parsing and validation into an adapter.
* **Duplicated Schema:** each call site hand-writes the expected argument shape. Derive the schema from the tool or protocol once.
* **Trust-the-Model:** the adapter invokes the tool before validating arguments. Validate before side effects.
* **Untyped Observation:** the tool returns a raw string and every caller reformats it differently. Return a typed observation.
* **Schema Staleness:** a protocol schema is fetched once and never refreshed. Cache with an invalidation policy or schema version.

## Use When

Use this pattern when:

* a model calls tools with structured arguments;
* tools have typed functions or external protocol schemas;
* malformed arguments could cause side effects;
* audit requires a single owner for tool format;
* observations need to be consumed by later verification or trajectory steps.

## Do Not Use When

Do not reach for Tool Adapter when:

* there is a single trivial tool with no arguments;
* the framework already provides a typed tool boundary and double-wrapping would add no signal;
* the wrapper enforces policy rather than adapting types. Use Guardrail Decorator;
* the call is fully internal and no model output crosses the boundary.

If schema validation is unavailable, label the tool boundary as advisory and add a downstream executable check.

## Evidence

* **Verification Design Principle 6:** the design doc treats executable checks as the strongest verification move; schema validation is the executable check at the tool boundary.
* **[AutoGen](https://github.com/microsoft/autogen) FunctionTool and BaseTool:** the orchestration sweep records a direct function-adapter instance: typed function signatures generate argument schemas, JSON calls are validated, and validated fields are mapped into the wrapped function.
* **[CrewAI](https://github.com/crewAIInc/crewAI) MCP tool resolver:** the orchestration sweep records a direct protocol-adapter instance: external MCP schemas are fetched, converted to local argument models, cached, and exposed as local tools.
* **Synthesized inline-conversion antipattern:** no OSS instance was promoted for the antipattern. This card synthesizes the failure case because the issue is the absence of schema ownership and validate-before-invoke behavior.

## Related Patterns

* **Guardrail Decorator:** enforces policy at the boundary; Tool Adapter adapts type shape at the same boundary.
* **Executable Analog:** schema validation is an executable check for model-emitted tool calls.
* **Comparator:** uses an explicit expected-vs-actual check; Tool Adapter applies that check to argument shapes.
* **Causal Tag:** tags tool calls so the boundary is auditable across logs.
* **Trajectory Cursor:** records tool boundaries as cursor points in the agent trajectory.
