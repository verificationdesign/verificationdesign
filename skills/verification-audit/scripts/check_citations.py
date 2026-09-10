#!/usr/bin/env python3
"""Check citation file existence and line bounds only, never evidence meaning."""
import sys
sys.dont_write_bytecode = True
from load_catalog import cli_main, emit, parser, read_record, resolve_output
from pathlib import Path
import re

FIELDS = {"evidence", "reason", "statement", "note", "instantiation"}
CITATION = re.compile(r"(?<![\w/.:~-])([\w./~@+-]+):(\d+)(?:-(\d+))?(?![\w-])")


def strings(value, entry="$", field=None):
    if isinstance(value, dict):
        for key, child in value.items():
            yield from strings(child, entry + "." + key, key)
    elif isinstance(value, list):
        for i, child in enumerate(value):
            yield from strings(child, f"{entry}[{i}]", field)
    elif field in FIELDS and isinstance(value, str):
        yield entry, value


def check(record, roots):
    counts = dict(found=0, missing=0, **{"out-of-bounds": 0})
    failures, seen, sizes = [], set(), {}
    resolved, entries = [], {}
    for entry, text in strings(record):
        for match in CITATION.finditer(text):
            path, start, end = match.groups()
            if not ("." in path or "/" in path):
                continue
            citation = match.group()
            entries.setdefault(citation, set()).add(entry)
            if citation in seen:
                continue
            seen.add(citation)
            file = Path(path)
            root = None
            if not file.is_absolute():
                root = next((r for r in roots if (Path(r) / file).is_file()), None)
                if root is None:
                    counts["missing"] += 1
                    failures.append(dict(citation=citation, entry=entry, status="missing"))
                    continue
                file = Path(root) / file
            if file not in sizes:
                try:
                    with file.open("rb") as stream:
                        sizes[file] = sum(1 for _ in stream)
                except (FileNotFoundError, NotADirectoryError, IsADirectoryError):
                    sizes[file] = None
            first, last = int(start), int(end or start)
            status = "missing" if sizes[file] is None else (
                "out-of-bounds" if first < 1 or last < first or last > sizes[file] else "found")
            counts[status] += 1
            if status != "found":
                failures.append(dict(citation=citation, entry=entry, status=status))
            else:
                resolved.append(dict(citation=citation, root=root))
    repeated = [dict(citation=c, entries=len(paths)) for c, paths in entries.items() if len(paths) >= 3]
    repeated.sort(key=lambda item: (-item["entries"], item["citation"]))
    return dict(counts=counts, citations=failures, roots=roots, resolved=resolved, repeated=repeated)


def main():
    p = parser(__doc__ + " Repeated citations are reported for the operator's eye and are not a failure, because one line can legitimately bear on several conditions.", "python3 scripts/check_citations.py record.json --root /path/to/project --root /path/to/evidence")
    p.add_argument("record", help="JSON record; only evidence, reason, statement, note and instantiation strings are scanned")
    p.add_argument("--root", action="append", required=True, help="repeat for several roots; first file match wins, so order roots deliberately")
    p.add_argument("--output", default="-", metavar="FILE|-")
    args = p.parse_args()
    resolve_output(args.output, args.record)
    result = check(read_record(args.record), args.root)
    emit(result, args.output)
    return 3 if result["citations"] else 0


if __name__ == "__main__":
    sys.exit(cli_main(main))
