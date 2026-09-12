#!/usr/bin/env python3
"""Attach the pinned failure map's candidate cards to validated defects. A lookup, not an applicability judgment."""
import copy
import sys
sys.dont_write_bytecode = True
from load_catalog import cli_main, emit, load_catalog, parser, read_record, resolve_output
from validate_findings import validate


def route(record, catalog):
    result = copy.deepcopy(record)
    cards = {c["id"]: c for c in catalog["cards"]}
    failures = {f["failure"]: f["cards"] for f in catalog["failures"]}
    for check in result["checks"]:
        check.pop("cards", None)
        check.pop("routed", None)
        if check["status"] == "defect":
            ids = failures.get(check["failure"], [])
            check["cards"] = [{k: cards[cid][k] for k in ("id", "title", "html_url", "source_url")} for cid in ids]
            check["routed"] = bool(ids)
    return result


def main():
    p = parser(__doc__, "python3 scripts/route_failures.py record.json --output routed.json")
    p.add_argument("record", help="JSON findings record")
    p.add_argument("--output", default="-", metavar="FILE|-", help="routed JSON destination (default stdout)")
    args = p.parse_args()
    resolve_output(args.output, args.record)
    record = read_record(args.record)
    catalog, meta = load_catalog()
    errors = validate(record, catalog, meta=meta)
    if errors:
        emit(errors)
        return 3
    emit(route(record, catalog), args.output)
    return 0


if __name__ == "__main__":
    sys.exit(cli_main(main))
