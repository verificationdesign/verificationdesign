"""Catalog boundaries using the audit copy, including offline snapshot tests.

Transport-only LC-17, LC-19, LC-21, LC-22 and LC-23 remain in test_skills_retrieval.
"""
import copy
from contextlib import redirect_stdout, redirect_stderr
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch
from support import ROOT, AUDIT, DESIGN, ScriptCase, module

loader = module("load_catalog")
spec = importlib.util.spec_from_file_location("b2_checker", ROOT / "skills/check_skills.py")
checker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checker)


class ParserTests(unittest.TestCase):
    def setUp(self):
        self.text = (DESIGN / "SKILL.md").read_text()
        self.yaml = (DESIGN / "agents/openai.yaml").read_text()

    def test_good_frontmatter_and_host_policy(self):
        self.assertEqual(checker.frontmatter_errors(self.text, DESIGN.name, self.yaml), [])
        parsed = checker.parse_frontmatter(self.text)
        self.assertIs(parsed["disable-model-invocation"], True)
        self.assertEqual(parsed["metadata"]["disable-model-invocation"], "true")

    def test_bad_description(self):
        for phrase in ("use when", "whenever", "automatically", "trigger"):
            with self.subTest(phrase=phrase):
                bad = self.text.replace("Write a verification plan", phrase + " a verification plan")
                self.assertTrue(checker.frontmatter_errors(bad, DESIGN.name, self.yaml))

    def test_missing_explicit_request_sentence(self):
        self.assertTrue(checker.frontmatter_errors(self.text.replace("Do not run without an explicit request.", ""), DESIGN.name, self.yaml))

    def test_wrong_name_and_flag_types(self):
        for old, new in (("name: verification-design", "name: Wrong_Name"), ("disable-model-invocation: true\n", 'disable-model-invocation: "true"\n'), ('  disable-model-invocation: "true"', "  disable-model-invocation: true")):
            with self.subTest(new=new):
                self.assertTrue(checker.frontmatter_errors(self.text.replace(old, new, 1), DESIGN.name, self.yaml))

    def test_bad_yaml_policy(self):
        for value in ("true", '"false"'):
            self.assertTrue(checker.frontmatter_errors(self.text, DESIGN.name, self.yaml.replace("false", value)))

    def test_lc_3_frontmatter_missing_or_unclosed(self):
        """LC-3 is code-only."""
        for text in ("name: example\n", "---\nname: example\n"):
            with self.assertRaises(ValueError):
                loader.parse_frontmatter(text)

    def test_lc_2_yaml_subset_good(self):
        self.assertEqual(loader.parse_yaml_subset('policy:\n  enabled: false\n  text: "true"\nname: example\n'), {"policy": {"enabled": False, "text": "true"}, "name": "example"})

    def test_lc_2_yaml_subset_rejects_ambiguous_inputs(self):
        for text in ('a: x\na: y\n', '  a: x\n', 'a:\n    b: true\n', 'a: "unterminated\n', 'a: [x]\n', 'a:\n  b:\n'):
            with self.subTest(text=text), self.assertRaises(ValueError):
                loader.parse_yaml_subset(text)

    def test_lc_19_normalization_crlf(self):
        self.assertEqual(loader.normalize_body(b"one\r\ntwo\r\n\r\n"), b"one\ntwo\n")
        self.assertEqual(loader.normalize_body(b"one\n"), b"one\n")
        self.assertEqual(loader.normalize_body(b""), b"\n")



class LoaderTests(ScriptCase):
    def test_lc_1_python_guard(self):
        from unittest.mock import patch
        import io
        from contextlib import redirect_stderr
        require_python = loader.require_python
        with patch.object(sys, "version_info", (3, 9, 6)), redirect_stderr(io.StringIO()) as stderr:
            with self.assertRaises(SystemExit) as exc:
                require_python()
        self.assertEqual(exc.exception.code, 2)
        self.assertEqual(stderr.getvalue(), "Python 3.9.6 found; Python 3.11 or later required\n")
        with patch.object(sys, "version_info", (3, 11, 0)):
            require_python()


    def test_lc_7_checklist_pin_is_enforced_by_the_loader(self):
        import shutil
        audit = ROOT / "skills/verification-audit"
        with tempfile.TemporaryDirectory() as tmp:
            copy = Path(tmp) / "verification-audit"
            shutil.copytree(audit, copy)
            catalog, meta = loader.load_catalog(copy)
            self.assertEqual(meta["name"], "verification-audit")
            self.assertIn("checklist_sha256", loader.skill_pins(meta))
            checklist = copy / loader.CHECKLIST_PATH
            checklist.write_text(checklist.read_text() + "\n- An extra question nobody pinned.\n")
            with self.assertRaises(loader.SnapshotError):
                loader.load_catalog(copy)
            checklist.unlink()
            with self.assertRaises(loader.SnapshotError):
                loader.load_catalog(copy)
            design = Path(tmp) / "verification-design"
            shutil.copytree(ROOT / "skills/verification-design", design)
            self.assertNotIn("checklist_sha256", loader.skill_pins(loader.load_catalog(design)[1]))
            shutil.copy(audit / loader.CHECKLIST_PATH, design / "references" / "principles-checklist.md")
            with self.assertRaises(loader.SnapshotError):
                loader.load_catalog(design)


    def snapshot(self, *, front=None, catalog=None):
        target = self.root / "snapshot"
        if target.exists():
            shutil.rmtree(target)
        shutil.copytree(AUDIT, target)
        text = (target / "SKILL.md").read_text()
        if catalog is not None:
            value, meta = loader.load_catalog(target)
            catalog(value)
            raw = (json.dumps(value) + "\n").encode()
            (target / "assets/catalog.json").write_bytes(raw)
            text = text.replace(meta["catalog-sha256"], hashlib.sha256(raw).hexdigest())
        if front is not None:
            text = front(text)
        (target / "SKILL.md").write_text(text)
        return target

    def test_lc_4_required_pins_and_name(self):
        for key in (*loader.PIN_KEYS, "name"):
            for replacement in (None, '""', 'false'):
                def change(text):
                    return "\n".join(
                        line if not line.lstrip().startswith(key + ":") else
                        ("" if replacement is None else line.split(":", 1)[0] + ": " + replacement)
                        for line in text.splitlines()) + "\n"
                with self.subTest(key=key, replacement=replacement):
                    target = self.snapshot(front=change)
                    with self.assertRaisesRegex(loader.SnapshotError, "missing skill name" if key == "name" else "missing pin field"):
                        loader.load_catalog(target)

    def test_lc_5_malformed_revision_and_hashes(self):
        _, meta = loader.load_catalog()
        for key, width in (("corpus-revision", 40), ("catalog-sha256", 64),
                           ("principles-sha256", 64), ("checklist-sha256", 64)):
            for bad in ("a" * (width - 1), "a" * (width + 1), "G" * width):
                with self.subTest(key=key, bad=bad):
                    target = self.snapshot(front=lambda s: s.replace(meta[key], bad))
                    with self.assertRaisesRegex(loader.SnapshotError, "invalid corpus revision" if width == 40 else "invalid hash: " + key):
                        loader.load_catalog(target)

    def test_lc_9_cards_and_ids(self):
        """LC-9 is code-only; each variant changes just one catalog constraint."""
        changes = [lambda c: c.pop("cards"), lambda c: c.update(cards=[]),
                   lambda c: c.update(cards={}),
                   lambda c: c["cards"].append(copy.deepcopy(c["cards"][0]))]
        changes += [lambda c, bad=bad: c["cards"][0].update(id=bad)
                    for bad in ("UPPER/card", "no-slash", "a/b/c", "a/_")]
        changes += [lambda c, bad=bad: c["cards"][0].update(source_sha256=bad)
                    for bad in ("a" * 63, "a" * 65, "G" * 64)]
        for index, change in enumerate(changes):
            with self.subTest(index=index):
                target = self.snapshot(catalog=change)
                message = "missing cards" if index < 3 else "duplicate or invalid card id" if index < 8 else "invalid card hash"
                with self.assertRaisesRegex(loader.SnapshotError, message):
                    loader.load_catalog(target)

    def test_lc_10_each_required_card_field(self):
        """LC-10 is code-only."""
        for key in ("id", "source_url", "source_sha256"):
            for value in (None, "", 12):
                with self.subTest(key=key, value=value):
                    target = self.snapshot(catalog=lambda c: c["cards"][0].update({key: value}))
                    with self.assertRaisesRegex(loader.SnapshotError, "card missing id, source_url or source_sha256"):
                        loader.load_catalog(target)
            target = self.snapshot(catalog=lambda c: c["cards"][0].pop(key))
            with self.assertRaisesRegex(loader.SnapshotError, "card missing id, source_url or source_sha256"):
                loader.load_catalog(target)

    def test_lc_11_principles_and_pinned_urls(self):
        for change in (lambda c: c.pop("principles"), lambda c: c.update(principles=[])):
            with self.assertRaisesRegex(loader.SnapshotError, "missing Principles"):
                loader.load_catalog(self.snapshot(catalog=change))
        for location in ("card", "principles"):
            for part, replacement in (("raw.githubusercontent.com", "example.invalid"),
                                      (loader.load_catalog()[1]["corpus-revision"], "0" * 40)):
                def change(c):
                    entry = c["cards"][0] if location == "card" else c["principles"]
                    entry["source_url"] = entry["source_url"].replace(part, replacement)
                with self.subTest(location=location, part=part):
                    with self.assertRaisesRegex(loader.SnapshotError, "source_url does not carry the pinned host and SHA"):
                        loader.load_catalog(self.snapshot(catalog=change))

    def test_lc_13_check_report(self):
        catalog, meta = loader.load_catalog()
        result = self.run_script("audit", "load_catalog.py", "--check")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout), {
            "python": ".".join(map(str, sys.version_info[:3])), "valid": True,
            "revision": catalog["revision"], "cards": len(catalog["cards"]),
            "skill": {"name": "verification-audit", "version": meta["version"],
                      "catalog_sha256": meta["catalog-sha256"], "principles_sha256": meta["principles-sha256"],
                      "checklist_sha256": meta["checklist-sha256"]}})

    def test_lc_14_selection_and_unknown_card(self):
        catalog, meta = loader.load_catalog()
        for card in catalog["cards"]:
            self.assertEqual(loader.source_entry(catalog, meta, card["id"]),
                             dict(card, _revision=meta["corpus-revision"], _base_url=loader.BASE_URL))
        changed = dict(meta, **{"principles-sha256": "b" * 64})
        self.assertEqual(loader.source_entry(catalog, changed, "principles"),
                         dict(catalog["principles"], source_sha256="b" * 64,
                              _revision=meta["corpus-revision"], _base_url=loader.BASE_URL))
        with self.assertRaisesRegex(loader.SnapshotError, "unknown card: absent/card"):
            loader.source_entry(catalog, meta, "absent/card")

    def test_lc_16_unsafe_urls_make_no_request(self):
        """LC-16 is code-only."""
        catalog, meta = loader.load_catalog()
        original = loader.source_entry(catalog, meta, "principles")
        url = original["source_url"]
        urls = [url.replace("https://", "https://user:pass@"), url + "?query=1", url + "#fragment"]
        urls += [url.rsplit("/", 1)[0] + "/" + segment + "/source.md"
                 for segment in (".", "..", "", "%2e", "a b", "a\\b")]
        for bad in urls:
            with self.subTest(url=bad), patch.object(loader, "request_bytes") as request:
                with self.assertRaises(loader.Unavailable) as caught:
                    loader.fetch_source(dict(original, source_url=bad), offline=False, timeout=1)
                self.assertEqual(caught.exception.result, {"unavailable": True, "source_url": bad, "reason": "refused-url"})
                request.assert_not_called()

    def test_lc_20_invalid_utf8(self):
        """LC-20 is code-only; transport bytes are supplied without a socket."""
        catalog, meta = loader.load_catalog()
        entry = loader.source_entry(catalog, meta, "principles")
        with patch.dict(os.environ, {"VERIFICATION_SKILLS_OFFLINE": "0"}), patch.object(loader, "request_bytes", return_value=b"\xff") as request:
            with self.assertRaises(loader.Unavailable) as caught:
                loader.fetch_source(entry, offline=False, timeout=2)
        request.assert_called_once_with(entry["source_url"], 2)
        self.assertEqual(caught.exception.result, {"unavailable": True, "source_url": entry["source_url"], "reason": "hash-mismatch"})

    def test_lc_24_drift_offline(self):
        catalog, _ = loader.load_catalog()
        for flag, env in ((True, "0"), (False, "1")):
            with self.subTest(flag=flag), patch.dict(os.environ, {"VERIFICATION_SKILLS_OFFLINE": env}), patch.object(loader, "request_bytes") as request:
                with self.assertRaises(loader.Unavailable) as caught:
                    loader.drift(catalog, offline=flag, live_url="https://example.invalid/catalog.json")
                self.assertEqual(caught.exception.result, {"unavailable": True, "source_url": "https://example.invalid/catalog.json", "reason": "offline"})
                request.assert_not_called()

    def test_lc_25_invalid_live_catalog(self):
        """LC-25 is code-only."""
        catalog, _ = loader.load_catalog()
        for raw in (b"{", b"{}", b"[]", b"null", b'\xff', b'{"revision":12}',
                    b'{"revision":"short"}', b'{"revision":"' + b'G' * 40 + b'"}'):
            with self.subTest(raw=raw), patch.dict(os.environ, {"VERIFICATION_SKILLS_OFFLINE": "0"}), patch.object(loader, "request_bytes", return_value=raw):
                with self.assertRaises(loader.Unavailable) as caught:
                    loader.drift(catalog)
                self.assertEqual(caught.exception.result, {"unavailable": True, "source_url": loader.LIVE_URL, "reason": "invalid-catalog"})

    def test_lc_26_drift_invalid_snapshot(self):
        """LC-26 is code-only; invoke the actual CLI in a temporary broken package."""
        target = self.snapshot(front=lambda s: s.replace("name: verification-audit", "name: false"))
        import subprocess
        result = subprocess.run([sys.executable, str(target / "scripts/load_catalog.py"), "--drift"], capture_output=True, text=True)
        self.assertEqual(result.returncode, 4)
        self.assertEqual(json.loads(result.stdout), {"unavailable": True, "source_url": loader.LIVE_URL, "reason": "invalid-snapshot"})
        self.assertEqual(result.stderr, "invalid-snapshot\n")

    def test_lc_27_mode_combinations(self):
        for args in ((), ("fetch",), ("--check", "--drift"), ("--check", "fetch", "principles"),
                     ("--drift", "fetch", "principles"), ("--check", "principles"), ("wrong",)):
            with self.subTest(args=args):
                result = self.run_script("audit", "load_catalog.py", *args, "--offline")
                self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
                self.assertEqual(result.stdout, "")
                self.assertIn("usage:", result.stderr)
        for args in (("fetch", "principles"), ("--drift",)):
            result = self.run_script("audit", "load_catalog.py", *args, "--offline")
            self.assertEqual(result.returncode, 4)
            self.assertEqual(json.loads(result.stdout)["reason"], "offline")

    def test_lc_28_timeout_arguments(self):
        for value in ("0", "-1", "nan", "inf", "-inf", "no-number"):
            with self.subTest(value=value):
                result = self.run_script("audit", "load_catalog.py", "--check", "--timeout=" + value)
                self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
                self.assertEqual(result.stdout, "")
                self.assertIn("timeout must be positive and finite", result.stderr)
        self.assertEqual(loader.positive_timeout("0.01"), 0.01)

    def test_lc_29_resolved_output_boundaries(self):
        inside = AUDIT / "assets/never-written.json"
        self.assertFalse(inside.exists())
        self.addCleanup(inside.unlink, missing_ok=True)
        self.record.write_bytes(b"original\n")
        alias = self.root / "alias"
        alias.symlink_to(self.record)
        skill_alias = self.root / "skill"
        skill_alias.symlink_to(AUDIT, target_is_directory=True)
        for target in (self.record, alias, self.root / "sub/../record.json", AUDIT,
                       AUDIT / "assets/never-written.json", skill_alias / "new.json"):
            with self.subTest(target=target), self.assertRaises(loader.UsageError):
                loader.resolve_output(str(target), self.record)
        self.assertEqual(self.record.read_bytes(), b"original\n")
        self.assertEqual(loader.resolve_output("-", self.record), "-")
        self.assertEqual(loader.resolve_output(str(self.output), self.record), str(self.output))
        inside = AUDIT / "assets/never-written.json"
        result = self.run_script("audit", "load_catalog.py", "--check", "--output", inside)
        self.assertEqual(result.returncode, 2)
        self.assertEqual({e["rule"] for e in json.loads(result.stdout)}, {"usage"})
        self.assertFalse(inside.exists())

    def test_lc_30_utf8_lf_and_parent_directories(self):
        target = self.root / "new/nested/document.md"
        loader.write_file(target, "caf\u00e9\nsecond\n")
        self.assertEqual(target.read_bytes(), b"caf\xc3\xa9\nsecond\n")

    def test_lc_31_stdout_envelopes_and_file_receipts(self):
        for value in ({"valid": True, "name": "caf\u00e9"}, [1, None], "text", 5):
            with redirect_stdout(io.StringIO()) as out:
                loader.emit(value)
            self.assertEqual(json.loads(out.getvalue()), value)
            with redirect_stdout(io.StringIO()) as out:
                loader.emit(value, self.output)
            self.assertEqual(json.loads(out.getvalue()), {"output": str(self.output)})
            self.assertEqual(json.loads(self.output.read_text()), value)
        text = "caf\u00e9\nnext\n"
        with redirect_stdout(io.StringIO()) as out:
            loader.write_text(text)
        self.assertEqual(json.loads(out.getvalue()), {"text": text})
        with redirect_stdout(io.StringIO()) as out:
            loader.write_text(text, self.output)
        self.assertEqual(json.loads(out.getvalue()), {"output": str(self.output)})
        self.assertEqual(self.output.read_bytes(), text.encode("utf-8"))

    def test_lc_32_invalid_records_are_structure_errors(self):
        """LC-32 is code-only."""
        for data in (None, b"{", b"\xff"):
            if self.record.exists():
                self.record.unlink()
            if data is not None:
                self.record.write_bytes(data)
            with self.subTest(data=data), self.assertRaisesRegex(loader.SnapshotError, "cannot read record:"):
                loader.read_record(self.record)
        self.record.write_text('{"valid":true}')
        self.assertEqual(loader.read_record(self.record), {"valid": True})

    def test_lc_33_exception_exit_and_diagnostics(self):
        import subprocess
        cases = (("UsageError('bad usage')", 2, [{"card": None, "rule": "usage", "message": "bad usage"}], "bad usage\n"),
                 ("SnapshotError('bad record')", 3, [{"card": None, "rule": "structure", "message": "bad record"}], "bad record\n"),
                 ("Unavailable('source', 'offline')", 4, {"unavailable": True, "source_url": "source", "reason": "offline"}, "offline\n"),
                 ("RuntimeError('unexpected')", 5, {"error": "internal", "message": "unexpected"}, "internal: unexpected\n"))
        for expression, code, expected, stderr in cases:
            program = ("import sys\nsys.dont_write_bytecode = True\nsys.path.insert(0, " + repr(str(AUDIT / "scripts")) + ")\n"
                       "from load_catalog import *\ndef fail():\n    raise " + expression + "\nsys.exit(cli_main(fail))\n")
            result = subprocess.run([sys.executable, "-c", program], capture_output=True, text=True)
            with self.subTest(expression=expression):
                self.assertEqual(result.returncode, code)
                self.assertEqual(json.loads(result.stdout), expected)
                self.assertEqual(result.stderr, stderr)
        self.assertEqual(loader.cli_main(lambda: 7), 7)


class SnapshotTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name) / "verification-design"
        shutil.copytree(AUDIT, self.root)
        self.catalog, self.meta = loader.load_catalog(self.root)

    def change_catalog(self, change, rehash=True):
        value = copy.deepcopy(self.catalog)
        change(value)
        raw = (json.dumps(value) + "\n").encode()
        (self.root / "assets/catalog.json").write_bytes(raw)
        if rehash:
            skill = self.root / "SKILL.md"
            skill.write_text(skill.read_text().replace(self.meta["catalog-sha256"], hashlib.sha256(raw).hexdigest()))

    def test_lc_12_snapshot_loads(self):
        self.assertEqual(len(self.catalog["cards"]), 17)
        self.assertEqual(self.catalog["revision"], self.meta["corpus-revision"])

    def test_lc_8_snapshot_wrong_revision(self):
        self.change_catalog(lambda c: c.update(revision="0" * 40))
        with self.assertRaisesRegex(loader.SnapshotError, "revision mismatch"):
            loader.load_catalog(self.root)

    def test_lc_6_snapshot_wrong_file_hash(self):
        self.change_catalog(lambda c: c.update(generated="changed"), rehash=False)
        with self.assertRaisesRegex(loader.SnapshotError, "file hash mismatch"):
            loader.load_catalog(self.root)

    def test_lc_4_snapshot_missing_pin_field(self):
        path = self.root / "SKILL.md"
        path.write_text("\n".join(line for line in path.read_text().splitlines() if not line.startswith("  principles-sha256:")) + "\n")
        with self.assertRaisesRegex(loader.SnapshotError, "missing pin field"):
            loader.load_catalog(self.root)

    def test_lc_10_snapshot_card_missing_source_sha256(self):
        """LC-10 is code-only."""
        self.change_catalog(lambda c: c["cards"][0].pop("source_sha256"))
        with self.assertRaisesRegex(loader.SnapshotError, "source_sha256"):
            loader.load_catalog(self.root)

    def test_lc_11_snapshot_source_url_without_pin(self):
        self.change_catalog(lambda c: c["cards"][0].update(source_url=c["cards"][0]["markdown_url"]))
        with self.assertRaisesRegex(loader.SnapshotError, "source_url"):
            loader.load_catalog(self.root)

    def test_lc_14_default_composed_url_without_request(self):
        card = self.catalog["cards"][0]
        entry = loader.source_entry(self.catalog, self.meta, card["id"])
        self.assertEqual(entry["source_url"], card["source_url"])
        self.assertTrue(loader.valid_source_url(entry["source_url"], self.meta["corpus-revision"]))
        self.assertEqual(entry["source_url"].split("/")[5], self.meta["corpus-revision"])

    def test_lc_18_offline_environment_makes_no_request(self):
        entry = loader.source_entry(self.catalog, self.meta, "principles")
        with patch.dict(os.environ, {"VERIFICATION_SKILLS_OFFLINE": "1"}), patch.object(loader, "request_bytes") as request:
            with self.assertRaises(loader.Unavailable) as caught:
                loader.fetch_source(entry, offline=False, timeout=1)
            self.assertEqual(caught.exception.result["reason"], "offline")
            request.assert_not_called()

    def test_lc_15_default_http_scheme_refused_before_request(self):
        entry = loader.source_entry(self.catalog, self.meta, "principles")
        entry["source_url"] = entry["source_url"].replace("https:", "http:")
        with patch.object(loader, "request_bytes") as request:
            with self.assertRaises(loader.Unavailable) as caught:
                loader.fetch_source(entry, offline=False, timeout=1)
            self.assertEqual(caught.exception.result["reason"], "refused-url")
            request.assert_not_called()
