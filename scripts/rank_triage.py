#!/usr/bin/env python3
"""Anchor-calibrated comparative ranking of Pass 1 triage candidates.

Pass 2 layer over `research/triage/`. Consumes existing triage notes plus a
human-tagged anchor fixture (`research/triage/anchors.md`), asks a model to
place each candidate against weak/adjacent/strong anchors using asymmetric
framing, drops runs whose anchor ordering inverts, and emits a markdown
digest with median bucket and full per-run distribution.

Contract: `research/triage/ranking_design.md`.

The script fails closed when:
- the anchor fixture is missing required human fields
- fewer than one anchor per role is tagged
- all runs are dropped due to anchor inversions and no buckets can be reported
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import re
import shlex
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path


PRINCIPLES = {
    "principle-1": "External Signals Over Self-Review: prefer binary pass/fail signals that do not depend on the agent's judgment.",
    "principle-2": "Independence Between Generation and Verification: the verification step must not be conditioned on the draft.",
    "principle-3": "Step-Level Checkpoints: verify intermediate steps throughout the workflow, not just the final output.",
    "principle-4": "Adversarial Framing: ask what could fail, not whether the output looks right.",
    "principle-5": "Explicit Criteria: externally defined, specific, unambiguous criteria constrain rationalization.",
    "principle-6": "Executable Verification Is King: tests and executable analogs provide binary external signals.",
    "principle-7": "Cross-Family Beats Self-Verification: self-verification and intra-family verification share blind spots.",
    "principle-8": "Simulate Debate: argue against the output before concluding.",
    "principle-9": "Isolate Verification from Ambient State: assertions must prove the action caused the expected outcome.",
}

ROLES = ("strong", "adjacent", "weak")
ANCHOR_SOURCES = ("reviewed", "triage", "external")
COMP_VALUES = ("weaker", "comparable", "stronger")

BUCKET_RANK = {"below-weak": 0, "adjacent-weak": 1, "strong-adjacent": 2, "above-strong": 3}
BUCKET_LABELS = {
    "above-strong": "above strong anchor (read now)",
    "strong-adjacent": "between strong and adjacent (likely read)",
    "adjacent-weak": "between adjacent and weak (maybe later)",
    "below-weak": "below weak (probably skip)",
    "unclassified": "unclassified",
}

WORDS_RE = re.compile(r"\s+")
SECTION_RE = re.compile(r"(?ms)^### (?P<name>.+?)\n\n(?P<body>.*?)(?=\n### |\n## |\Z)")


# Parsing helpers

def one_line(text: str) -> str:
    text = text.replace(chr(0x2014), "; ")
    return WORDS_RE.sub(" ", text).strip()


def bullets(text: str) -> list[str]:
    out: list[str] = []
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("- "):
            out.append(line[2:].strip())
    return out


def line_value(block: str, label: str) -> str:
    match = re.search(rf"(?m)^{re.escape(label)}:[ \t]*(.*)$", block)
    return match.group(1).strip() if match else ""


def sections(block: str) -> dict[str, str]:
    return {match.group("name"): match.group("body").strip() for match in SECTION_RE.finditer(block)}


@dataclass
class TriageRecord:
    kind: str  # "candidate" or "anchor"
    title: str
    source: str
    initial_label: str
    confidence: str
    decision: str
    abstract: str
    key_findings: list[str]
    why: str
    what_would_change: str
    block: str

    def short_text(self) -> str:
        parts = [f"Title: {self.title}"]
        if self.abstract:
            parts.append(f"Abstract: {self.abstract}")
        if self.key_findings:
            parts.append("Key findings:")
            for finding in self.key_findings:
                parts.append(f"  - {finding}")
        if self.why:
            parts.append(f"Why it might matter: {self.why}")
        return "\n".join(parts)


@dataclass
class Anchor:
    record: TriageRecord
    role: str
    anchor_source: str
    rationale: str
    tagged_by: str


@dataclass
class Candidate:
    record: TriageRecord
    candidate_id: str


@dataclass
class RunOutput:
    candidate_id: str
    title: str
    source: str
    run_id: int
    seed: int
    skip_reason: str
    principle_touched: str
    abstract_claim: str
    principle_claim: str
    versus_weak: str
    versus_adjacent: str
    versus_strong: str
    bucket: str
    raw_response: str = ""


@dataclass
class DroppedRun:
    run_id: int
    seed: int
    inversions: list[str]


@dataclass
class AggregatedCandidate:
    candidate_id: str
    title: str
    source: str
    bucket_distribution: list[str]
    median_bucket: str
    bucket_disagreement: bool
    principles_touched: list[str]
    runs_used: int
    runs_dropped: int
    per_run: list[RunOutput]


def split_records(text: str) -> list[tuple[str, str, str]]:
    """Return list of (kind, title, block) per `## Candidate:` or `## Anchor` heading."""
    out: list[tuple[str, str, str]] = []
    for raw_block in re.split(r"(?m)^## ", text)[1:]:
        first_line, _, _ = raw_block.partition("\n")
        if first_line.startswith("Candidate:"):
            kind = "candidate"
            title = first_line[len("Candidate:"):].strip() or "(untitled)"
        elif first_line.startswith("Anchor"):
            kind = "anchor"
            after = first_line[len("Anchor"):].lstrip(":").strip()
            title = after or "(untagged anchor slot)"
        else:
            continue
        out.append((kind, title, "## " + raw_block))
    return out


def to_record(kind: str, title: str, block: str) -> TriageRecord:
    sec = sections(block)
    return TriageRecord(
        kind=kind,
        title=title,
        source=line_value(block, "Source") or "(no source)",
        initial_label=line_value(block, "Initial label"),
        confidence=line_value(block, "Confidence"),
        decision=line_value(block, "Decision"),
        abstract=one_line(sec.get("Abstract Paraphrase", "")),
        key_findings=bullets(sec.get("Key Findings", "")),
        why=one_line(sec.get("Why It Might Matter", "")),
        what_would_change=one_line(sec.get("What Would Change In The Doc", "")),
        block=block,
    )


def validate_anchor(record: TriageRecord) -> Anchor:
    role = line_value(record.block, "Anchor role")
    src = line_value(record.block, "Anchor source")
    rationale = line_value(record.block, "Anchor rationale")
    tagged_by = line_value(record.block, "Tagged by")
    errors: list[str] = []
    if record.decision != "anchor":
        errors.append(f"Decision must be 'anchor' (got {record.decision!r})")
    if role not in ROLES:
        errors.append(f"Anchor role must be one of {list(ROLES)} (got {role!r})")
    if src not in ANCHOR_SOURCES:
        errors.append(f"Anchor source must be one of {list(ANCHOR_SOURCES)} (got {src!r})")
    if not rationale:
        errors.append("Anchor rationale is required and must be non-empty")
    if not tagged_by:
        errors.append("Tagged by is required and must be non-empty")
    if not record.abstract and not record.key_findings:
        errors.append("anchor must include Abstract Paraphrase or Key Findings to be comparable")
    if errors:
        raise ValueError(f"anchor {record.title!r} invalid:\n  - " + "\n  - ".join(errors))
    return Anchor(record=record, role=role, anchor_source=src, rationale=rationale, tagged_by=tagged_by)


def parse_anchors(path: Path) -> tuple[dict[str, Anchor], str]:
    text = path.read_text(encoding="utf-8")
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()[:12]
    records = split_records(text)
    anchors_by_role: dict[str, Anchor] = {}
    errors: list[str] = []
    for kind, title, block in records:
        if kind != "anchor":
            continue
        record = to_record(kind, title, block)
        try:
            anchor = validate_anchor(record)
        except ValueError as exc:
            errors.append(str(exc))
            continue
        if anchor.role in anchors_by_role:
            errors.append(f"more than one anchor tagged role {anchor.role!r}; only one supported in v1")
        anchors_by_role[anchor.role] = anchor
    missing = [role for role in ROLES if role not in anchors_by_role]
    if missing:
        errors.append(f"missing required anchor role(s): {missing}")
    if errors:
        raise SystemExit(
            f"anchor fixture {path} invalid; refusing to run:\n  - " + "\n  - ".join(errors)
        )
    return anchors_by_role, digest


def parse_candidates_from_triage(paths: list[Path]) -> list[Candidate]:
    candidates: list[Candidate] = []
    for path in paths:
        text = path.read_text(encoding="utf-8")
        for kind, title, block in split_records(text):
            if kind != "candidate":
                continue
            record = to_record(kind, title, block)
            if record.decision == "anchor":
                continue
            cid = hashlib.sha256(record.source.encode("utf-8")).hexdigest()[:12]
            candidates.append(Candidate(record=record, candidate_id=cid))
    return candidates


# Prompts

def principles_index() -> str:
    return "\n".join(f"- {key}: {label}" for key, label in PRINCIPLES.items())


def shuffled_anchors(anchors: dict[str, Anchor], seed: int) -> list[Anchor]:
    rng = random.Random(seed)
    order = list(ROLES)
    rng.shuffle(order)
    return [anchors[role] for role in order]


def candidate_prompt(candidate: Candidate, anchors: dict[str, Anchor], seed: int) -> str:
    rotated = shuffled_anchors(anchors, seed)
    anchor_blocks: list[str] = []
    for anchor in rotated:
        anchor_blocks.append(
            f"Anchor (role: {anchor.role}):\n{anchor.record.short_text()}"
        )
    anchors_text = "\n\n".join(anchor_blocks)
    return f"""You are calibrating reading priority for a research-notes repo on verification design.

Repo principles (use these IDs for principle_touched):
{principles_index()}

Three known anchors are presented below in rotated order. Their roles (strong, adjacent, weak) are labelled. Strong means the anchor is the kind of work the doc would clearly integrate. Weak means recognizable adjacent eval work that the doc would not integrate. Adjacent is between.

Candidate to evaluate:

{candidate.record.short_text()}

Anchors:

{anchors_text}

Answer these three asymmetric comparisons. Each invites a different failure mode so the model has explicit permission to reject the candidate in either direction. Use values: weaker, comparable, stronger.

1. versus_weak: is the candidate WEAKER than the weak anchor for informing the verification-design doc?
2. versus_adjacent: is the candidate COMPARABLE to the adjacent anchor?
3. versus_strong: is the candidate STRONGER than the strong anchor?

Also report:
- skip_reason: strongest single reason a maintainer should skip this candidate, or the literal string "none"
- principle_touched: exactly one of "none", "new-candidate", or a principle ID from the list above
- abstract_claim: short verbatim phrase from the candidate abstract that best represents its contribution
- principle_claim: short verbatim phrase from the principle named above, or "none"

Return JSON only, no preamble, no markdown fence:

{{
  "skip_reason": "...",
  "principle_touched": "...",
  "abstract_claim": "...",
  "principle_claim": "...",
  "versus_weak": "weaker|comparable|stronger",
  "versus_adjacent": "weaker|comparable|stronger",
  "versus_strong": "weaker|comparable|stronger"
}}
"""


def anchor_pair_prompt(stronger: Anchor, weaker: Anchor, seed: int) -> tuple[str, str]:
    rng = random.Random(seed)
    presented = [("X", stronger), ("Y", weaker)]
    rng.shuffle(presented)
    blocks: list[str] = []
    for label, anchor in presented:
        blocks.append(f"Item {label}:\n{anchor.record.short_text()}")
    items_text = "\n\n".join(blocks)
    expected_stronger_label = next(label for label, anchor in presented if anchor is stronger)
    expected_verdict = "stronger" if expected_stronger_label == "X" else "weaker"
    prompt = f"""You are checking whether two known anchors are ordered correctly by reading-priority strength for a verification-design methodology doc.

{items_text}

Question: relative to the doc, is Item X STRONGER than, COMPARABLE to, or WEAKER than Item Y?

Return JSON only, no preamble:

{{
  "x_versus_y": "stronger|comparable|weaker"
}}
"""
    return prompt, expected_verdict


# Model interface

def parse_model_json(text: str) -> dict:
    text = text.strip()
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        raise ValueError(f"no JSON object in model output: {text[:200]!r}")
    return json.loads(match.group(0))


def call_model_subprocess(prompt: str, cmd: list[str], timeout: int) -> dict:
    result = subprocess.run(
        cmd, input=prompt, capture_output=True, text=True, timeout=timeout
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"model command exited {result.returncode}: {result.stderr.strip()[:300]}"
        )
    return parse_model_json(result.stdout)


def stub_candidate_response(candidate: Candidate, seed: int) -> dict:
    h = int(hashlib.sha256(f"{candidate.candidate_id}:{seed}".encode("utf-8")).hexdigest(), 16)
    bucket_choice = h % 4
    if bucket_choice == 0:
        versus = ("stronger", "stronger", "stronger")
    elif bucket_choice == 1:
        versus = ("stronger", "stronger", "weaker")
    elif bucket_choice == 2:
        versus = ("stronger", "weaker", "weaker")
    else:
        versus = ("weaker", "weaker", "weaker")
    principle_idx = (h >> 4) % (len(PRINCIPLES) + 1)
    if principle_idx == len(PRINCIPLES):
        principle = "none"
    else:
        principle = list(PRINCIPLES.keys())[principle_idx]
    return {
        "skip_reason": "none" if bucket_choice < 3 else "dry-run stub: below weak anchor",
        "principle_touched": principle,
        "abstract_claim": (candidate.record.abstract.split(".")[0] or candidate.record.title)[:120],
        "principle_claim": PRINCIPLES.get(principle, "none") if principle.startswith("principle-") else "none",
        "versus_weak": versus[0],
        "versus_adjacent": versus[1],
        "versus_strong": versus[2],
    }


def stub_anchor_pair_response(stronger: Anchor, weaker: Anchor, seed: int) -> dict:
    _prompt, expected = anchor_pair_prompt(stronger, weaker, seed)
    return {"x_versus_y": expected, "_expected_x_versus_y": expected}


# Comparison logic

def derive_bucket(versus_weak: str, versus_adjacent: str, versus_strong: str) -> str:
    if versus_strong == "stronger":
        return "above-strong"
    if versus_adjacent in {"comparable", "stronger"}:
        return "strong-adjacent"
    if versus_adjacent == "weaker" and versus_weak != "weaker":
        return "adjacent-weak"
    if versus_weak == "weaker":
        return "below-weak"
    return "unclassified"


def median_bucket(buckets: list[str]) -> str:
    if not buckets:
        return "unclassified"
    ranked = sorted(buckets, key=lambda b: BUCKET_RANK.get(b, -1))
    return ranked[(len(ranked) - 1) // 2]


# Run orchestration

def run_anchor_inversion_check(
    anchors: dict[str, Anchor],
    run_id: int,
    seed: int,
    call_pair,
) -> list[str]:
    pairs = [
        (anchors["strong"], anchors["adjacent"], "strong>adjacent"),
        (anchors["adjacent"], anchors["weak"], "adjacent>weak"),
        (anchors["strong"], anchors["weak"], "strong>weak"),
    ]
    inversions: list[str] = []
    for i, (a, b, label) in enumerate(pairs):
        pair_seed = seed * 1000 + run_id * 10 + i
        try:
            response = call_pair(a, b, pair_seed)
        except Exception as exc:  # noqa: BLE001
            inversions.append(f"{label}: model error {exc}")
            continue
        verdict = response.get("x_versus_y", "")
        expected = response.get("_expected_x_versus_y", "stronger")
        if verdict != expected:
            inversions.append(f"{label}: expected {expected!r}, got {verdict!r}")
    return inversions


def run_candidate(
    candidate: Candidate,
    anchors: dict[str, Anchor],
    run_id: int,
    seed: int,
    call_candidate,
) -> RunOutput | None:
    try:
        response = call_candidate(candidate, anchors, seed)
    except Exception as exc:  # noqa: BLE001
        print(
            f"warn: candidate {candidate.record.title!r} run {run_id}: model error: {exc}",
            file=sys.stderr,
        )
        return None
    vw = response.get("versus_weak", "")
    va = response.get("versus_adjacent", "")
    vs = response.get("versus_strong", "")
    for value, name in ((vw, "versus_weak"), (va, "versus_adjacent"), (vs, "versus_strong")):
        if value not in COMP_VALUES:
            print(
                f"warn: candidate {candidate.record.title!r} run {run_id}: "
                f"invalid {name}={value!r}; marking unclassified",
                file=sys.stderr,
            )
    principle = response.get("principle_touched", "none")
    if principle not in PRINCIPLES and principle not in {"none", "new-candidate"}:
        print(
            f"warn: candidate {candidate.record.title!r} run {run_id}: "
            f"invalid principle_touched={principle!r}; coercing to 'none'",
            file=sys.stderr,
        )
        principle = "none"
    bucket = derive_bucket(vw, va, vs)
    return RunOutput(
        candidate_id=candidate.candidate_id,
        title=candidate.record.title,
        source=candidate.record.source,
        run_id=run_id,
        seed=seed,
        skip_reason=str(response.get("skip_reason", "none")),
        principle_touched=principle,
        abstract_claim=str(response.get("abstract_claim", "")),
        principle_claim=str(response.get("principle_claim", "")),
        versus_weak=vw,
        versus_adjacent=va,
        versus_strong=vs,
        bucket=bucket,
        raw_response=json.dumps(response, ensure_ascii=False),
    )


def aggregate(
    candidates: list[Candidate],
    per_candidate_runs: dict[str, list[RunOutput]],
    runs_attempted: int,
    runs_dropped: int,
) -> list[AggregatedCandidate]:
    aggregated: list[AggregatedCandidate] = []
    for cand in candidates:
        runs = per_candidate_runs.get(cand.candidate_id, [])
        buckets = [r.bucket for r in runs]
        bucket = median_bucket(buckets) if buckets else "unclassified"
        disagreement = len(set(buckets)) > 1
        principles = sorted({r.principle_touched for r in runs if r.principle_touched})
        aggregated.append(
            AggregatedCandidate(
                candidate_id=cand.candidate_id,
                title=cand.record.title,
                source=cand.record.source,
                bucket_distribution=buckets,
                median_bucket=bucket,
                bucket_disagreement=disagreement,
                principles_touched=principles,
                runs_used=len(runs),
                runs_dropped=runs_dropped,
                per_run=runs,
            )
        )
    return aggregated


# Render

def render(
    aggregated: list[AggregatedCandidate],
    anchors: dict[str, Anchor],
    anchor_path: Path,
    anchor_hash: str,
    triage_paths: list[Path],
    runs_attempted: int,
    dropped_runs: list[DroppedRun],
    model_label: str,
    seeds: list[int],
) -> str:
    lines: list[str] = [
        "# Triage Ranking Digest",
        "",
        "Scope: anchor-calibrated reading priority. Buckets are not evidence grades.",
        f"Anchor file: {anchor_path} (sha256/12: {anchor_hash})",
        f"Triage inputs: {', '.join(str(p) for p in triage_paths)}",
        f"Model: {model_label}",
        f"Runs attempted: {runs_attempted}",
        f"Runs dropped: {len(dropped_runs)}",
        f"Seeds: {seeds}",
        "",
        "Anchors (role: source):",
    ]
    for role in ROLES:
        anchor = anchors[role]
        lines.append(
            f"- {role}: {anchor.record.title} ({anchor.record.source}); "
            f"tagged by {anchor.tagged_by}; anchor source: {anchor.anchor_source}"
        )
    lines.append("")
    if not aggregated or all(c.runs_used == 0 for c in aggregated):
        lines.extend([
            "## No buckets reported",
            "",
            "All runs were dropped due to anchor inversions, or no candidates were parsed.",
            "See Dropped runs section for the specific inversions.",
            "",
        ])
    else:
        for bucket_key in ("above-strong", "strong-adjacent", "adjacent-weak", "below-weak"):
            in_bucket = [c for c in aggregated if c.median_bucket == bucket_key]
            in_bucket.sort(key=lambda c: (not c.bucket_disagreement, c.title))
            lines.append(f"## {BUCKET_LABELS[bucket_key]}")
            lines.append("")
            if not in_bucket:
                lines.append("(none)")
                lines.append("")
                continue
            for cand in in_bucket:
                principles = ", ".join(cand.principles_touched) or "(none)"
                lines.extend([
                    f"### {cand.title}",
                    "",
                    f"- Source: {cand.source}",
                    f"- Bucket distribution: {cand.bucket_distribution}",
                    f"- Bucket disagreement: {cand.bucket_disagreement}",
                    f"- Principles touched: {principles}",
                    f"- Runs used: {cand.runs_used} (runs dropped this digest: {cand.runs_dropped})",
                    "",
                ])
        unclassified = [c for c in aggregated if c.median_bucket == "unclassified"]
        if unclassified:
            lines.append("## Unclassified (no surviving runs produced a usable bucket)")
            lines.append("")
            for cand in unclassified:
                lines.append(f"- {cand.title} ({cand.source})")
            lines.append("")
    lines.append("## Dropped runs")
    lines.append("")
    if dropped_runs:
        for dr in dropped_runs:
            lines.append(f"- run {dr.run_id} (seed {dr.seed}):")
            for inv in dr.inversions:
                lines.append(f"    - {inv}")
    else:
        lines.append("(none)")
    lines.append("")
    return "\n".join(lines).rstrip() + "\n"


# Driver

def build_call_candidate(args):
    if args.dry_run:
        def _call(candidate, _anchors, seed):
            return stub_candidate_response(candidate, seed)
        return _call

    cmd = shlex.split(args.model_cmd)

    def _call(candidate, anchors, seed):
        prompt = candidate_prompt(candidate, anchors, seed)
        return call_model_subprocess(prompt, cmd, args.model_timeout)

    return _call


def build_call_pair(args):
    if args.dry_run:
        def _call(stronger, weaker, seed):
            return stub_anchor_pair_response(stronger, weaker, seed)
        return _call

    cmd = shlex.split(args.model_cmd)

    def _call(stronger, weaker, seed):
        prompt, expected = anchor_pair_prompt(stronger, weaker, seed)
        response = call_model_subprocess(prompt, cmd, args.model_timeout)
        response["_expected_x_versus_y"] = expected
        return response

    return _call


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--anchors", required=True, type=Path, help="path to anchors.md fixture")
    parser.add_argument("--input", nargs="+", type=Path, help="triage note markdown files to rank")
    parser.add_argument("--outfile", type=Path, help="ranked digest output path")
    parser.add_argument("--runs", type=int, default=3, help="number of ranking runs (default 3)")
    parser.add_argument("--seed", type=int, default=None, help="base seed; per-run seeds derived from this")
    parser.add_argument(
        "--model-cmd",
        default="",
        help="shell command receiving prompt on stdin, returning JSON on stdout (e.g. 'claude -p')",
    )
    parser.add_argument("--model-label", default="", help="model name recorded in the digest header")
    parser.add_argument("--model-timeout", type=int, default=120, help="per-call model timeout in seconds")
    parser.add_argument("--dry-run", action="store_true", help="use deterministic stub instead of calling a model")
    parser.add_argument(
        "--validate-anchors",
        action="store_true",
        help="validate the anchor fixture and exit; no model calls, no digest output",
    )
    args = parser.parse_args()

    if not args.anchors.exists():
        raise SystemExit(f"anchor file not found: {args.anchors}")
    anchors, anchor_hash = parse_anchors(args.anchors)
    print(f"anchors ok: {args.anchors} (sha256/12: {anchor_hash})")
    for role in ROLES:
        anchor = anchors[role]
        print(
            f"  {role}: {anchor.record.title} ({anchor.record.source}); "
            f"tagged by {anchor.tagged_by}; source: {anchor.anchor_source}"
        )

    if args.validate_anchors:
        return 0

    if not args.input:
        raise SystemExit("--input is required unless --validate-anchors is set")
    if not args.outfile:
        raise SystemExit("--outfile is required unless --validate-anchors is set")
    if not args.dry_run and not args.model_cmd:
        raise SystemExit("either --model-cmd or --dry-run must be provided")

    candidates = parse_candidates_from_triage(args.input)
    if not candidates:
        raise SystemExit(f"no candidates found in {[str(p) for p in args.input]}")
    print(f"candidates parsed: {len(candidates)}")

    base_seed = args.seed if args.seed is not None else 1
    seeds = [base_seed + i * 17 for i in range(args.runs)]
    call_candidate = build_call_candidate(args)
    call_pair = build_call_pair(args)

    per_candidate_runs: dict[str, list[RunOutput]] = {c.candidate_id: [] for c in candidates}
    dropped_runs: list[DroppedRun] = []
    for run_idx in range(args.runs):
        run_id = run_idx + 1
        seed = seeds[run_idx]
        inversions = run_anchor_inversion_check(anchors, run_id, seed, call_pair)
        if inversions:
            dropped_runs.append(DroppedRun(run_id=run_id, seed=seed, inversions=inversions))
            print(f"run {run_id} (seed {seed}) DROPPED: {len(inversions)} inversion(s)")
            for inv in inversions:
                print(f"    {inv}")
            continue
        print(f"run {run_id} (seed {seed}) anchor ordering clean")
        for cand in candidates:
            cand_seed = seed + int(cand.candidate_id[:8], 16) % 997
            output = run_candidate(cand, anchors, run_id, cand_seed, call_candidate)
            if output is not None:
                per_candidate_runs[cand.candidate_id].append(output)

    runs_used = args.runs - len(dropped_runs)
    aggregated = aggregate(candidates, per_candidate_runs, args.runs, len(dropped_runs))

    digest = render(
        aggregated=aggregated,
        anchors=anchors,
        anchor_path=args.anchors,
        anchor_hash=anchor_hash,
        triage_paths=args.input,
        runs_attempted=args.runs,
        dropped_runs=dropped_runs,
        model_label=(args.model_label or ("dry-run-stub" if args.dry_run else args.model_cmd)),
        seeds=seeds,
    )
    args.outfile.parent.mkdir(parents=True, exist_ok=True)
    args.outfile.write_text(digest, encoding="utf-8")
    print(
        f"wrote {args.outfile}: {len(aggregated)} candidates; "
        f"{runs_used}/{args.runs} runs used; {len(dropped_runs)} dropped"
    )
    if runs_used == 0:
        print("FAIL: all runs were dropped due to anchor inversions; no buckets in digest")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
