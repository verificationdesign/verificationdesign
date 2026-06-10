#!/usr/bin/env python3
"""Create a compact reading digest from triage notes.

The digest is a consumption layer, not a review layer. It reads already-written
triage notes, keeps the model suggestion visible, and applies only lightweight
heuristics for sorting and evidence-type hints.
"""

from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from pathlib import Path


SECTION_RE = re.compile(r"(?ms)^### (?P<name>.+?)\n\n(?P<body>.*?)(?=\n### |\n## Candidate: |\Z)")
WORDS_RE = re.compile(r"\s+")


@dataclass
class Candidate:
    title: str
    source: str
    label: str
    decision: str
    abstract: str
    why: str
    key_claims: list[str]
    human_checks: list[str]
    credibility_flags: list[str]
    ordinal: int


def one_line(text: str) -> str:
    # Digest prose is generated repo prose, not a verbatim source excerpt.
    text = text.replace(chr(0x2014), "; ")
    return WORDS_RE.sub(" ", text).strip()


def first_sentence(text: str, max_chars: int = 260) -> str:
    text = one_line(text)
    if not text:
        return "(none)"
    match = re.search(r"(?<=[.!?])\s+", text)
    if match and match.start() <= max_chars:
        return text[: match.start()].strip()
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 3].rstrip() + "..."


def bullets(text: str) -> list[str]:
    out: list[str] = []
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("- "):
            out.append(line[2:].strip())
    return out


def sections(block: str) -> dict[str, str]:
    return {match.group("name"): match.group("body").strip() for match in SECTION_RE.finditer(block)}


def line_value(block: str, label: str) -> str:
    match = re.search(rf"(?m)^{re.escape(label)}:\s*(.+)$", block)
    return match.group(1).strip() if match else ""


def parse_candidates(path: Path) -> list[Candidate]:
    text = path.read_text(encoding="utf-8")
    parts = re.split(r"(?m)^## Candidate: ", text)
    candidates: list[Candidate] = []
    for part in parts[1:]:
        block = "## Candidate: " + part
        title = line_value(block, "## Candidate")
        if not title:
            title_match = re.match(r"## Candidate: (.+)", block)
            title = title_match.group(1).strip() if title_match else "(untitled)"
        section_map = sections(block)
        candidates.append(
            Candidate(
                title=title,
                source=line_value(block, "Source") or "(no source)",
                label=line_value(block, "Initial label") or "(unlabeled)",
                decision=line_value(block, "Decision") or "(no decision)",
                abstract=one_line(section_map.get("Abstract Paraphrase", "")),
                why=one_line(section_map.get("Why It Might Matter", "")),
                key_claims=bullets(section_map.get("Key Findings", "")),
                human_checks=bullets(section_map.get("Needs Human Review", "")),
                credibility_flags=bullets(section_map.get("Credibility Flags", "")),
                ordinal=len(candidates),
            )
        )
    return candidates


def evidence_type(candidate: Candidate) -> str:
    text = " ".join([candidate.title, candidate.abstract, " ".join(candidate.key_claims)]).lower()
    if any(term in text for term in ["benchmark", "bench", "dataset", "evaluation"]):
        return "benchmark or eval"
    if any(term in text for term in ["theorem", "formal verification", "bound", "theoretical"]):
        return "theory or formal method"
    if any(term in text for term in ["framework", "pipeline", "library", "system", "tool"]):
        return "system or method"
    if any(term in text for term in ["experiment", "empirical", "study"]):
        return "empirical study"
    return "unclear from abstract"


def doc_impact(candidate: Candidate) -> str:
    mapping = {
        "challenges": "may challenge or sharpen an existing principle",
        "narrows": "may narrow an existing claim",
        "extends": "may add adjacent technique or scope",
        "operational technique": "may add a reusable process or harness",
        "ignore": "probably no canonical-doc impact",
    }
    return mapping.get(candidate.label, "unclear impact")


def read_priority(candidate: Candidate) -> int:
    text = " ".join([candidate.title, candidate.abstract, " ".join(candidate.key_claims)]).lower()
    priority_one = [
        "llm-as-a-judge",
        "llm judge",
        "judge",
        "rubric",
        "process reward",
        "verifiable reward",
        "verification feedback",
        "formal verification",
        "prompt-injection",
        "prompt injection",
        "tool calls",
        "agent trajectory",
        "benchmark",
        "audit",
    ]
    priority_two = [
        "sycophancy",
        "preference optimization",
        "reward bias",
        "deception",
        "guardrail",
        "privacy",
        "reasoning shortcut",
        "out-of-distribution",
        "long-horizon",
    ]
    if any(term in text for term in priority_one):
        return 1
    if any(term in text for term in priority_two):
        return 2
    return 3


def topic_cluster(candidate: Candidate) -> str:
    text = " ".join([candidate.title, candidate.abstract, " ".join(candidate.key_claims)]).lower()
    if any(term in text for term in ["llm-as-a-judge", "llm judge", "judge", "rubric", "item response"]):
        return "judge reliability"
    if any(term in text for term in ["verifiable reward", "rlvr", "verification feedback", "process reward"]):
        return "verifiable rewards"
    if any(term in text for term in ["formal verification", "neuro-symbolic", "theorem"]):
        return "formal or symbolic verification"
    if any(term in text for term in ["prompt-injection", "prompt injection", "tool calls", "untrusted prompt"]):
        return "tool and prompt isolation"
    if any(term in text for term in ["sycophancy", "preference optimization", "reward bias", "outcome optimization"]):
        return "reward and preference failures"
    if any(term in text for term in ["benchmark", "bench", "dataset"]):
        return "benchmark design"
    if any(term in text for term in ["agent", "long-horizon", "multi-agent"]):
        return "agent evaluation"
    return "adjacent or unclear"


def credibility_line(candidate: Candidate) -> str:
    flags = [flag for flag in candidate.credibility_flags if flag != "(none)"]
    if flags:
        return "; ".join(flags[:2])
    return "no flags in triage note"


def render(
    candidates: list[Candidate],
    sources: list[Path],
    decision: str,
    max_items: int | None,
    source_label: str | None,
) -> str:
    ranked = sorted(candidates, key=lambda item: (read_priority(item), item.ordinal))
    total = len(ranked)
    if max_items is not None:
        ranked = ranked[:max_items]
    lines: list[str] = [
        "# Triage Digest",
        "",
        "Scope: compact reading queue from triage notes. Not a source review.",
        f"Decision filter: {decision}",
        "Input summary:",
        source_label or ", ".join(path.name for path in sources),
        "",
        f"Total candidates shown: {len(ranked)}",
        f"Total candidates available after filter: {total}",
        "",
    ]
    for index, candidate in enumerate(ranked, start=1):
        priority = read_priority(candidate)
        claims = candidate.key_claims[:2] or ["(none)"]
        human_question = candidate.human_checks[0] if candidate.human_checks else "(none)"
        lines.extend(
            [
                f"## {index}. {candidate.title}",
                "",
                f"- Source: {candidate.source}",
                f"- Read priority: {priority}",
                f"- Suggested decision: {candidate.decision}",
                f"- Suggested label: {candidate.label}",
                f"- Topic cluster: {topic_cluster(candidate)}",
                f"- Potential doc impact: {doc_impact(candidate)}",
                f"- Evidence type: {evidence_type(candidate)}",
                f"- Why read this: {first_sentence(candidate.why)}",
                f"- Abstract gist: {first_sentence(candidate.abstract)}",
                f"- Key data or claims: {'; '.join(claims)}",
                f"- Credibility flags: {credibility_line(candidate)}",
                f"- Human question: {human_question}",
                "",
            ]
        )
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Create a compact digest from triage notes.")
    parser.add_argument("--input", required=True, nargs="+", type=Path, help="triage note markdown files")
    parser.add_argument("--outfile", required=True, type=Path, help="digest markdown output path")
    parser.add_argument(
        "--decision",
        default="promote",
        choices=["promote", "keep-in-triage", "ignore", "all"],
        help="which model-suggested decision to include",
    )
    parser.add_argument("--max-items", type=int, default=None, help="emit only the top N candidates after sorting")
    parser.add_argument("--source-label", default=None, help="stable description of the triage inputs for the digest header")
    args = parser.parse_args()
    if args.max_items is not None and args.max_items < 1:
        parser.error("--max-items must be positive")

    all_candidates: list[Candidate] = []
    for path in args.input:
        if not path.exists():
            raise SystemExit(f"input not found: {path}")
        all_candidates.extend(parse_candidates(path))

    if args.decision == "all":
        selected = all_candidates
    else:
        selected = [candidate for candidate in all_candidates if candidate.decision == args.decision]
    if not selected:
        raise SystemExit(f"no candidates matched decision filter: {args.decision}")

    args.outfile.parent.mkdir(parents=True, exist_ok=True)
    shown = min(len(selected), args.max_items) if args.max_items is not None else len(selected)
    args.outfile.write_text(
        render(selected, args.input, args.decision, args.max_items, args.source_label),
        encoding="utf-8",
    )
    print(f"wrote {args.outfile}: {shown} candidates shown; {len(selected)} matched filter")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
