#!/usr/bin/env python3
"""Check the self-contained verification skills, pinned corpus and fixtures."""
import argparse
import difflib
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
import urllib.parse

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parent.parent
SKILLS = ROOT / "skills"
NAMES = ("verification-design", "verification-audit")


def import_file(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


loader = import_file("skills_loader", SKILLS / NAMES[0] / "scripts/load_catalog.py")
parse_frontmatter = loader.parse_frontmatter
parse_yaml_subset = loader.parse_yaml_subset
normalize_body = loader.normalize_body


def frontmatter_errors(text, directory, yaml_text):
    errors = []
    try:
        fm, ui = parse_frontmatter(text), parse_yaml_subset(yaml_text)
    except ValueError as exc:
        return [str(exc)]
    name, desc, compat = fm.get("name"), fm.get("description"), fm.get("compatibility")
    if not isinstance(name, str) or not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", name) or not 1 <= len(name) <= 64 or name != directory:
        errors.append("name must match directory and the 1 to 64 character naming rule")
    description_limit = 400 if directory == "verification-design" else 200
    if not isinstance(desc, str) or not 1 <= len(desc) <= description_limit:
        errors.append(f"description length must be 1 to {description_limit}")
    elif any(phrase in desc.lower() for phrase in ("use when", "whenever", "automatically", "trigger")) or "Do not run without an explicit request." not in desc:
        errors.append("description must carry the explicit-request sentence and no denylisted phrase")
    if not isinstance(compat, str) or not 0 < len(compat) < 500:
        errors.append("compatibility must be non-empty and under 500 characters")
    if fm.get("disable-model-invocation") is not True:
        errors.append("top-level invocation flag must be boolean true")
    meta = fm.get("metadata")
    if not isinstance(meta, dict) or meta.get("disable-model-invocation") != "true":
        errors.append("metadata invocation flag must be string true")
    if not isinstance(ui.get("policy"), dict) or ui["policy"].get("allow_implicit_invocation") is not False:
        errors.append("policy.allow_implicit_invocation must be boolean false")
    return errors


def run(argv, **kwargs):
    return subprocess.run(argv, cwd=ROOT, capture_output=True, text=True, env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1"), **kwargs)


def git(*args):
    result = subprocess.run(["git", *args], cwd=ROOT, capture_output=True)
    if result.returncode:
        raise ValueError(result.stderr.decode("utf-8", errors="replace").strip())
    return result.stdout


def source_path(url, revision):
    if not loader.valid_source_url(url, revision):
        raise ValueError("invalid pinned source URL")
    return "/".join(urllib.parse.urlsplit(url).path.split("/")[4:])


class Reporter:
    def __init__(self):
        self.failed = 0
        self.checks = 0

    def check(self, name, observed, expected, errors=()):
        errors = list(errors)
        passed = observed == expected and not errors
        self.checks += 1
        self.failed += not passed
        print(f'{"PASS" if passed else "FAIL"} {name}: observed={observed}, expected={expected}, failures={len(errors) + (observed != expected)}')
        for error in errors:
            print(f"  {error}", file=sys.stderr)


def fixture_checks(report):
    positive, rendered, negative = 0, 0, 0
    errors, render_errors, negative_errors = [], [], []
    names = ("design-sound", "design-applicability-violation", "design-resolved", "audit-known-defect", "audit-missing-evidence")
    with tempfile.TemporaryDirectory(prefix="verification-fixtures-") as tmp:
        for name in names:
            folder = SKILLS / "fixtures" / name
            kind = "design" if name.startswith("design-") else "audit"
            scripts = SKILLS / ("verification-" + kind) / "scripts"
            validator = scripts / ("validate_judgments.py" if kind == "design" else "validate_findings.py")
            record = folder / "record.json"
            result = run([sys.executable, str(validator), str(record)])
            if kind == "audit":
                # Rendering straight from the unrouted record must give the same bytes as rendering the routed one.
                direct = Path(tmp) / (name + ".direct.md")
                unrouted = run([sys.executable, str(scripts / "render_findings.py"), str(record), "--output", str(direct)])
                if unrouted.returncode != 0 or direct.read_bytes() != (folder / "expected.md").read_bytes():
                    render_errors.append(name + " unrouted render mismatch: " + unrouted.stdout + unrouted.stderr)
            if result.returncode == 0:
                positive += 1
            else:
                errors.append(name + ": " + result.stdout + result.stderr)
            routed = Path(tmp) / (name + ".json")
            output = Path(tmp) / (name + ".md")
            if kind == "audit":
                route = run([sys.executable, str(scripts / "route_failures.py"), str(record), "--output", str(routed)])
                if route.returncode:
                    render_errors.append(name + " route: " + route.stdout + route.stderr)
                record = routed
            renderer = scripts / ("render_plan.py" if kind == "design" else "render_findings.py")
            result = run([sys.executable, str(renderer), str(record), "--output", str(output)])
            if result.returncode == 0 and output.read_bytes() == (folder / "expected.md").read_bytes():
                rendered += 1
            else:
                render_errors.append(name + " render mismatch: " + result.stdout + result.stderr)
            for bad in sorted(folder.glob("negative-*.json")):
                if bad.name.endswith(".expected.json"):
                    continue
                expected = json.loads(bad.with_suffix(".expected.json").read_text())
                result = run([sys.executable, str(validator), str(bad)])
                try:
                    rules = sorted({e["rule"] for e in json.loads(result.stdout)})
                except (ValueError, TypeError, KeyError):
                    rules = []
                if result.returncode == expected["exit_code"] and rules == sorted(expected["rules"]):
                    negative += 1
                else:
                    negative_errors.append(f"{bad.name}: exit={result.returncode}, rules={rules}, expected={expected}")
    report.check("fixture validators", positive, 5, errors)
    report.check("fixture renders", rendered, 5, render_errors)
    report.check("negative fixtures", negative, 23, negative_errors)


def helper_checks(report):
    scaffolds, citations = 0, 0
    scaffold_errors, citation_errors = [], []
    with tempfile.TemporaryDirectory(prefix="verification-helpers-") as tmp:
        root = Path(tmp)
        (root / "example.txt").write_text("first\nsecond\n")
        second = root / "second"
        second.mkdir()
        (second / "later.txt").write_text("later\n")
        (second / "example.txt").write_text("shorter\n")
        for name in NAMES:
            scripts = SKILLS / name / "scripts"
            design = name.endswith("design")
            path = root / "record.json"
            result = run([sys.executable, str(scripts / "scaffold_record.py"), "--artifact", "example", "--scope", "checks", "--output", str(path)])
            validator = scripts / ("validate_judgments.py" if design else "validate_findings.py")
            scaffold_receipt = result.stdout.strip()
            try:
                scaffold_receipt = json.dumps(json.loads(scaffold_receipt).get("counts"), sort_keys=True)
            except ValueError:
                pass
            validation = run([sys.executable, str(validator), str(path)])
            expected = {"assumptions", "structure", "models", "plan"} if design else {"status", "evidence", "models"}
            expected_counts = {"cards": 17, "conditions": 156} if design else {"checks": 18}
            try:
                good = result.returncode == 0 and json.loads(result.stdout)["counts"] == expected_counts and validation.returncode == 3 and {e["rule"] for e in json.loads(validation.stdout)} == expected
            except (ValueError, KeyError, TypeError):
                good = False
            scaffolds += good
            if not good:
                scaffold_errors.append(name + ": " + result.stdout + result.stderr + validation.stdout + validation.stderr)
            path.write_text(json.dumps({"evidence": "example.txt:1-2 absent.txt:1 example.txt:3 example.txt:1-2 later.txt:1",
                                        "checks": [{"evidence": "example.txt:1-2"}, {"evidence": "example.txt:1-2"}]}))
            result = run([sys.executable, str(scripts / "check_citations.py"), str(path), "--root", str(root), "--root", str(second)])
            try:
                data = json.loads(result.stdout)
                good = (result.returncode == 3 and data["counts"] == {"found": 2, "missing": 1, "out-of-bounds": 1, "requirements": 0, "unknown-requirement": 0}
                        and len(data["citations"]) == 2 and data["roots"] == [str(root), str(second)]
                        and data["resolved"] == [{"citation": "example.txt:1-2", "root": str(root)}, {"citation": "later.txt:1", "root": str(second)}]
                        and data["repeated"] == [{"citation": "example.txt:1-2", "entries": 3}])
            except (ValueError, KeyError, TypeError):
                good = False
            citations += good
            if not good:
                citation_errors.append(name + ": " + result.stdout + result.stderr)
            print(f'INFO {name} scaffold counts: {scaffold_receipt}; citation self-test counts: {json.dumps(data.get("counts"), sort_keys=True) if good else result.stdout.strip()}')
            print(f'INFO {name} citation roots/resolved/repeated counts: {len(data.get("roots", []))}/{len(data.get("resolved", []))}/{len(data.get("repeated", []))}')
    report.check("scaffolds fail validation", scaffolds, 2, scaffold_errors)
    report.check("citation checker self-tests", citations, 2, citation_errors)


def reference_check(report, enabled):
    if not enabled or not shutil.which("uvx"):
        print("SKIP skills-ref: " + ("--skills-ref not requested" if not enabled else "uvx not on PATH"))
        return
    verified, errors = 0, []
    with tempfile.TemporaryDirectory(prefix="verification-skills-ref-") as tmp:
        for name in NAMES:
            original, target = SKILLS / name, Path(tmp) / name
            shutil.copytree(original, target)
            text = (original / "SKILL.md").read_text()
            lines = text.splitlines(keepends=True)
            flag = "disable-model-invocation: true\n"
            if lines.count(flag) != 1:
                errors.append(name + ": expected exactly one top-level invocation line")
                continue
            stripped = [line for line in lines if line != flag]
            (target / "SKILL.md").write_text("".join(stripped))
            diff = list(difflib.ndiff(lines, stripped))
            changes = [line for line in diff if line[:2] != "  "]
            same_files = all((target / path.relative_to(original)).read_bytes() == path.read_bytes()
                             for path in original.rglob("*") if path.is_file() and path.name != "SKILL.md")
            if changes != ["- " + flag] or not same_files:
                errors.append(name + ": temporary copy changed more than the top-level flag")
                continue
            result = run(["uvx", "--from", "git+https://github.com/agentskills/agentskills@69ef37e9424c0a7ea9dd2293b559e43ec8176379#subdirectory=skills-ref", "skills-ref", "validate", str(target)], timeout=180)
            if result.returncode == 0:
                verified += 1
            else:
                errors.append(name + ": " + result.stdout + result.stderr)
    report.check("skills-ref", verified, 2, errors)


def link_checks(report, files, catalog, meta):
    sys.path.insert(0, str(ROOT))
    from research_tools import verify as verifier
    urls = set()
    for path in files:
        for url in re.findall(r'https?://[^\s<>"`]+', path.read_text(encoding="utf-8")):
            urls.add(url.rstrip(".,;:)"))
    # Anchors are checked hermetically where the pinned source is available.
    urls = {urllib.parse.urldefrag(url)[0] for url in urls}
    ok, errors = 0, []
    for url in sorted(urls):
        live, detail = verifier.url_ok(url)
        if live:
            ok += 1
        else:
            errors.append(url + ": " + detail)
    report.check("live URLs", ok, len(urls) if urls else 1, errors)
    ok, errors = 0, []
    for name in [c["id"] for c in catalog["cards"]] + ["principles"]:
        try:
            loader.fetch_source(loader.source_entry(catalog, meta, name), offline=False, timeout=15)
            ok += 1
        except loader.Unavailable as exc:
            errors.append(json.dumps(exc.result))
    report.check("live source hashes", ok, 18, errors)


def main():
    p = argparse.ArgumentParser(description=__doc__, epilog="Exit codes: 0 ok; 2 usage; 3 validation failed; 4 unavailable (source helpers); 5 internal. Example: python3 skills/check_skills.py")
    p.add_argument("--links", action="store_true", help="also check live URLs and source hashes (not for CI)")
    p.add_argument("--skills-ref", action="store_true", help="run the optional pinned skills-ref validator via uvx")
    args = p.parse_args()
    report = Reporter()
    metas, catalogs = [], []
    for name in NAMES:
        folder = SKILLS / name
        text = (folder / "SKILL.md").read_text()
        errors = frontmatter_errors(text, name, (folder / "agents/openai.yaml").read_text())
        report.check(name + " frontmatter", 1, 1, errors)
        metas.append(parse_frontmatter(text)["metadata"])
        try:
            catalog, _ = loader.load_catalog(folder)
            catalogs.append(catalog)
            report.check(name + " snapshot", len(catalog["cards"]), 17)
        except loader.SnapshotError as exc:
            report.check(name + " snapshot", 0, 17, [str(exc)])
    same = sum(metas[0].get(k) == metas[1].get(k) and isinstance(metas[0].get(k), str) and bool(metas[0][k]) for k in loader.PIN_KEYS)
    report.check("pin consistency", same, 5)
    checklist_file = SKILLS / NAMES[1] / loader.CHECKLIST_PATH
    observed = hashlib.sha256(checklist_file.read_bytes()).hexdigest() if checklist_file.exists() else "absent"
    report.check("checklist pin", observed, metas[1].get(loader.CHECKLIST_KEY),
                 [] if loader.CHECKLIST_KEY not in metas[0] else ["design skill must not carry a checklist pin"])
    for path, label in (("assets/catalog.json", "snapshot byte identity"), ("scripts/load_catalog.py", "loader byte identity")):
        report.check(label, int((SKILLS/NAMES[0]/path).read_bytes() == (SKILLS/NAMES[1]/path).read_bytes()), 1)
    if not catalogs:
        print(f"Summary: {report.checks} checks, {report.failed} failed; dependency checks blocked.")
        return 3
    catalog, meta = catalogs[0], metas[0]
    revision = meta["corpus-revision"]
    errors = []
    try:
        git("cat-file", "-e", revision + "^{commit}")
        if git("rev-parse", meta["corpus-tag"] + "^{commit}").decode().strip() != revision:
            errors.append("tag does not resolve to pin")
    except ValueError as exc:
        errors.append(str(exc))
    report.check("git commit and tag", 0 if errors else 2, 2, errors)
    for entries, label, expected in ((catalog["cards"], "git card hashes", 17), ([dict(catalog["principles"], source_sha256=meta["principles-sha256"])], "git Principles hash", 1)):
        ok, errors = 0, []
        for entry in entries:
            try:
                source = source_path(entry["source_url"], revision)
                observed = hashlib.sha256(normalize_body(git("show", revision + ":" + source))).hexdigest()
                if observed == entry["source_sha256"]:
                    ok += 1
                else:
                    errors.append(source + ": " + observed + " != " + entry["source_sha256"])
            except (ValueError, UnicodeError) as exc:
                errors.append(str(exc))
        report.check(label, ok, expected, errors)
    # Package content only: the checker and its tests live here too but are not
    # shipped skill files, and their fixture URLs are not meant to be fetched.
    tooling = (Path(__file__).resolve(), SKILLS / "tests")
    files = sorted(path for path in SKILLS.rglob("*") if path.is_file()
                   and path != tooling[0] and tooling[1] not in path.parents)
    report.check("no symlinks", sum(not p.is_symlink() for p in SKILLS.rglob("*")), len(list(SKILLS.rglob("*"))))
    ids, found, errors = {c["id"] for c in catalog["cards"]}, set(), []
    categories = "|".join(sorted({c["category"] for c in catalog["cards"]}))
    for path in files:
        text = path.read_text(encoding="utf-8")
        mentioned = set(re.findall(r"\b(?:" + categories + r")/[a-z0-9-]+", text))
        mentioned.update(re.findall(r'"id"\s*:\s*"([a-z0-9-]+/[a-z0-9-]+)"', text))
        found.update(mentioned)
        errors.extend(str(path.relative_to(ROOT)) + ": unknown id " + cid for cid in sorted(mentioned - ids))
    report.check("card ids", len(found & ids), len(ids), errors)
    entries = catalog["cards"] + [catalog["principles"]]
    report.check("pinned source URLs", sum(loader.valid_source_url(e["source_url"], revision) for e in entries), 18)
    errors = []
    for path in files:
        text = path.read_text(encoding="utf-8")
        if "\u2014" in text or "\u2013" in text:
            errors.append(str(path.relative_to(ROOT)) + ": forbidden dash")
    report.check("dash-free files", len(files), len(files) if files else 1, errors)
    for name in NAMES:
        count = len((SKILLS/name/"SKILL.md").read_text().splitlines())
        report.check(name + " body line limit", count, count, [] if 0 < count < 500 else ["expected 1 to 499 lines"])
    # Checklist citations must refer to real numbered headings at the pin.
    source = git("show", revision + ":verification_design.md").decode()
    headings = re.findall(r"^### ([1-9]\. .+?)\r?$", source, re.M)
    anchors = {re.sub(r"[^\w\s-]", "", h.strip().lower()).replace(" ", "-") for h in headings}
    checklist = (SKILLS/NAMES[1]/"references/principles-checklist.md").read_text()
    expected_prefix = catalog["principles"]["source_url"] + "#"
    questions = re.findall(r"^- (.+)$", checklist, re.M)
    good = sum(any(expected_prefix + a + ")" in q for a in anchors) for q in questions)
    report.check("checklist pinned anchors", good, 18)
    fixture_checks(report)
    helper_checks(report)
    expected_tests = unittest.defaultTestLoader.discover(str(ROOT / "skills/tests")).countTestCases()
    result = run([sys.executable, "-m", "unittest", "discover", "-s", "skills/tests"])
    match = re.search(r"Ran (\d+) tests?", result.stderr)
    count = int(match[1]) if match else 0
    report.check("unit tests", count, expected_tests if expected_tests else 1, [] if result.returncode == 0 and count else [result.stderr + result.stdout])
    reference_check(report, args.skills_ref)
    if args.links:
        link_checks(report, files, catalog, meta)
    else:
        print("SKIP links: --links not requested; hermetic mode")
    print(f"Summary: {report.checks} checks, {report.failed} failed.")
    return 3 if report.failed else 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:
        print("FAIL checker: " + str(exc), file=sys.stderr)
        sys.exit(5)
