#!/usr/bin/env python3
"""Card-code runner: extract each card's Pattern code block and execute it.

Why this exists: the 2026-06-07 cold-review adjudication found that several
Pattern blocks do not run as pasted (undefined names), run but assert nothing,
or hide their assertions inside an uncalled `def test_` so a plain run executes
none of them. This runner is the mechanical gate for runnability and for "an
assertion actually executes."

Scope and contract:
- Targets ONLY the code under the `### Pattern:` subsection of
  `## Pattern / Antipattern`. The Antipattern block is frequently a synthesized
  illustrative shape with undefined names by design, so it is not run here.
- Execution mode:
  - if the block defines `def test_...`, the assertions live in test functions;
    run under pytest so they execute. "No tests collected" is a failure: the
    assertions never run.
  - otherwise run as a module; module-level asserts execute directly.
- A Pattern block with no assertion and no test fails: there is nothing
  load-bearing to execute (this is the constitution / executable-analog /
  state-baseline shape the review flagged).
- A card whose Pattern subsection has no python block is SKIP (empty by design
  under no-forced-fill, e.g. cross-family), not a failure.
- A missing third-party import (e.g. pydantic) is reported as DEP, distinct from
  a code defect, but still counts against the gate since the block does not run
  as pasted in this environment.

Card Pattern code targets Python 3.10+ (class-level `X | None` unions appear in
several cards). Default interpreter is python3.13 resolved from PATH; override
with CARD_CODE_PYTHON. Exit status: 0 only if every Pattern block is PASS or
SKIP.

This does NOT judge whether a passing assertion is load-bearing; that is a
review step. It checks that the block runs and that an assertion executes.
"""
from __future__ import annotations

import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

CARDS_DIR = Path(__file__).resolve().parent.parent / "cards"
INTERPRETER = os.environ.get("CARD_CODE_PYTHON", "python3.13")
TIMEOUT_SECONDS = 60

HEADING_RE = re.compile(r"^(#{2,6})\s+(.*)$")
PY_FENCE_RE = re.compile(r"```python\n(.*?)```", re.DOTALL)
DEF_TEST_RE = re.compile(r"^\s*def test_", re.MULTILINE)
ASSERT_RE = re.compile(r"^\s*assert\b", re.MULTILINE)
MODNOTFOUND_RE = re.compile(r"ModuleNotFoundError: No module named '([^']+)'")


def extract_pattern_code(card_text: str) -> str | None:
    """Return concatenated python code under the `### Pattern:` subsection.

    Returns None when no Pattern subsection python block exists (empty by design).
    """
    lines = card_text.splitlines(keepends=True)
    pattern_start = None
    pattern_level = None
    for i, line in enumerate(lines):
        m = HEADING_RE.match(line)
        if not m:
            continue
        hashes, title = m.group(1), m.group(2)
        low = title.lower()
        # Subsection (### or deeper) named Pattern, not Antipattern, not the
        # "## Pattern / Antipattern" parent.
        if len(hashes) >= 3 and "pattern" in low and "antipattern" not in low and "/" not in title:
            pattern_start = i
            pattern_level = len(hashes)
            break
    if pattern_start is None:
        return None
    body_lines = []
    for line in lines[pattern_start + 1:]:
        m = HEADING_RE.match(line)
        if m and len(m.group(1)) <= pattern_level:
            break
        body_lines.append(line)
    blocks = PY_FENCE_RE.findall("".join(body_lines))
    if not blocks:
        return None
    return "\n\n".join(blocks)


def run_block(code: str) -> tuple[str, str]:
    """Execute the Pattern block; return (status, detail).

    status in {PASS, FAIL, DEP}. DEP detail names the missing module.
    """
    has_test = bool(DEF_TEST_RE.search(code))
    has_assert = bool(ASSERT_RE.search(code))

    if not has_test and not has_assert:
        return "FAIL", "no assertion and no test: nothing load-bearing executes"

    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as fh:
        fh.write(code)
        tmp = fh.name
    try:
        if has_test:
            cmd = [INTERPRETER, "-m", "pytest", tmp, "-q", "-p", "no:cacheprovider"]
        else:
            cmd = [INTERPRETER, tmp]
        try:
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=TIMEOUT_SECONDS)
        except subprocess.TimeoutExpired:
            return "FAIL", f"TIMEOUT after {TIMEOUT_SECONDS}s"
        except FileNotFoundError:
            return "FAIL", f"interpreter not found: {INTERPRETER} (set CARD_CODE_PYTHON)"
    finally:
        os.unlink(tmp)

    combined = (proc.stderr or "") + (proc.stdout or "")
    dep = MODNOTFOUND_RE.search(combined)
    if dep:
        return "DEP", f"needs third-party module '{dep.group(1)}' (install to test fully)"

    if has_test:
        if proc.returncode == 0:
            return "PASS", "pytest: tests passed"
        if proc.returncode == 5:
            return "FAIL", "pytest collected no tests: assertions never execute"
        tail = combined.strip().splitlines()
        return "FAIL", "\n".join(tail[-4:]) if tail else f"pytest exit {proc.returncode}"

    if proc.returncode == 0:
        return "PASS", "module runs; module-level assertion executed"
    tail = combined.strip().splitlines()
    return "FAIL", "\n".join(tail[-4:]) if tail else f"exit {proc.returncode}"


def main(argv: list[str]) -> int:
    if argv:
        cards = []
        for name in argv:
            p = Path(name)
            if not p.exists():
                p = CARDS_DIR / name
            if not p.exists() and not name.endswith(".md"):
                p = CARDS_DIR / f"{name}.md"
            cards.append(p)
    else:
        cards = sorted(CARDS_DIR.glob("*.md"))

    counts = {"PASS": 0, "FAIL": 0, "DEP": 0, "SKIP": 0}
    print(f"Card-code runner: interpreter {INTERPRETER}\n")
    for card in cards:
        name = card.name
        code = extract_pattern_code(card.read_text())
        if code is None:
            print(f"  [SKIP] {name}: no Pattern code block (empty by design)")
            counts["SKIP"] += 1
            continue
        status, detail = run_block(code)
        counts[status] += 1
        head, *rest = detail.splitlines()
        print(f"  [{status}] {name}: {head}")
        for ln in rest:
            print(f"         {ln}")

    print(f"\nPattern blocks: {counts['PASS']} pass, {counts['FAIL']} fail, "
          f"{counts['DEP']} dep-missing, {counts['SKIP']} skip "
          f"({sum(counts.values())} cards)")
    return 1 if (counts["FAIL"] or counts["DEP"]) else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
