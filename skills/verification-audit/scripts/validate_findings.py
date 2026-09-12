#!/usr/bin/env python3
"""Validate evidence and coverage in a verification findings record."""
from pathlib import Path
import re
import sys
sys.dont_write_bytecode = True
from load_catalog import ROOT, SnapshotError, cli_main, emit, load_catalog, parser, read_record

from record_fields import validate_common

STATUSES = ("defect", "sound", "not-applicable", "not-checked", "insufficient-evidence", "out-of-scope")


def nonempty(value):
    return isinstance(value, str) and bool(value.strip())


def checklist(path=None):
    rows, principle = [], None
    path = Path(path) if path else ROOT / "references" / "principles-checklist.md"
    for line in path.read_text(encoding="utf-8").splitlines():
        heading = re.fullmatch(r"## Principle ([1-9])", line)
        if heading:
            principle = int(heading[1])
        elif line.startswith("- "):
            if principle is None:
                raise SnapshotError("checklist question lacks principle")
            rows.append((principle, line[2:]))
    if any(sum(p == n for p, _ in rows) < 2 for n in range(1, 10)) or len(set(q for _, q in rows)) != len(rows):
        raise SnapshotError("checklist needs unique questions, at least two per principle")
    return rows


def validate(record, catalog=None, questions=None, meta=None):
    if catalog is None or meta is None:
        loaded_catalog, loaded_meta = load_catalog()
        catalog, meta = catalog or loaded_catalog, meta or loaded_meta
    questions = checklist() if questions is None else questions
    errors = []
    def fail(index, rule, message):
        errors.append({"card": None, "check": index, "rule": rule, "message": message})
    if not isinstance(record, dict):
        fail(None, "structure", "record must be an object")
        return errors
    validate_common(record, fail, meta)
    for key in ("corpus_revision", "artifact", "scope"):
        if not nonempty(record.get(key)):
            fail(None, "structure", key + " must be a non-empty string")
    if record.get("corpus_revision") != catalog["revision"]:
        fail(None, "structure", "corpus_revision must equal the snapshot revision")
    if isinstance(record.get("scope"), str) and len(record["scope"].splitlines()) != 1:
        fail(None, "structure", "scope must be one line")
    checks = record.get("checks")
    if not isinstance(checks, list):
        fail(None, "structure", "checks must be a list")
        return errors
    failures = {f["failure"] for f in catalog["failures"]}
    mapped = {f["failure"]: set(f["cards"]) for f in catalog["failures"]}
    card_ids = {c["id"] for c in catalog["cards"]}
    known = dict((q, p) for p, q in questions)
    seen = []
    for i, check in enumerate(checks):
        if not isinstance(check, dict):
            fail(i, "structure", "check must be an object")
            continue
        principle, question = check.get("principle"), check.get("question")
        outside = check.get("status") == "out-of-scope"
        valid_principle = (type(principle) is int and principle in range(1, 10)) or (outside and principle is None)
        if not valid_principle or not nonempty(question):
            fail(i, "structure", "principle must be 1 to 9 and question must be non-empty")
            continue
        if "free" in check and type(check["free"]) is not bool:
            fail(i, "structure", "free must be a boolean")
        if check.get("free") is True:
            if question in known or check.get("status") not in ("defect", "out-of-scope"):
                fail(i, "coverage", "free entries must be additional defects or out-of-scope observations with their own question")
        else:
            if outside:
                fail(i, "coverage", "out-of-scope requires free: true and an original question")
            seen.append(question)
            if known.get(question) != principle:
                fail(i, "coverage", "question must match the checklist and its principle verbatim")
        status = check.get("status")
        if not isinstance(status, str) or status not in STATUSES:
            fail(i, "status", "unsupported status")
        if not nonempty(check.get("evidence")):
            fail(i, "evidence", "every status requires evidence or a reason stating what is missing")
        if status == "defect":
            failure = check.get("failure")
            if not isinstance(failure, str) or failure not in failures | {"unmapped"}:
                fail(i, "failure", "defects require a catalog failure string or unmapped")
            if failure == "unmapped" and not nonempty(check.get("failure_note")):
                fail(i, "failure", "unmapped defects require failure_note")
            if check.get("severity") not in ("high", "medium", "low"):
                fail(i, "severity", "defects require high, medium or low severity")
        else:
            if "severity" not in check or check["severity"] is not None:
                fail(i, "severity", "non-defect severity must be null")
            if status in ("not-applicable", "out-of-scope"):
                if check.get("failure") is not None or check.get("failure_note", ""):
                    fail(i, "failure", "this status has no failure or failure note")
                if "cards" in check or "routed" in check:
                    fail(i, "routing", "this status has no routing")
        if "failure_note" in check and not isinstance(check["failure_note"], str):
            fail(i, "failure", "failure_note must be a string")
        if "related_cards" in check:
            related = check["related_cards"]
            if status != "defect":
                fail(i, "routing", "related_cards is allowed only on defects")
            elif (not isinstance(related, list) or not all(isinstance(x, str) for x in related)
                  or len(set(related)) != len(related) or not set(related) <= card_ids):
                fail(i, "routing", "related_cards must list unique catalog card ids")
            elif (isinstance(check.get("failure"), str) and check["failure"] in mapped
                  and not set(related) <= mapped[check["failure"]]):
                fail(i, "routing", "related_cards on a mapped defect must be drawn from that failure's candidate cards")
    for _, question in questions:
        if seen.count(question) != 1:
            fail(None, "coverage", "checklist question must appear exactly once: " + question)
    return errors


def counts(record):
    checks = record["checks"]
    return {"checks": len(checks), "defects": sum(c["status"] == "defect" for c in checks),
            "statuses": {s: sum(c["status"] == s for c in checks) for s in STATUSES},
            "severity": {s: sum(c["status"] == "defect" and c["severity"] == s for c in checks)
                         for s in ("high", "medium", "low")}}


def main():
    p = parser(__doc__, "python3 scripts/validate_findings.py record.json")
    p.add_argument("record", help="JSON findings record")
    args = p.parse_args()
    record = read_record(args.record)
    catalog, meta = load_catalog()
    errors = validate(record, catalog, meta=meta)
    if errors:
        emit(errors)
        print("findings validation failed", file=sys.stderr)
        return 3
    emit(dict(valid=True, **counts(record)))
    return 0


if __name__ == "__main__":
    sys.exit(cli_main(main))
