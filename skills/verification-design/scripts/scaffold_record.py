#!/usr/bin/env python3
"""Scaffold an unfilled record from packaged fields without making judgments."""
import sys
sys.dont_write_bytecode = True
from load_catalog import cli_main, emit, load_catalog, parser, resolve_output, skill_pins, write_file
import json
from pathlib import Path



def scaffold(artifact, scope):
    catalog, meta = load_catalog()
    record = dict(corpus_revision=catalog["revision"], skill=skill_pins(meta), artifact=artifact, scope=scope,
                  models=dict(generator="", verifier=""),
                  assumptions=[{"topic": "verification-path", "statement": ""}])
    record["plan"] = dict(design="", requirements=[])
    record["workflow"] = dict(generated="", generator="", completion_signal="", self_review_points=[])
    record["cards"] = [dict(id=c["id"], decision="", reason="", **{
        group: [dict(condition=text, verdict="", evidence="") for text in c[group]]
        for group in ("use_when", "do_not_use_when")}) for c in catalog["cards"]]
    return record


def main():
    p = parser(__doc__, "python3 scripts/scaffold_record.py --artifact project --scope checks --output record.json")
    p.add_argument("--artifact", required=True)
    p.add_argument("--scope", required=True)
    p.add_argument("--output", required=True, metavar="FILE|-", help="JSON record destination; stdout includes record and counts in one envelope")
    args = p.parse_args()
    resolve_output(args.output, args.artifact)
    record = scaffold(args.artifact, args.scope)
    counts = {"cards": len(record["cards"]), "conditions": sum(len(c[g]) for c in record["cards"] for g in ("use_when", "do_not_use_when"))}
    if args.output == "-":
        emit(dict(record=record, counts=counts))
    else:
        write_file(args.output, json.dumps(record, indent=2, ensure_ascii=False) + "\n")
        emit(dict(output=args.output, counts=counts))
    return 0


if __name__ == "__main__":
    sys.exit(cli_main(main))
