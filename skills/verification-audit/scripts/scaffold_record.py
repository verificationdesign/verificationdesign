#!/usr/bin/env python3
"""Scaffold an unfilled record from packaged fields without making judgments."""
import sys
sys.dont_write_bytecode = True
from load_catalog import cli_main, emit, load_catalog, parser, resolve_output, skill_pins, write_file
import json
from pathlib import Path
from validate_findings import checklist


def scaffold(artifact, scope):
    catalog, meta = load_catalog()
    record = dict(corpus_revision=catalog["revision"], skill=skill_pins(meta), artifact=artifact, scope=scope,
                  models=dict(generator="", verifier=""), assumptions=[])
    record["checks"] = [dict(principle=p, question=q, status="", evidence="", failure=None,
                             failure_note="", severity=None) for p, q in checklist()]
    return record


def main():
    p = parser(__doc__, "python3 scripts/scaffold_record.py --artifact project --scope checks --output record.json")
    p.add_argument("--artifact", required=True)
    p.add_argument("--scope", required=True)
    p.add_argument("--output", required=True, metavar="FILE|-", help="JSON record destination; stdout includes record and counts in one envelope")
    args = p.parse_args()
    resolve_output(args.output, args.artifact)
    record = scaffold(args.artifact, args.scope)
    counts = {"checks": len(record["checks"])}
    if args.output == "-":
        emit(dict(record=record, counts=counts))
    else:
        write_file(args.output, json.dumps(record, indent=2, ensure_ascii=False) + "\n")
        emit(dict(output=args.output, counts=counts))
    return 0


if __name__ == "__main__":
    sys.exit(cli_main(main))
