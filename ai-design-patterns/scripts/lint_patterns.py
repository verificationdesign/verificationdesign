#!/usr/bin/env python3
"""Pattern card linter for the AI Design Patterns book.

Loads `constitution.json` (editorial standards as data) and runs each rule
against the cards under `./cards/`. Prints observed values for every check,
not only failures, matching the repo's `scripts/verify.py` discipline.
Exits non-zero on any failure.

The constitution is data; this script is the verifier. See `cards/constitution.md`
for the pattern this artifact implements.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class CheckResult:
    name: str
    passed: bool
    observed: str
    detail: list[str] = field(default_factory=list)


def load_constitution(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def strip_code_blocks(content: str) -> str:
    """Return content with fenced code blocks blanked, preserving line numbers.

    Used to scope prose-only checks (vague terms, empirical claims) so that
    antipattern code blocks may intentionally include vague language without
    triggering the linter.
    """
    lines = content.split("\n")
    result: list[str] = []
    in_block = False
    for line in lines:
        if line.lstrip().startswith("```"):
            in_block = not in_block
            result.append("")
            continue
        if in_block:
            result.append("")
            continue
        result.append(line)
    return "\n".join(result)


def check_forbidden_characters(content: str, rule: dict) -> CheckResult:
    counts: dict[str, int] = {}
    locations: dict[str, list[int]] = {}
    for item in rule["items"]:
        char = chr(item["codepoint"])
        line_hits: list[int] = []
        for match in re.finditer(re.escape(char), content):
            line_hits.append(content.count("\n", 0, match.start()) + 1)
        counts[item["name"]] = len(line_hits)
        locations[item["name"]] = line_hits
    total = sum(counts.values())
    breakdown = ", ".join(f"{name}: {count}" for name, count in counts.items())
    detail: list[str] = []
    for name, lines_at in locations.items():
        if not lines_at:
            continue
        preview = lines_at[:10]
        suffix = f" (+ {len(lines_at) - 10} more)" if len(lines_at) > 10 else ""
        detail.append(f"{name} at lines: {preview}{suffix}")
    return CheckResult(
        name="Forbidden characters",
        passed=(total == 0),
        observed=f"{total} found ({breakdown})",
        detail=detail,
    )


def check_required_sections(content: str, sections: list[str]) -> CheckResult:
    found: list[str] = []
    missing: list[str] = []
    for section in sections:
        pattern = rf"^#{{2,3}}\s+{re.escape(section)}\b"
        (found if re.search(pattern, content, re.MULTILINE) else missing).append(section)
    return CheckResult(
        name="Required sections",
        passed=(len(missing) == 0),
        observed=f"{len(found)} of {len(sections)} present",
        detail=[f"missing: {s}" for s in missing],
    )


def check_determinism_move(content: str, valid_sources: list[str]) -> CheckResult:
    section_match = re.search(
        r"^#{2,3}\s+Determinism Move\s*\n(.*?)(?=\n#{2,3}\s|\Z)",
        content,
        re.MULTILINE | re.DOTALL,
    )
    if not section_match:
        return CheckResult(
            name="Determinism Move sources",
            passed=False,
            observed="section not found",
        )
    body = section_match.group(1)
    found = [src for src in valid_sources if re.search(rf"`{re.escape(src)}`", body)]
    return CheckResult(
        name="Determinism Move sources",
        passed=(len(found) > 0),
        observed=f"{len(found)} valid source(s) named: {found if found else '(none)'}",
    )


def check_vague_terms(content: str, terms: list[str]) -> CheckResult:
    hits: list[str] = []
    for term in terms:
        for match in re.finditer(rf"\b{re.escape(term)}\b", content, re.IGNORECASE):
            line_no = content.count("\n", 0, match.start()) + 1
            hits.append(f"line {line_no}: '{term}'")
    return CheckResult(
        name="Vague terms",
        passed=(len(hits) == 0),
        observed=f"{len(hits)} found",
        detail=hits[:10] + (["..."] if len(hits) > 10 else []),
    )


def check_empirical_claims(
    content: str,
    verbs: list[str],
    citation_patterns: list[str],
) -> CheckResult:
    verb_re = re.compile(rf"\b({'|'.join(verbs)})\b", re.IGNORECASE)
    citation_re = re.compile("|".join(citation_patterns))
    digit_re = re.compile(r"\d")
    sentences = re.split(r"(?<=[.!?])\s+", content)
    hits: list[str] = []
    checked = 0
    for sentence in sentences:
        if not (verb_re.search(sentence) and digit_re.search(sentence)):
            continue
        checked += 1
        if citation_re.search(sentence):
            continue
        preview = sentence.strip().replace("\n", " ")
        if len(preview) > 90:
            preview = preview[:87] + "..."
        hits.append(preview)
    return CheckResult(
        name="Empirical claims with citation",
        passed=(len(hits) == 0),
        observed=f"{len(hits)} uncited, {checked} verb+number sentences checked",
        detail=[f"'{h}'" for h in hits[:10]] + (["..."] if len(hits) > 10 else []),
    )


def check_code_block_languages(content: str) -> CheckResult:
    fences = [match.group(1) for match in re.finditer(r"^```([^\n]*)$", content, re.MULTILINE)]
    blocks_opened = 0
    untagged: list[int] = []
    in_block = False
    block_index = 0
    for tag in fences:
        if in_block:
            in_block = False
        else:
            in_block = True
            blocks_opened += 1
            block_index += 1
            if not tag.strip():
                untagged.append(block_index)
    return CheckResult(
        name="Code block languages",
        passed=(len(untagged) == 0),
        observed=f"{blocks_opened} block(s), {len(untagged)} untagged",
        detail=[f"block #{n} missing language tag" for n in untagged],
    )


def lint_file(path: Path, constitution: dict) -> list[CheckResult]:
    content = path.read_text(encoding="utf-8")
    prose = strip_code_blocks(content)
    return [
        check_forbidden_characters(content, constitution["forbidden_characters"]),
        check_required_sections(content, constitution["required_sections"]["sections"]),
        check_determinism_move(content, constitution["determinism_move"]["valid_sources"]),
        check_vague_terms(prose, constitution["vague_terms"]["terms"]),
        check_empirical_claims(
            prose,
            constitution["empirical_claim_verbs"]["verbs"],
            constitution["citation_patterns"]["regex"],
        ),
        check_code_block_languages(content),
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    script_dir = Path(__file__).resolve().parent
    project_dir = script_dir.parent
    parser.add_argument(
        "--constitution",
        type=Path,
        default=project_dir / "constitution.json",
        help="path to constitution.json (default: ../constitution.json relative to this script)",
    )
    parser.add_argument(
        "--cards",
        type=Path,
        default=project_dir / "cards",
        help="path to cards directory (default: ../cards relative to this script)",
    )
    args = parser.parse_args()

    if not args.constitution.exists():
        print(f"constitution not found: {args.constitution}", file=sys.stderr)
        return 1
    if not args.cards.exists():
        print(f"cards directory not found: {args.cards}", file=sys.stderr)
        return 1

    constitution = load_constitution(args.constitution)
    print(f"Constitution: {args.constitution} (version {constitution.get('version', 'unknown')})")
    print(f"Cards: {args.cards}")
    print()

    files = sorted(args.cards.glob("*.md"))
    if not files:
        print("no card files found", file=sys.stderr)
        return 1

    total_failures = 0
    for path in files:
        print(f"=== {path.name} ===")
        for result in lint_file(path, constitution):
            status = "PASS" if result.passed else "FAIL"
            print(f"  [{status}] {result.name}: {result.observed}")
            for line in result.detail:
                print(f"          {line}")
            if not result.passed:
                total_failures += 1
        print()

    print(f"Total failing checks: {total_failures}")
    return 0 if total_failures == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
