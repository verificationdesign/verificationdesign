#!/usr/bin/env python3
"""Render validated, routed findings without generating fix proposals."""
import sys
sys.dont_write_bytecode = True
from load_catalog import cli_main, emit, load_catalog, parser, read_record, resolve_output, write_text
from route_failures import route
from validate_findings import checklist, validate, counts
from render_fields import header, unavailable, Sources
import re


def render(record, catalog, meta):
    sources = Sources()
    lines = header("Verification findings", record, catalog, meta)
    totals = counts(record)
    lines += ["## Summary", "", f'Defects: {totals["defects"]}. ' + "; ".join(f'{s}: {n}' for s, n in totals["severity"].items()) + ".", ""]
    lines += [f'- {s}: {n}' for s, n in totals["statuses"].items()] + ["", "Unmapped defects:", ""]
    unmapped = [c for c in record["checks"] if c["status"] == "defect" and c["failure"] == "unmapped"]
    for check in unmapped:
        lines += ["- " + re.sub(r" \[Principles\]\([^)]+\)", "", check["question"])]
    if not unmapped:
        lines += ["None."]
    lines.append("")
    order = {q: i for i, (_, q) in enumerate(checklist())}
    checks = sorted(record["checks"], key=lambda c: (c["principle"] or 10, order.get(c["question"], len(order)), c["question"]))
    for heading, status in (("Defects", "defect"), ("Checked and sound", "sound"), ("Not applicable", "not-applicable"), ("Not checked", "not-checked"), ("Insufficient evidence", "insufficient-evidence"), ("Observed outside scope", "out-of-scope")):
        lines += ["## " + heading, ""]
        selected = [c for c in checks if c["status"] == status]
        if not selected:
            lines += ["None.", ""]
        for check in selected:
            def principle_ref(match):
                key = "p" + str(check["principle"])
                sources.definitions[key] = match[1]
                return "[Principles][" + key + "]"
            question = re.sub(r"\[Principles\]\(([^)]+)\)", principle_ref, check["question"])
            label = "Evidence" if status in {"sound", "defect"} else "Reason"
            lines += [f'### Principle {check["principle"]}' if check["principle"] else "### Observation", "", question, "", label + ": " + check["evidence"], ""]
            if status == "defect":
                lines += ["Severity: " + check["severity"], "", "Failure: " + check["failure"], ""]
                if check.get("failure_note"):
                    lines += ["Failure note: " + check["failure_note"], ""]
                if not check["cards"]:
                    lines += ["No routed card: outside the six mapped failures; see the failure note above.", ""]
                else:
                    lines += ["- " + sources.card(c) for c in check["cards"]] + [""]
        if status == "insufficient-evidence":
            lines += unavailable(record)
    lines += sources.render(catalog["revision"])
    return "\n".join(lines)


def main():
    p = parser(__doc__, "python3 scripts/render_findings.py routed.json --output findings.md")
    p.add_argument("record", help="routed JSON findings record")
    p.add_argument("--output", default="-", metavar="FILE|-", help="markdown file; - emits a JSON text envelope")
    args = p.parse_args()
    resolve_output(args.output, args.record)
    record = read_record(args.record)
    catalog, meta = load_catalog()
    errors = validate(record, catalog, meta=meta)
    if errors:
        emit(errors)
        return 3
    if route(record, catalog) != record:
        emit([{"card": None, "rule": "routing", "message": "routed record must match the pinned failure map; run route_failures.py"}])
        return 3
    write_text(render(record, catalog, meta), args.output)
    return 0


if __name__ == "__main__":
    sys.exit(cli_main(main))
