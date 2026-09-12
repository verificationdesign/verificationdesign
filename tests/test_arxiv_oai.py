"""Offline OAI tests: captured records and explicitly synthetic envelopes/errors."""

import contextlib
import datetime as dt
import io
from pathlib import Path
import unittest
from unittest.mock import patch
import urllib.parse
import xml.etree.ElementTree as ET

from research_tools import arxiv_oai as oai

FIXTURES = Path(__file__).parent / "fixtures"
SAMPLE = (FIXTURES / "oai-listrecords-sample.xml").read_bytes()
NOW = dt.datetime(2026, 9, 12, tzinfo=dt.timezone.utc)
DAY = dt.date(2026, 9, 8)


def envelope(*, token=None, deleted=False):
    """Synthetic pagination/deletion envelope around unmodified captured record bodies."""
    root = ET.fromstring(SAMPLE)
    records = root.find(f"{oai.OAI_NS}ListRecords")
    if token is not None:
        ET.SubElement(records, f"{oai.OAI_NS}resumptionToken").text = token
    if deleted:
        records[0].find(f"{oai.OAI_NS}header").set("status", "deleted")
    return ET.tostring(root)


def ok(body=SAMPLE):
    return 200, "OK", {}, body


class FakeIO:
    """Scripted transport plus a fixed starting monotonic clock advanced only by sleep."""
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []
        self.sleeps = []
        self.time = 100.0

    def monotonic(self):
        return self.time

    def sleep(self, seconds):
        self.sleeps.append(seconds)
        self.time += seconds

    def transport(self, path, headers):
        self.calls.append((path, headers))
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response

    def client(self):
        return oai.OAIClient(10, 60, transport=self.transport,
                             monotonic=self.monotonic, sleep=self.sleep, now=lambda: NOW)


def harvest(client, max_results=100, anchors=None, topics=None):
    return oai.harvest_category(client, "cs.AI", DAY, DAY, max_results, 2, 60,
                                [] if anchors is None else anchors,
                                ["evaluation", "prediction"] if topics is None else topics)


class OAITests(unittest.TestCase):
    def setUp(self):
        self.guard = patch("http.client.HTTPSConnection", side_effect=AssertionError("live OAI access"))
        self.guard.start()
        self.addCleanup(self.guard.stop)
        guard = patch("time.sleep", side_effect=AssertionError("real sleep"))
        guard.start()
        self.addCleanup(guard.stop)
        self.stderr = io.StringIO()
        redirect = contextlib.redirect_stderr(self.stderr)
        redirect.__enter__()
        self.addCleanup(redirect.__exit__, None, None, None)

    def get(self, fake, retries=2, retry_sleep=60):
        return oai.oai_get(fake.client(), {"verb": "ListRecords"}, retries, retry_sleep)

    def test_default_transport_guard(self):
        """Removing the default HTTPS transport makes the live-access guard stop tripping."""
        with self.assertRaisesRegex(AssertionError, "live OAI access"):
            oai.OAIClient(10, 60).get({"verb": "ListRecords"})

    def test_dropped_connection(self):
        """Removing the OSError retry branch prevents recovery within budget."""
        fake = FakeIO([ConnectionResetError("dropped"), ok()])
        self.assertEqual(self.get(fake).tag, f"{oai.OAI_NS}OAI-PMH")
        self.assertEqual(fake.sleeps, [60])
        self.assertEqual(len(fake.calls), 2)

    def test_exhausted_connections(self):
        """Removing attempt >= retries permits a forbidden fourth request."""
        fake = FakeIO([ConnectionResetError("dropped")] * 3)
        with self.assertRaises(ConnectionResetError):
            self.get(fake)
        self.assertEqual(fake.sleeps, [60, 120])
        self.assertEqual(len(fake.calls), 3)

    def test_malformed_retry_after(self):
        """Removing Retry-After fallback loses exponential delays (synthetic 503s)."""
        fake = FakeIO([(503, "Unavailable", {"Retry-After": "nonsense"}, b"")] * 2 + [ok()])
        self.get(fake)
        self.assertEqual(fake.sleeps, [60, 120])
        self.assertEqual(len(fake.calls), 3)

    def test_missing_retry_after(self):
        """Removing absent-header fallback loses backoff (synthetic 503)."""
        fake = FakeIO([(503, "Unavailable", {}, b""), ok()])
        self.get(fake)
        self.assertEqual(fake.sleeps, [60])
        self.assertEqual(len(fake.calls), 2)

    def test_numeric_retry_after(self):
        """Removing numeric Retry-After parsing ignores the synthetic 503 header."""
        fake = FakeIO([(503, "Unavailable", {"Retry-After": "45"}, b""), ok()])
        self.get(fake)
        self.assertEqual(fake.sleeps, [45])

    def test_date_retry_after(self):
        """Removing the injected wall-clock subtraction breaks date-form Retry-After."""
        fake = FakeIO([(503, "Unavailable", {"Retry-After": "Sat, 12 Sep 2026 00:01:30 GMT"}, b""), ok()])
        self.get(fake)
        self.assertEqual(fake.sleeps, [90])

    def test_retry_after_capped(self):
        """Removing min(..., MAX_RETRY_AFTER_SECONDS) permits waits beyond 300."""
        for value in ("999", "Sat, 12 Sep 2026 01:00:00 GMT"):
            with self.subTest(value=value):
                fake = FakeIO([(503, "Unavailable", {"Retry-After": value}, b""), ok()])
                self.get(fake)
                self.assertEqual(fake.sleeps, [300])

    def test_zero_retry_after_retains_fallback(self):
        """Replacing legacy 'or retry_delay' changes zero/past Retry-After behavior."""
        for value in ("0", "-1", "Fri, 11 Sep 2026 23:59:00 GMT"):
            fake = FakeIO([(503, "Unavailable", {"Retry-After": value}, b""), ok()])
            self.get(fake)
            self.assertEqual(fake.sleeps, [60])

    def test_rate_limit_immediate(self):
        """Removing the immediate 429 raise allows retries or sleeps (synthetic 429)."""
        fake = FakeIO([(429, "Too Many Requests", {"Retry-After": "120"}, b"")])
        with self.assertRaises(oai.HTTPStatusError) as caught:
            self.get(fake)
        self.assertEqual(caught.exception.status, 429)
        self.assertEqual(fake.sleeps, [])
        self.assertEqual(len(fake.calls), 1)

    def test_http_exhaustion_and_nonretryable(self):
        """Removing the status/budget check retries non-503s or exhausted 503s."""
        for status, budget in ((503, 0), (500, 2), (404, 2)):
            fake = FakeIO([(status, "failure", {}, b"")])
            with self.assertRaises(oai.HTTPStatusError):
                self.get(fake, retries=budget)
            self.assertEqual(fake.sleeps, [])
            self.assertEqual(len(fake.calls), 1)

    def test_spacing(self):
        """Removing wait_until_allowed or its remaining > 0 guard changes spacing."""
        fake = FakeIO([ok()] * 4)
        client = fake.client()
        for _ in range(3):
            client.get({"verb": "ListRecords"})
        fake.time += 11
        client.get({"verb": "ListRecords"})
        self.assertEqual(fake.sleeps, [10, 10])
        self.assertEqual(len(fake.calls), 4)
        self.assertEqual(fake.calls[0][1], {"User-Agent": oai.USER_AGENT})

    def test_resumption_token(self):
        """Removing token-only continuation params fails this synthetic pagination case."""
        fake = FakeIO([ok(envelope(token="next token/+")), ok()])
        records, capped = harvest(fake.client())
        self.assertEqual([r["id"] for r in records], ["2609.01788", "2609.02746"] * 2)
        self.assertFalse(capped)
        params = [urllib.parse.parse_qs(urllib.parse.urlsplit(path).query) for path, _ in fake.calls]
        self.assertEqual(params, [
            {"verb": ["ListRecords"], "set": ["cs:cs:AI"], "from": ["2026-09-08"],
             "until": ["2026-09-08"], "metadataPrefix": ["arXiv"]},
            {"verb": ["ListRecords"], "resumptionToken": ["next token/+"]},
        ])
        self.assertEqual(fake.sleeps, [10])

    def test_deleted(self):
        """Removing deleted-header rejection retains a synthetic deleted record."""
        fake = FakeIO([ok(envelope(deleted=True))])
        records, capped = harvest(fake.client())
        self.assertEqual([r["id"] for r in records], ["2609.02746"])
        self.assertFalse(capped)

    def test_no_records(self):
        """Removing noRecordsMatch special handling rejects this synthetic error envelope."""
        root = ET.fromstring((FIXTURES / "oai-norecordsmatch.xml").read_bytes())
        error = root.find(f"{oai.OAI_NS}error")
        error.set("code", "noRecordsMatch")
        error.text = "No records match the requested window."
        fake = FakeIO([ok(ET.tostring(root))])
        self.assertEqual(harvest(fake.client()), ([], False))
        self.assertEqual(len(fake.calls), 1)

    def test_real_bad_argument(self):
        """Removing OAI error propagation accepts the supplied badArgument capture."""
        fake = FakeIO([ok((FIXTURES / "oai-norecordsmatch.xml").read_bytes())])
        with self.assertRaises(oai.OAIError) as caught:
            self.get(fake)
        self.assertEqual(caught.exception.code, "badArgument")
        self.assertIn("until date too late", str(caught.exception))

    def test_raw_page_cap(self):
        """Removing the raw-page guard requests page 21 instead of raising localPageLimit."""
        fake = FakeIO([ok(envelope(token="more"))] * 20)
        with self.assertRaises(oai.OAIError) as caught:
            harvest(fake.client(), topics=["never present"])
        self.assertEqual(caught.exception.code, "localPageLimit")
        self.assertEqual(len(fake.calls), 20)
        self.assertEqual(fake.sleeps, [10] * 19)

    def test_matched_record_cap(self):
        """Removing the matched-record cap reads the second record instead of marking early stop."""
        fake = FakeIO([ok(envelope(token="more"))])
        records, capped = harvest(fake.client(), max_results=1)
        self.assertTrue(capped)
        self.assertEqual([r["id"] for r in records], ["2609.01788"])
        self.assertIn("stopped at --max-per-category 1", self.stderr.getvalue())
        self.assertEqual(len(fake.calls), 1)

    def test_anchor_and_topic_filters(self):
        """Removing either required match check admits the excluded captured records."""
        fake = FakeIO([ok()])
        records, capped = harvest(fake.client(), anchors=["llm"], topics=["evaluation"])
        self.assertEqual([r["id"] for r in records], ["2609.01788"])
        self.assertEqual(records[0]["matched_anchors"], ["llm"])
        self.assertEqual(records[0]["matched_topics"], ["evaluation"])
        self.assertFalse(capped)
        self.assertEqual(harvest(FakeIO([ok()]).client(), topics=["never present"]), ([], False))

    def test_parse_records(self):
        """Removing any parsed field fails independently transcribed real-record values."""
        elements = ET.fromstring(SAMPLE).findall(f"{oai.OAI_NS}ListRecords/{oai.OAI_NS}record")
        expected = [
            {
                "id": "2609.01788",
                "title": "VakyArth: Evaluating Pragmatic Competence in LLMs across Indic Languages",
                "authors": ["Usneek Singh", "Poorvaja Veera Balaji Kumar", "Parth Nanda", "Anand Madhusoodanan", "Geyang Guo", "Wei Xu", "Junyi Jessy Li"],
                "categories": ["cs.CL", "cs.AI"],
                "created": dt.date(2026, 9, 1), "updated": DAY, "datestamp": DAY,
                "summary": "Real-world communication often requires pragmatic reasoning: interpreting meanings implied through context and cultural convention rather than stated literally. Existing pragmatic evaluation remains largely limited to English and high-resource languages, leaving Indic languages unexplored despite their linguistic and cultural diversity. We introduce VakyArth, the first pragmatic benchmark for Indic languages, designed as a diagnostic evaluation covering Hindi, Punjabi, Tamil, and Malayalam. VakyArth evaluates models across five phenomena: deixis, speech acts, implicature, social pragmatics, and coherence; through multiple-choice questions, natural language inference, and translation, with all items authored by native speakers. Across multilingual large language models (LLMs) of varying families and sizes, we find consistent failures on pragmatic meanings rooted in Indic linguistic and cultural conventions. Our analysis shows systematic differences across languages and tasks: MCQ accuracy exceeds NLI accuracy in all model-language combinations, translation performance does not reliably track pragmatic understanding, and Indo-Aryan languages show a translation advantage over Dravidian languages. We further show that automatic translation metrics can miss fluent but pragmatically unfaithful outputs, especially for implicature and deixis.",
            },
            {
                "id": "2609.02746",
                "title": "HiPoly: a hierarchical polymer-native AI framework for property prediction and generative design",
                "authors": ["Ge Sun", "Gervasio Zaldivar", "Yuan Tian", "Gustavo Perez Lemus", "Juhae Park", "Daryna Safarian", "Ming Han", "Juan J. de Pablo"],
                "categories": ["physics.chem-ph", "cond-mat.mtrl-sci", "cs.AI", "cs.LG", "physics.comp-ph"],
                "created": dt.date(2026, 9, 2), "updated": DAY, "datestamp": DAY,
                "summary": "Polymeric materials are central to modern technologies, with applications ranging from energy to health and transportation. Although AI has made significant advances in materials discovery, the hierarchical structure of polymers across multiple length scales makes them inherently difficult to represent in a unified and physically meaningful way. Here we introduce HiPoly, a polymer-native AI framework that processes complete polymer descriptions through a three-level hierarchical graph architecture built on the G2RINS representation. HiPoly encodes stochastic inter-monomer connectivity, composition, and molecular weight directly within its architecture, using physically motivated design principles that mirror the multi-scale nature of polymeric systems. The framework establishes an end-to-end AI-driven workflow from experimental formulation data to property prediction, generative molecular design, and physics-based validation through molecular simulations, all unified by a single polymer representation. We demonstrate state-of-the-art prediction accuracy for thermophysical properties of multi-component polymer systems, with ablation studies confirming that each hierarchical design choice contributes independently to model performance. As an example, the generative design pathway is applied here to the discovery of sustainable alternatives to persistent fluorinated polymers, where it is possible to identify and independently validate PFAS-free candidates with target surface-energy properties. This work demonstrates how polymer-native AI can accelerate discovery by linking representation, prediction, and design across complex polymer chemistries.",
            },
        ]
        self.assertEqual([oai.parse_record(r) for r in elements], expected)
