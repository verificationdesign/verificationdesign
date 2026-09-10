#!/usr/bin/env python3
"""Validate recorded applicability judgments against the pinned catalog."""
import sys
sys.dont_write_bytecode = True
from load_catalog import cli_main, emit, load_catalog, parser, read_record

from record_fields import validate_common
import datetime
import re

VERDICTS = {"holds", "does-not-hold", "unknown"}


def nonempty(value):
    return isinstance(value, str) and bool(value.strip())


def decision(use, exclude):
    if "holds" in exclude or all(v == "does-not-hold" for v in use):
        return "reject"
    if "holds" in use and all(v == "does-not-hold" for v in exclude):
        return "apply"
    return "undecided"


def validate_plan(record, fail):
    plan = record.get("plan")
    if not isinstance(plan, dict):
        fail(None, "plan", "plan must be an object")
        return
    if not {"design", "requirements"} <= set(plan) or set(plan) - {"design", "source", "requirements"}:
        fail(None, "plan", "plan requires design and requirements, with only source optional")
    if not nonempty(plan.get("design")):
        fail(None, "plan", "plan.design must be a non-empty string")
    if "source" in plan and not nonempty(plan["source"]):
        fail(None, "plan", "plan.source must be a non-empty string")
    requirements = plan.get("requirements")
    if not isinstance(requirements, list) or not requirements:
        fail(None, "plan", "plan.requirements must be a non-empty list")
        return
    cards = record.get("cards")
    applied = {c["id"] for c in cards if isinstance(c, dict) and isinstance(c.get("id"), str)
               and c.get("decision") == "apply"} if isinstance(cards, list) else set()
    served = set()
    for index, requirement in enumerate(requirements, 1):
        if not isinstance(requirement, dict) or set(requirement) != {"id", "statement", "check", "patterns"}:
            fail(None, "plan", "each requirement needs exactly id, statement, check and patterns")
            continue
        if requirement["id"] != f"V{index}":
            fail(None, "plan", "requirement ids must be contiguous from V1 in list order")
        for key in ("statement", "check"):
            if not nonempty(requirement[key]):
                fail(None, "plan", "requirement " + key + " must be a non-empty string")
        patterns = requirement["patterns"]
        if not isinstance(patterns, list):
            fail(None, "plan", "requirement patterns must be a list of applied card ids")
            continue
        ids = [cid for cid in patterns if isinstance(cid, str)]
        if len(ids) != len(patterns) or any(cid not in applied for cid in ids):
            fail(None, "plan", "requirement patterns must name only applied cards")
        if len(set(ids)) != len(ids):
            fail(None, "plan", "requirement patterns must not contain duplicates")
        served.update(ids)
    for cid in sorted(applied - served):
        fail(cid, "plan", "every applied card must serve at least one requirement")


def validate(record, catalog=None, meta=None):
    if catalog is None or meta is None:
        loaded_catalog, loaded_meta = load_catalog()
        catalog, meta = catalog or loaded_catalog, meta or loaded_meta
    errors = []
    def fail(card, rule, message):
        errors.append({"card": card, "rule": rule, "message": message})
    if not isinstance(record, dict):
        fail(None, "structure", "record must be an object")
        return errors
    validate_common(record, fail, meta, design=True)
    validate_plan(record, fail)
    for key in ("corpus_revision", "artifact", "scope"):
        if not nonempty(record.get(key)):
            fail(None, "structure", key + " must be a non-empty string")
    if record.get("corpus_revision") != catalog["revision"]:
        fail(None, "structure", "corpus_revision must equal the snapshot revision")
    if isinstance(record.get("scope"), str) and len(record["scope"].splitlines()) != 1:
        fail(None, "structure", "scope must be one line")
    workflow = record.get("workflow")
    if not isinstance(workflow, dict):
        fail(None, "structure", "workflow must be an object")
    else:
        for key in ("generated", "generator", "completion_signal"):
            if not nonempty(workflow.get(key)):
                fail(None, "structure", "workflow." + key + " must be a non-empty string")
        points = workflow.get("self_review_points")
        if not isinstance(points, list) or any(not nonempty(p) for p in points):
            fail(None, "structure", "workflow.self_review_points must be a list of non-empty strings")
    cards = record.get("cards")
    if not isinstance(cards, list):
        fail(None, "structure", "cards must be a list")
        return errors
    if "priority" in record:
        priority = record["priority"]
        applied = {c.get("id") for c in cards if isinstance(c, dict) and isinstance(c.get("id"), str) and c.get("decision") == "apply"}
        if not isinstance(priority, list) or any(not isinstance(x, str) or x not in applied for x in priority) or len(set(x for x in priority if isinstance(x, str))) != len(priority):
            fail(None, "priority", "priority must list applied card ids without duplicates")
    for card in cards:
        if not isinstance(card, dict) or not nonempty(card.get("id")):
            fail(None, "structure", "each card needs an id")
            continue
        if "instantiation" in card and not isinstance(card["instantiation"], str):
            fail(card["id"], "instantiation", "instantiation must be a string")
        if "resolution" in card:
            resolution = card["resolution"]
            if card.get("decision") != "undecided":
                fail(card["id"], "resolution", "resolution is allowed only on an undecided card")
            if not isinstance(resolution, dict) or set(resolution) != {"date", "observation", "evidence", "measurement"}:
                fail(card["id"], "resolution", "resolution must be an object with exactly date, observation, evidence and measurement")
            else:
                if (not isinstance(resolution["date"], str)
                        or not nonempty(resolution["observation"])
                        or not nonempty(resolution["evidence"])
                        or not (resolution["measurement"] is None or isinstance(resolution["measurement"], str))):
                    fail(card["id"], "resolution", "resolution requires a string date, non-empty observation and evidence, and string or null measurement")
                if isinstance(resolution["date"], str):
                    try:
                        if not re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", resolution["date"]):
                            raise ValueError
                        datetime.date.fromisoformat(resolution["date"])
                    except ValueError:
                        fail(card["id"], "resolution", "resolution date must be a valid YYYY-MM-DD calendar date")
                measurements = record.get("measurements", [])
                ids = [m.get("id") for m in measurements if isinstance(m, dict)] if isinstance(measurements, list) else []
                if isinstance(resolution["measurement"], str) and resolution["measurement"] not in ids:
                    fail(card["id"], "resolution", "resolution measurement must name an id in measurements")
        if not nonempty(card.get("reason")):
            fail(card["id"], "structure", "reason must be non-empty")
        for group in ("use_when", "do_not_use_when"):
            if not isinstance(card.get(group), list) or any(not isinstance(c, dict) for c in card[group]):
                fail(card["id"], "structure", group + " must be a list of condition objects")
    if errors:
        return errors
    expected_ids = [c["id"] for c in catalog["cards"]]
    ids = [c["id"] for c in cards]
    for cid in sorted(set(expected_ids + ids)):
        if cid not in expected_ids or ids.count(cid) != 1:
            fail(cid, "coverage", "every catalog card must appear exactly once; unknown ids are forbidden")
    if errors:
        return errors
    by_id = {c["id"]: c for c in cards}
    for source in catalog["cards"]:
        card = by_id[source["id"]]
        for group in ("use_when", "do_not_use_when"):
            if [c.get("condition") for c in card[group]] != source[group]:
                fail(card["id"], "conditions", group + " must match every catalog condition verbatim in catalog order")
    if errors:
        return errors
    for card in cards:
        for group in ("use_when", "do_not_use_when"):
            for condition in card[group]:
                verdict = condition.get("verdict")
                if not isinstance(verdict, str) or verdict not in VERDICTS:
                    fail(card["id"], "verdicts", "verdict must be holds, does-not-hold or unknown")
                if not isinstance(condition.get("evidence"), str) or (verdict != "unknown" and not nonempty(condition["evidence"])):
                    fail(card["id"], "verdicts", "non-unknown verdicts require non-empty evidence; evidence must be a string")
    if errors:
        return errors
    for card in cards:
        expected = decision([c["verdict"] for c in card["use_when"]], [c["verdict"] for c in card["do_not_use_when"]])
        if card.get("decision") != expected:
            explanation = {
                "apply": "at least one use_when holds and every exclusion does-not-hold",
                "reject": "an exclusion holds or every use_when does-not-hold",
                "undecided": "unresolved applicability or an unknown exclusion blocks apply",
            }[expected]
            fail(card["id"], "decision-" + expected, "expected " + expected + ": " + explanation)
    return errors


def counts(record):
    return dict(cards=len(record["cards"]), **{
        d: sum(c["decision"] == d for c in record["cards"]) for d in ("apply", "reject", "undecided")},
        unknown=sum(c["verdict"] == "unknown" for card in record["cards"]
                    for group in ("use_when", "do_not_use_when") for c in card[group]))


def main():
    p = parser(__doc__, "python3 scripts/validate_judgments.py record.json")
    p.add_argument("record", help="JSON judgment record")
    args = p.parse_args()
    record = read_record(args.record)
    catalog, meta = load_catalog()
    errors = validate(record, catalog, meta)
    if errors:
        emit(errors)
        print("judgment validation failed", file=sys.stderr)
        return 3
    emit(dict(valid=True, **counts(record)))
    return 0


if __name__ == "__main__":
    sys.exit(cli_main(main))
