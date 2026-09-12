"""Shared record field validation within this self-contained skill."""
import json
import sys
sys.dont_write_bytecode = True
from load_catalog import emit, skill_pins


def nonempty(value):
    return isinstance(value, str) and bool(value.strip())


def validate_common(record, fail, meta, design=False):
    expected = skill_pins(meta)
    if record.get("skill") != expected:
        fail(None, "skill", "skill must equal the packaged identity emitted by scaffold_record.py: " + json.dumps(expected, sort_keys=True))
    models = record.get("models")
    if not isinstance(models, dict) or set(models) != {"generator", "verifier"} or not all(nonempty(models[k]) for k in models):
        fail(None, "models", "models must name the generator and verifier model families as non-empty strings; use unknown when not recorded")
    assumptions = record.get("assumptions")
    if not isinstance(assumptions, list) or any(
        not isinstance(x, dict) or not nonempty(x.get("topic")) or not nonempty(x.get("statement"))
        for x in assumptions
    ):
        fail(None, "assumptions", "assumptions must list non-empty topic and statement objects")
    elif design and not any(x["topic"] == "verification-path" for x in assumptions):
        fail(None, "assumptions", "design requires a verification-path assumption")
    if "measurements" in record:
        rows = record["measurements"]
        seen = set()
        if not isinstance(rows, list):
            fail(None, "measurements", "measurements must be a list")
        else:
            for row in rows:
                valid = isinstance(row, dict) and nonempty(row.get("id")) and nonempty(row.get("command"))
                if valid:
                    valid = (row["id"] not in seen and isinstance(row.get("env"), dict)
                             and all(isinstance(k, str) and isinstance(v, str) for k, v in row["env"].items())
                             and type(row.get("exit_code")) is int
                             and isinstance(row.get("artifact_revision"), str)
                             and "log" in row and (row["log"] is None or isinstance(row["log"], str))
                             and isinstance(row.get("note"), str)
                             and row.get("kind") in ("inspection", "execution"))
                    seen.add(row["id"])
                if not valid:
                    fail(None, "measurements", "measurement fields must have documented types, kind must be inspection or execution, and ids must be unique")
    if "artifact_identity" in record:
        x = record["artifact_identity"]
        valid = (isinstance(x, dict) and "revision" in x and
                 (x["revision"] is None or isinstance(x["revision"], str)) and isinstance(x.get("files"), list))
        if valid:
            valid = all(isinstance(f, dict) and isinstance(f.get("path"), str) and
                        isinstance(f.get("sha256"), str)
                        for f in x["files"])
        if not valid:
            fail(None, "artifact-identity", "identity requires revision (string or null) and files with string path and sha256")
    if "unavailable_sources" in record:
        rows = record["unavailable_sources"]
        if not isinstance(rows, list) or any(not isinstance(x, dict) or
            set(x) != {"unavailable", "source_url", "reason"} or x.get("unavailable") is not True or
            not nonempty(x.get("source_url")) or not nonempty(x.get("reason")) for x in rows):
            fail(None, "unavailable-sources", "use the unavailable, source_url, reason objects emitted by fetch")
