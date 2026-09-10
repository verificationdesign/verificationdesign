#!/usr/bin/env python3
"""Render a verification plan from a valid applicability record."""
import sys
sys.dont_write_bytecode = True
from load_catalog import cli_main, emit, load_catalog, parser, read_record, resolve_output, write_text
from validate_judgments import validate, counts
from render_fields import header, unavailable, Sources


def render(record, catalog, meta):
    sources = Sources()
    lines = header("Verification plan", record, catalog, meta)
    plan = record["plan"]
    catalog_by_id = {c["id"]: c for c in catalog["cards"]}
    plan_lines = ["## Design", "", plan["design"], ""]
    if "source" in plan:
        plan_lines += ["Source: " + plan["source"], ""]
    plan_lines += ["## Verification requirements", ""]
    for requirement in plan["requirements"]:
        citations = [sources.card(catalog_by_id[cid]) for cid in requirement["patterns"]]
        plan_lines += [f'### {requirement["id"]}: {requirement["statement"]}', "",
                       requirement["check"], "", "Patterns: " + (", ".join(citations) or "none"), ""]
    # The shared header includes assumptions and measurements; keep their formatter intact.
    start = lines.index("## Assumptions")
    lines[start:start] = plan_lines
    totals = counts(record)
    lines += ["## Summary", "", f'Apply: {totals["apply"]}; reject: {totals["reject"]}; undecided: {totals["undecided"]}; unknown verdicts: {totals["unknown"]}.', ""]
    lines += [f'Requirements: {len(plan["requirements"])}', ""]
    by_id = {c["id"]: c for c in record["cards"]}
    lines += ["Operator decisions:", ""]
    undecided = [c for c in catalog["cards"] if by_id[c["id"]]["decision"] == "undecided"]
    for card in undecided:
        unknowns = [c["condition"] for g in ("use_when", "do_not_use_when") for c in by_id[card["id"]][g] if c["verdict"] == "unknown"]
        lines += [f'- {card["title"]}: ' + "; ".join(unknowns)]
        if "resolution" in by_id[card["id"]]:
            lines[-1] += f' Resolution recorded {by_id[card["id"]]["resolution"]["date"]}.'
    if not undecided:
        lines += ["None."]
    lines.append("")
    if "priority" in record:
        titles = {c["id"]: c["title"] for c in catalog["cards"]}
        lines += ["Recommended order:", ""] + [f'{i}. {titles[cid]}' for i, cid in enumerate(record["priority"], 1)]
        if not record["priority"]:
            lines += ["None."]
        lines.append("")
    lines += ["## Workflow characterization", ""]
    workflow = record["workflow"]
    for key, title in (("generated", "Generated"), ("generator", "Generator"), ("completion_signal", "Completion signal")):
        lines += [f'{title}: {workflow[key]}', ""]
    lines += ["Self-review points:", ""] + (["- " + p for p in workflow["self_review_points"]] or ["None recorded."]) + [""]
    by_id = {c["id"]: c for c in record["cards"]}
    for heading, selection in (("Patterns applied", "apply"), ("Patterns rejected", "reject")):
        lines += ["## " + heading, ""]
        selected = [c for c in catalog["cards"] if by_id[c["id"]]["decision"] == selection]
        if not selected:
            lines += ["None.", ""]
        for card in selected:
            judgment = by_id[card["id"]]
            lines += ["### " + card["title"], "", sources.card(card), "", judgment["reason"], ""]
            if selection == "apply":
                serves = [r["id"] for r in plan["requirements"] if card["id"] in r["patterns"]]
                lines += ["Decision: apply", "", "Serves: " + ", ".join(serves), ""]
                conditions = [("use_when", c) for c in judgment["use_when"] if c["verdict"] == "holds"]
            else:
                conditions = [("do_not_use_when", c) for c in judgment["do_not_use_when"] if c["verdict"] == "holds"]
                if not conditions:
                    conditions = [("use_when", c) for c in judgment["use_when"]]
            for group, condition in conditions:
                lines += [f'- {group}: {condition["condition"]} ({condition["verdict"]}). {"Reason" if condition["verdict"] == "unknown" else "Evidence"}: {condition["evidence"]}']
            lines.append("")
            if selection == "apply":
                lines += ["Observable signals:", ""] + ["- " + s for s in card["observable_signal"]]
                lines += ["", "Determinism move: " + card["determinism_move"], ""]
            if "instantiation" in judgment:
                if selection != "apply":
                    lines += ["Determinism move: " + card["determinism_move"], ""]
                lines += ["Instantiation: " + judgment["instantiation"], ""]
    lines += ["## Not verified", ""]
    uncertain = False
    for card in catalog["cards"]:
        judgment = by_id[card["id"]]
        unknowns = [(group, c) for group in ("use_when", "do_not_use_when") for c in judgment[group] if c["verdict"] == "unknown"]
        if judgment["decision"] == "undecided" or unknowns:
            uncertain = True
            lines += ["### " + card["title"], "", sources.card(card), "", "Decision: " + judgment["decision"], ""]
            lines += [f'- {group}: {c["condition"].rstrip(".")}. Reason: {c["evidence"] or "Not recorded."}' for group, c in unknowns]
            lines.append("")
            if "resolution" in judgment:
                resolution = judgment["resolution"]
                line = f'Resolution ({resolution["date"]}): {resolution["observation"]} Evidence: {resolution["evidence"]}'
                if isinstance(resolution["measurement"], str):
                    line += " Measurement: " + resolution["measurement"]
                lines += [line, ""]
            if judgment["decision"] == "undecided" and "instantiation" in judgment:
                lines += ["Determinism move: " + card["determinism_move"], "",
                          "Instantiation: " + judgment["instantiation"], ""]
    if not uncertain:
        lines += ["None in the judgment record.", ""]
    lines += unavailable(record)
    lines += sources.render(catalog["revision"])
    return "\n".join(lines)


def main():
    p = parser(__doc__, "python3 scripts/render_plan.py record.json --output plan.md")
    p.add_argument("record", help="JSON judgment record")
    p.add_argument("--output", default="-", metavar="FILE|-", help="markdown file; - emits a JSON text envelope")
    args = p.parse_args()
    resolve_output(args.output, args.record)
    record = read_record(args.record)
    catalog, meta = load_catalog()
    errors = validate(record, catalog, meta)
    if errors:
        emit(errors)
        return 3
    write_text(render(record, catalog, meta), args.output)
    return 0


if __name__ == "__main__":
    sys.exit(cli_main(main))
