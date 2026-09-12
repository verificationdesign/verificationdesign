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


class ByteIdentityTests(unittest.TestCase):
    def test_audit_loader_byte_identical(self):
        self.assertEqual((DESIGN / "scripts/load_catalog.py").read_bytes(), (AUDIT / "scripts/load_catalog.py").read_bytes())


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
