#!/usr/bin/env python3
"""Verify the packaged catalog and optionally retrieve hash-checked source text."""
import argparse
import hashlib
import http.client
import json
import math
import os
from pathlib import Path
import re
import socket
import sys


def require_python():
    """Refuse unsupported interpreters before loading or writing anything."""
    if sys.version_info < (3, 11):
        found = ".".join(map(str, sys.version_info[:3]))
        print(f"Python {found} found; Python 3.11 or later required", file=sys.stderr)
        raise SystemExit(2)


require_python()

import urllib.error
import urllib.parse
import urllib.request

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parent.parent
BASE_URL = "https://raw.githubusercontent.com"
LIVE_URL = "https://verificationdesign.com/catalog.json"
PIN_KEYS = ("version", "corpus-revision", "corpus-tag", "catalog-sha256", "principles-sha256")
CHECKLIST_KEY = "checklist-sha256"
CHECKLIST_PATH = Path("references") / "principles-checklist.md"
EXIT_HELP = "Exit codes: 0 ok; 2 usage (including an output path that is the input or inside the skill); 3 validation failed; 4 unavailable; 5 internal."


class SnapshotError(ValueError):
    """The packaged dependency or record cannot be validated."""


class UsageError(ValueError):
    """The command line asks for something the scripts refuse to do."""


class Unavailable(Exception):
    def __init__(self, url, reason):
        self.result = {"unavailable": True, "source_url": url, "reason": reason}
        super().__init__(reason)


def normalize_body(body):
    text = body.decode("utf-8") if isinstance(body, bytes) else body
    return (text.replace("\r\n", "\n").rstrip("\n") + "\n").encode("utf-8")


def parse_yaml_subset(text):
    """Parse scalar keys and two-space maps; reject ambiguous or duplicate keys."""
    result, current = {}, None
    for line in text.splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        match = re.fullmatch(r"(  )?([a-zA-Z][a-zA-Z0-9_-]*):(?: (.*))?", line)
        if not match:
            raise SnapshotError("unsupported YAML line: " + line)
        indent, key, raw = match.groups()
        if indent:
            if current is None:
                raise SnapshotError("nested key without map")
            target = result[current]
        else:
            target, current = result, None
        if key in target:
            raise SnapshotError("duplicate YAML key: " + key)
        if raw is None or raw == "":
            if indent:
                raise SnapshotError("only two-space maps supported")
            target[key], current = {}, key
        elif raw.startswith('"'):
            try:
                value = json.loads(raw)
            except ValueError as exc:
                raise SnapshotError("invalid quoted value") from exc
            if not isinstance(value, str):
                raise SnapshotError("expected string")
            target[key] = value
        elif raw.startswith("'"):
            if not raw.endswith("'") or len(raw) < 2:
                raise SnapshotError("invalid quoted value")
            target[key] = raw[1:-1].replace("''", "'")
        elif raw in ("true", "false"):
            target[key] = raw == "true"
        else:
            if raw.startswith(("[", "{", "|", ">", "&", "*", "!")):
                raise SnapshotError("expected scalar string")
            target[key] = raw
    return result


def parse_frontmatter(text):
    lines = text.splitlines()
    if not lines or lines[0] != "---":
        raise SnapshotError("missing frontmatter")
    try:
        end = lines.index("---", 1)
    except ValueError as exc:
        raise SnapshotError("unclosed frontmatter") from exc
    return parse_yaml_subset("\n".join(lines[1:end]))


def valid_source_url(url, revision, base_url=BASE_URL):
    if not isinstance(url, str) or not isinstance(revision, str):
        return False
    try:
        parsed, base = urllib.parse.urlsplit(url), urllib.parse.urlsplit(base_url)
        # An explicit loopback base is the only HTTP exception, for hermetic tests.
        allowed_scheme = base.scheme == "https" or (
            base.scheme == "http" and base.hostname in ("127.0.0.1", "localhost", "::1"))
        parts = parsed.path.split("/")
        return bool(allowed_scheme and not base.path.rstrip("/")
                    and parsed.scheme == base.scheme and parsed.netloc == base.netloc
                    and not parsed.username and not parsed.password
                    and not parsed.query and not parsed.fragment
                    and len(parts) >= 5 and parts[0] == ""
                    and all(re.fullmatch(r"[A-Za-z0-9_.-]+", p) and p not in (".", "..")
                            for p in parts[1:])
                    and re.fullmatch(r"[0-9a-f]{40}", revision)
                    and parts[3] == revision)
    except ValueError:
        return False


def load_catalog(root=None, *, base_url=BASE_URL):
    """Return the packaged catalog and the SKILL.md metadata map with the skill name added."""
    root = Path(root) if root is not None else ROOT
    try:
        frontmatter = parse_frontmatter((root / "SKILL.md").read_text(encoding="utf-8"))
        meta = frontmatter.get("metadata")
        if not isinstance(meta, dict) or any(not isinstance(meta.get(k), str) or not meta[k] for k in PIN_KEYS):
            raise SnapshotError("missing pin field")
        if not isinstance(frontmatter.get("name"), str) or not frontmatter["name"]:
            raise SnapshotError("missing skill name")
        meta = dict(meta, name=frontmatter["name"])
        if not re.fullmatch(r"[0-9a-f]{40}", meta["corpus-revision"]):
            raise SnapshotError("invalid corpus revision")
        for key in ("catalog-sha256", "principles-sha256", CHECKLIST_KEY):
            if key in meta and not re.fullmatch(r"[0-9a-f]{64}", meta[key]):
                raise SnapshotError("invalid hash: " + key)
        raw = (root / "assets" / "catalog.json").read_bytes()
        if hashlib.sha256(raw).hexdigest() != meta["catalog-sha256"]:
            raise SnapshotError("catalog file hash mismatch")
        checklist = root / CHECKLIST_PATH
        if checklist.exists() != (CHECKLIST_KEY in meta):
            raise SnapshotError("checklist and its pin must be packaged together")
        if checklist.exists() and hashlib.sha256(checklist.read_bytes()).hexdigest() != meta[CHECKLIST_KEY]:
            raise SnapshotError("checklist file hash mismatch")
        catalog = json.loads(raw)
        if not isinstance(catalog, dict) or catalog.get("revision") != meta["corpus-revision"]:
            raise SnapshotError("catalog revision mismatch")
        cards = catalog.get("cards")
        if not isinstance(cards, list) or not cards:
            raise SnapshotError("missing cards")
        ids = set()
        for card in cards:
            if not isinstance(card, dict) or any(not isinstance(card.get(k), str) or not card[k]
                                                for k in ("id", "source_url", "source_sha256")):
                raise SnapshotError("card missing id, source_url or source_sha256")
            if card["id"] in ids or not re.fullmatch(r"[a-z0-9-]+/[a-z0-9-]+", card["id"]):
                raise SnapshotError("duplicate or invalid card id")
            ids.add(card["id"])
            if not re.fullmatch(r"[0-9a-f]{64}", card["source_sha256"]):
                raise SnapshotError("invalid card hash")
        principles = catalog.get("principles")
        if not isinstance(principles, dict):
            raise SnapshotError("missing Principles")
        for entry in cards + [principles]:
            if not valid_source_url(entry.get("source_url"), meta["corpus-revision"], base_url):
                raise SnapshotError("source_url does not carry the pinned host and SHA")
        return catalog, meta
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise SnapshotError(str(exc)) from exc


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def request_bytes(url, timeout):
    try:
        request = urllib.request.Request(url, headers={"User-Agent": "verification-skills/1.0"})
        with urllib.request.build_opener(NoRedirect()).open(request, timeout=timeout) as response:
            if response.status != 200:
                raise Unavailable(url, "http-" + str(response.status))
            return response.read()
    except urllib.error.HTTPError as exc:
        raise Unavailable(url, "http-" + str(exc.code)) from exc
    except (TimeoutError, socket.timeout) as exc:
        raise Unavailable(url, "timeout") from exc
    except urllib.error.URLError as exc:
        reason = "timeout" if isinstance(exc.reason, (TimeoutError, socket.timeout)) else "transport"
        raise Unavailable(url, reason) from exc
    except (OSError, http.client.HTTPException) as exc:
        raise Unavailable(url, "transport") from exc


def fetch_source(entry, *, offline, timeout):
    """Retrieve one pinned entry. Runtime pin/base/hash are attached by source_entry."""
    url = entry.get("source_url")
    if not valid_source_url(url, entry.get("_revision"), entry.get("_base_url", BASE_URL)):
        raise Unavailable(url, "refused-url")
    if offline or os.environ.get("VERIFICATION_SKILLS_OFFLINE") == "1":
        raise Unavailable(url, "offline")
    try:
        body = normalize_body(request_bytes(url, timeout))
    except UnicodeError as exc:
        raise Unavailable(url, "hash-mismatch") from exc
    if hashlib.sha256(body).hexdigest() != entry.get("source_sha256"):
        raise Unavailable(url, "hash-mismatch")
    return body


def source_entry(catalog, meta, name, base_url=BASE_URL):
    if name == "principles":
        entry = dict(catalog["principles"], source_sha256=meta["principles-sha256"])
    else:
        entry = next((dict(c) for c in catalog["cards"] if c["id"] == name), None)
        if entry is None:
            raise SnapshotError("unknown card: " + name)
    # Rebase only the host, preserving the owner, repo, pin and source path.
    if base_url != BASE_URL:
        entry["source_url"] = base_url.rstrip("/") + urllib.parse.urlsplit(entry["source_url"]).path
    return dict(entry, _revision=meta["corpus-revision"], _base_url=base_url)


def drift(catalog, *, live_url=LIVE_URL, offline=False, timeout=10):
    if offline or os.environ.get("VERIFICATION_SKILLS_OFFLINE") == "1":
        raise Unavailable(live_url, "offline")
    try:
        live = json.loads(request_bytes(live_url, timeout))["revision"]
        if not isinstance(live, str) or not re.fullmatch(r"[0-9a-f]{40}", live):
            raise ValueError("invalid live revision")
    except (ValueError, KeyError, TypeError, UnicodeError) as exc:
        raise Unavailable(live_url, "invalid-catalog") from exc
    return {"pinned": catalog["revision"], "live": live, "newer_available": live != catalog["revision"]}


def skill_pins(meta):
    """The identity a record must carry: which skill, version and question set judged it."""
    pins = {"name": meta["name"], "version": meta["version"], "catalog_sha256": meta["catalog-sha256"],
            "principles_sha256": meta["principles-sha256"]}
    if CHECKLIST_KEY in meta:
        pins["checklist_sha256"] = meta[CHECKLIST_KEY]
    return pins


def resolve_output(output, *inputs):
    """Refuse a destination that would overwrite an input or land inside the skill directory."""
    if output == "-":
        return output
    target = Path(output).resolve()
    for path in inputs:
        if path is not None and Path(path).exists() and Path(path).resolve() == target:
            raise UsageError("output must not overwrite the input: " + str(path))
    if target == ROOT or ROOT in target.parents:
        raise UsageError("output must not be inside the skill directory: " + str(ROOT))
    return output


def parser(description, example):
    return argparse.ArgumentParser(description=description, epilog=EXIT_HELP + " Example: " + example)


def read_record(path):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError, UnicodeError) as exc:
        raise SnapshotError("cannot read record: " + str(exc)) from exc


def write_file(output, text):
    """Create the operator's output directory if needed; resolve_output has already vetted the path."""
    target = Path(output)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8", newline="\n")


def emit(value, output="-"):
    text = json.dumps(value, ensure_ascii=False, indent=2) + "\n"
    if output == "-":
        sys.stdout.write(text)
    else:
        write_file(output, text)
        emit({"output": str(output)})


def write_text(text, output="-"):
    # stdout remains structured; --output FILE writes the actual rendered document.
    if output == "-":
        emit({"text": text})
    else:
        write_file(output, text)
        emit({"output": str(output)})


def cli_main(fn):
    try:
        return fn()
    except UsageError as exc:
        emit([{"card": None, "rule": "usage", "message": str(exc)}])
        print(str(exc), file=sys.stderr)
        return 2
    except SnapshotError as exc:
        emit([{"card": None, "rule": "structure", "message": str(exc)}])
        print(str(exc), file=sys.stderr)
        return 3
    except Unavailable as exc:
        # A single JSON line is convenient to paste into an uncertainty record.
        print(json.dumps(exc.result, ensure_ascii=False))
        return 4
    except Exception as exc:
        print("internal: " + str(exc), file=sys.stderr)
        emit({"error": "internal", "message": str(exc)})
        return 5


def positive_timeout(value):
    try:
        number = float(value)
        if not math.isfinite(number) or number <= 0:
            raise ValueError()
        return number
    except ValueError as exc:
        raise argparse.ArgumentTypeError("timeout must be positive and finite") from exc


def main():
    p = parser(__doc__, "python3 scripts/load_catalog.py fetch principles --offline")
    mode = p.add_mutually_exclusive_group()
    mode.add_argument("--check", action="store_true", help="verify packaged snapshot")
    mode.add_argument("--drift", action="store_true", help="report live revision without changing the snapshot")
    p.add_argument("command", choices=["fetch"], nargs="?", help="retrieve pinned source text")
    p.add_argument("name", nargs="?", help="card id or principles")
    p.add_argument("--offline", action="store_true", help="disable requests (also VERIFICATION_SKILLS_OFFLINE=1)")
    p.add_argument("--timeout", type=positive_timeout, default=10, metavar="S", help="request timeout, seconds (default 10)")
    p.add_argument("--base-url", default=BASE_URL, help="raw source host; loopback override for tests")
    p.add_argument("--live-url", default=LIVE_URL, help="live catalog URL for drift")
    p.add_argument("--output", default="-", metavar="FILE|-", help="destination; stdout is a JSON text envelope")
    args = p.parse_args()
    if sum((args.check, args.drift, args.command == "fetch")) != 1 or bool(args.name) != (args.command == "fetch"):
        p.error("choose --check, --drift, or fetch <card-id|principles>")
    resolve_output(args.output)
    try:
        catalog, meta = load_catalog()
    except SnapshotError as exc:
        if args.drift:
            raise Unavailable(args.live_url, "invalid-snapshot") from exc
        raise
    if args.check:
        emit({"python": ".".join(map(str, sys.version_info[:3])), "valid": True, "revision": catalog["revision"], "cards": len(catalog["cards"]),
              "skill": skill_pins(meta)}, args.output)
    elif args.drift:
        emit(drift(catalog, live_url=args.live_url, offline=args.offline, timeout=args.timeout), args.output)
    else:
        entry = source_entry(catalog, meta, args.name, args.base_url)
        body = fetch_source(entry, offline=args.offline, timeout=args.timeout)
        write_text(body.decode("utf-8"), args.output)
    return 0


if __name__ == "__main__":
    sys.exit(cli_main(main))
