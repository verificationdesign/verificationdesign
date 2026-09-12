#!/usr/bin/env python3
"""Create a compact reading digest from triage notes.

The digest is a consumption layer, not a review layer. It reads already-written
triage notes, keeps the model suggestion visible, and applies only lightweight
heuristics for sorting and evidence-type hints.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from research_tools import records
from research_tools.profile import Profile, load_profile


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


def parse_candidates(path: Path) -> list[Candidate]:
    try:
        document = records.parse_triage(path.read_text(encoding="utf-8"))
    except records.RecordError as error:
        raise SystemExit(f"{path}: {error}") from error
    # Records keep field values byte-exact; the digest compares and looks up
    # semantic values, so strip them the way the verifier and old script did.
    return [Candidate(
        title=item.title.strip(), source=item.source.strip(), label=item.initial_label.strip(),
        decision=item.decision.strip(), abstract=one_line(item.abstract),
        why=one_line(item.why), key_claims=bullets(item.key_findings),
        human_checks=bullets(item.human_checks),
        credibility_flags=bullets(item.credibility_flags), ordinal=index,
    ) for index, item in enumerate(document.candidates)]


def candidate_text(candidate: Candidate) -> str:
    return " ".join([candidate.title, candidate.abstract, " ".join(candidate.key_claims)]).lower()


def evidence_type(candidate: Candidate, tables: dict) -> str:
    text = candidate_text(candidate)
    for entry in tables["evidence_types"]:
        if any(term in text for term in entry["terms"]):
            return entry["label"]
    return tables["evidence_fallback"]


def doc_impact(candidate: Candidate, tables: dict) -> str:
    return tables["doc_impact"].get(candidate.label, tables["doc_impact_fallback"])


def read_priority(candidate: Candidate, tables: dict) -> int:
    text = candidate_text(candidate)
    for priority, terms in enumerate(tables["read_priority"], start=1):
        if any(term in text for term in terms):
            return priority
    return tables["read_priority_fallback"]


def topic_cluster(candidate: Candidate, tables: dict) -> str:
    text = candidate_text(candidate)
    for entry in tables["topic_clusters"]:
        if any(term in text for term in entry["terms"]):
            return entry["label"]
    return tables["topic_fallback"]


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
    tables: dict,
) -> str:
    ranked = sorted(candidates, key=lambda item: (read_priority(item, tables), item.ordinal))
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
        priority = read_priority(candidate, tables)
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
                f"- Topic cluster: {topic_cluster(candidate, tables)}",
                f"- Potential doc impact: {doc_impact(candidate, tables)}",
                f"- Evidence type: {evidence_type(candidate, tables)}",
                f"- Why read this: {first_sentence(candidate.why)}",
                f"- Abstract gist: {first_sentence(candidate.abstract)}",
                f"- Key data or claims: {'; '.join(claims)}",
                f"- Credibility flags: {credibility_line(candidate)}",
                f"- Human question: {human_question}",
                "",
            ]
        )
    return "\n".join(lines).rstrip() + "\n"


def register(subparsers):
    parser = subparsers.add_parser("digest", description="Create a compact digest from triage notes.")
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
    parser.add_argument("--profile", type=Path,
                        default=Path(__file__).resolve().parents[1] / "research/scouts/config.json")
    parser.set_defaults(run=main, parser=parser)


def main(args) -> int:
    if args.max_items is not None and args.max_items < 1:
        args.parser.error("--max-items must be positive")
    try:
        profile = load_profile(args.profile)
    except (ValueError, OSError) as error:
        raise SystemExit(f"{args.profile}: {error}") from error
    return run(args, profile)


def run(args, profile: Profile) -> int:
    tables = profile.digest_heuristics
    if tables is None:
        raise SystemExit("digest requires digest_heuristics in the profile")
    if args.max_items is not None and args.max_items < 1:
        args.parser.error("--max-items must be positive")

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
        render(selected, args.input, args.decision, args.max_items, args.source_label, tables),
        encoding="utf-8",
    )
    print(f"wrote {args.outfile}: {shown} candidates shown; {len(selected)} matched filter")
    return 0

