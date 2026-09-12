"""Pinned retrieval contract, using only a loopback HTTP server for transport."""
import copy
import hashlib
import http.server
import importlib.util
import json
import os
from pathlib import Path
import shutil
import socket
import tempfile
import threading
import time
import unittest
from unittest.mock import patch
import sys
sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parents[2]
DESIGN = ROOT / "skills/verification-design"
AUDIT = ROOT / "skills/verification-audit"
spec = importlib.util.spec_from_file_location("retrieval_loader", DESIGN / "scripts/load_catalog.py")
loader = importlib.util.module_from_spec(spec)
spec.loader.exec_module(loader)


class SnapshotTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name) / "verification-design"
        shutil.copytree(DESIGN, self.root)
        self.catalog, self.meta = loader.load_catalog(self.root)

    def change_catalog(self, change, rehash=True):
        value = copy.deepcopy(self.catalog)
        change(value)
        raw = (json.dumps(value) + "\n").encode()
        (self.root / "assets/catalog.json").write_bytes(raw)
        if rehash:
            skill = self.root / "SKILL.md"
            skill.write_text(skill.read_text().replace(self.meta["catalog-sha256"], hashlib.sha256(raw).hexdigest()))

    def test_snapshot_loads(self):
        self.assertEqual(len(self.catalog["cards"]), 17)
        self.assertEqual(self.catalog["revision"], self.meta["corpus-revision"])

    def test_snapshot_wrong_revision(self):
        self.change_catalog(lambda c: c.update(revision="0" * 40))
        with self.assertRaisesRegex(loader.SnapshotError, "revision mismatch"):
            loader.load_catalog(self.root)

    def test_snapshot_wrong_file_hash(self):
        self.change_catalog(lambda c: c.update(generated="changed"), rehash=False)
        with self.assertRaisesRegex(loader.SnapshotError, "file hash mismatch"):
            loader.load_catalog(self.root)

    def test_snapshot_missing_pin_field(self):
        path = self.root / "SKILL.md"
        path.write_text("\n".join(line for line in path.read_text().splitlines() if not line.startswith("  principles-sha256:")) + "\n")
        with self.assertRaisesRegex(loader.SnapshotError, "missing pin field"):
            loader.load_catalog(self.root)

    def test_snapshot_card_missing_source_sha256(self):
        self.change_catalog(lambda c: c["cards"][0].pop("source_sha256"))
        with self.assertRaisesRegex(loader.SnapshotError, "source_sha256"):
            loader.load_catalog(self.root)

    def test_snapshot_source_url_without_pin(self):
        self.change_catalog(lambda c: c["cards"][0].update(source_url=c["cards"][0]["markdown_url"]))
        with self.assertRaisesRegex(loader.SnapshotError, "source_url"):
            loader.load_catalog(self.root)

    def test_audit_loader_byte_identical(self):
        self.assertEqual((DESIGN / "scripts/load_catalog.py").read_bytes(), (AUDIT / "scripts/load_catalog.py").read_bytes())

    def test_default_composed_url_without_request(self):
        card = self.catalog["cards"][0]
        entry = loader.source_entry(self.catalog, self.meta, card["id"])
        self.assertEqual(entry["source_url"], card["source_url"])
        self.assertTrue(loader.valid_source_url(entry["source_url"], self.meta["corpus-revision"]))
        self.assertEqual(entry["source_url"].split("/")[5], self.meta["corpus-revision"])

    def test_offline_environment_makes_no_request(self):
        entry = loader.source_entry(self.catalog, self.meta, "principles")
        with patch.dict(os.environ, {"VERIFICATION_SKILLS_OFFLINE": "1"}), patch.object(loader, "request_bytes") as request:
            with self.assertRaises(loader.Unavailable) as caught:
                loader.fetch_source(entry, offline=False, timeout=1)
            self.assertEqual(caught.exception.result["reason"], "offline")
            request.assert_not_called()

    def test_default_http_scheme_refused_before_request(self):
        entry = loader.source_entry(self.catalog, self.meta, "principles")
        entry["source_url"] = entry["source_url"].replace("https:", "http:")
        with patch.object(loader, "request_bytes") as request:
            with self.assertRaises(loader.Unavailable) as caught:
                loader.fetch_source(entry, offline=False, timeout=1)
            self.assertEqual(caught.exception.result["reason"], "refused-url")
            request.assert_not_called()


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=args[2].root, **kwargs)

    def log_message(self, *args):
        pass

    def do_GET(self):
        self.server.requests.append(self.path)
        if self.server.mode == "drop":
            self.connection.shutdown(socket.SHUT_RDWR)
            self.connection.close()
            return
        if self.server.mode == "delay":
            time.sleep(0.2)
        if self.server.mode == "redirect":
            self.send_response(302)
            self.send_header("Location", "/mutable.md")
            self.end_headers()
            return
        try:
            super().do_GET()
        except (BrokenPipeError, ConnectionResetError):
            pass


class RetrievalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.tmp.cleanup)
        # A bind failure is an error, never a silent skip or a fake passing mock.
        cls.server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        cls.server.daemon_threads = True
        cls.addClassCleanup(cls.server.server_close)
        cls.server.root = cls.tmp.name
        cls.server.requests = []
        cls.server.mode = "ok"
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.addClassCleanup(cls.thread.join, 2)
        cls.addClassCleanup(cls.server.shutdown)
        cls.base = "http://127.0.0.1:" + str(cls.server.server_port)
        cls.catalog, cls.meta = loader.load_catalog()

    def setUp(self):
        self.server.requests.clear()
        self.server.mode = "ok"
        self.env = patch.dict(os.environ, {"VERIFICATION_SKILLS_OFFLINE": "0"})
        self.env.start()
        self.addCleanup(self.env.stop)
        self.body = b"A pinned source.\r\n\r\n"
        self.entry = loader.source_entry(self.catalog, self.meta, self.catalog["cards"][0]["id"], self.base)
        self.entry["source_sha256"] = hashlib.sha256(loader.normalize_body(self.body)).hexdigest()
        self.path = Path(self.tmp.name) / self.entry["source_url"].split(self.base + "/", 1)[1]
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_bytes(self.body)

    def unavailable(self, entry, reason, offline=False, timeout=1):
        with self.assertRaises(loader.Unavailable) as caught:
            loader.fetch_source(entry, offline=offline, timeout=timeout)
        self.assertEqual(caught.exception.result, {"unavailable": True, "source_url": entry["source_url"], "reason": reason})

    def test_fetch_accepted(self):
        self.assertEqual(loader.fetch_source(self.entry, offline=False, timeout=1), b"A pinned source.\n")
        self.assertEqual(len(self.server.requests), 1)

    def test_fetch_one_byte_change_hash_mismatch(self):
        self.path.write_bytes(self.body.replace(b"A", b"B", 1))
        self.unavailable(self.entry, "hash-mismatch")

    def test_fetch_404(self):
        self.path.unlink()
        self.unavailable(self.entry, "http-404")

    def test_fetch_dropped_connection(self):
        self.server.mode = "drop"
        self.unavailable(self.entry, "transport")

    def test_fetch_timeout(self):
        self.server.mode = "delay"
        self.unavailable(self.entry, "timeout", timeout=0.01)

    def refuse(self, url):
        entry = dict(self.entry, source_url=url)
        self.unavailable(entry, "refused-url")
        self.assertEqual(self.server.requests, [])

    def test_refuse_markdown_url_before_request(self):
        self.refuse(self.catalog["cards"][0]["markdown_url"])

    def test_refuse_html_url_before_request(self):
        self.refuse(self.catalog["cards"][0]["html_url"])

    def test_refuse_http_scheme_before_request(self):
        entry = loader.source_entry(self.catalog, self.meta, "principles")
        entry["source_url"] = entry["source_url"].replace("https:", "http:")
        self.unavailable(entry, "refused-url")
        self.assertEqual(self.server.requests, [])

    def test_refuse_other_host_before_request(self):
        self.refuse(self.entry["source_url"].replace("127.0.0.1", "localhost"))

    def test_refuse_other_sha_before_request(self):
        self.refuse(self.entry["source_url"].replace(self.meta["corpus-revision"], "0" * 40))

    def test_offline_mode(self):
        self.unavailable(self.entry, "offline", offline=True)
        self.assertEqual(self.server.requests, [])
        self.assertEqual(len(loader.load_catalog()[0]["cards"]), 17)

    def test_principles_accept(self):
        meta = dict(self.meta, **{"principles-sha256": hashlib.sha256(loader.normalize_body(self.body)).hexdigest()})
        entry = loader.source_entry(self.catalog, meta, "principles", self.base)
        path = Path(self.tmp.name) / entry["source_url"].split(self.base + "/", 1)[1]
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(self.body)
        self.assertEqual(entry["source_sha256"], meta["principles-sha256"])
        self.assertEqual(loader.fetch_source(entry, offline=False, timeout=1), loader.normalize_body(self.body))

    def test_principles_reject(self):
        entry = loader.source_entry(self.catalog, self.meta, "principles", self.base)
        path = Path(self.tmp.name) / entry["source_url"].split(self.base + "/", 1)[1]
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"changed principles")
        self.unavailable(entry, "hash-mismatch")

    def test_drift_different_revision_retains_snapshot(self):
        before = copy.deepcopy(self.catalog)
        (Path(self.tmp.name) / "catalog.json").write_text(json.dumps({"revision": "a" * 40}))
        result = loader.drift(self.catalog, live_url=self.base + "/catalog.json", timeout=1)
        self.assertEqual(result, {"pinned": self.meta["corpus-revision"], "live": "a" * 40, "newer_available": True})
        self.assertEqual(self.catalog, before)
        self.assertEqual(loader.load_catalog()[0], before)

    def test_redirect_is_not_followed(self):
        self.server.mode = "redirect"
        self.unavailable(self.entry, "http-302")
        self.assertEqual(len(self.server.requests), 1)


if __name__ == "__main__":
    unittest.main()
