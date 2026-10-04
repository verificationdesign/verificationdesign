"""Serial arXiv OAI-PMH retrieval with injectable transport and clocks."""

from __future__ import annotations

import datetime as dt
import email.utils
import http.client
import ssl
import sys
import time
import urllib.parse
import xml.etree.ElementTree as ET
from typing import Any

from research_tools.matching import match_phrases

OAI_HOST = "oaipmh.arxiv.org"
OAI_PATH = "/oai"
OAI_NS = "{http://www.openarchives.org/OAI/2.0/}"
ARXIV_NS = "{http://arxiv.org/OAI/arXiv/}"
USER_AGENT = "ai-research-scout/2.0 (mechanical arxiv discovery)"
# arXiv's Fastly edge answered 406 to http.client's default request shape when the
# window ended within about two days of today (probed 2026-10-04). Two changes together
# make it pass, matching curl's observed shape: an explicit TLS context (unlike the
# stdlib default helper it leaves post_handshake_auth off; ALPN http/1.1 is set
# explicitly so the shape does not depend on the interpreter's default) and request
# headers that send "Accept: */*" without the implicit "Accept-Encoding: identity".
REQUEST_HEADERS = {"User-Agent": USER_AGENT, "Accept": "*/*"}
ALPN_PROTOCOLS = ["http/1.1"]
MIN_DELAY_SECONDS = 10.0
MAX_OAI_PAGES_PER_CATEGORY = 20
MAX_RETRY_AFTER_SECONDS = 300.0


class HTTPStatusError(Exception):
    def __init__(self, status: int, reason: str, headers: http.client.HTTPMessage) -> None:
        super().__init__(f"HTTP {status} {reason}".strip())
        self.status = status
        self.headers = headers


class OAIError(Exception):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"OAI {code}: {message}".strip())
        self.code = code


def ssl_context() -> ssl.SSLContext:
    """Explicit TLS context: ALPN http/1.1, post_handshake_auth left at its False default.

    The stdlib's HTTPSConnection default helper enables post_handshake_auth; the arXiv edge
    accepted the handshake only in the probe modes that did not (explicit context or TLS 1.2).
    """
    context = ssl.create_default_context()
    context.set_alpn_protocols(ALPN_PROTOCOLS)
    return context


class OAIClient:
    def __init__(self, delay_seconds: float, timeout: float, *, transport=None,
                 monotonic=time.monotonic, sleep=time.sleep, now=None) -> None:
        self.monotonic = monotonic
        self.sleep = sleep
        self.now = now if now is not None else lambda: dt.datetime.now(dt.timezone.utc)
        self._custom_transport = transport is not None
        self.transport = transport if transport is not None else self._transport
        self.delay_seconds = delay_seconds
        self.timeout = timeout
        self.last_request_at: float | None = None
        self.connection: http.client.HTTPSConnection | None = None

    def close(self) -> None:
        if self.connection is not None:
            self.connection.close()
            self.connection = None

    def get(self, params: dict[str, str]) -> bytes:
        self.wait_until_allowed()
        query = urllib.parse.urlencode(params)
        path = f"{OAI_PATH}?{query}"
        if self._custom_transport:
            self.last_request_at = self.monotonic()
        try:
            status, reason, headers, payload = self.transport(path, dict(REQUEST_HEADERS))
        except Exception:
            self.close()
            raise
        if status != 200:
            if status >= 500:
                self.close()
            raise HTTPStatusError(status, reason, headers)
        return payload

    def _transport(self, path, headers):
        if self.connection is None:
            self.connection = http.client.HTTPSConnection(
                OAI_HOST, timeout=self.timeout, context=ssl_context())
        # putrequest instead of request(): skip the implicit "Accept-Encoding: identity"
        # header, which the edge rejects together with a missing Accept header.
        self.connection.putrequest("GET", path, skip_accept_encoding=True)
        for name, value in headers.items():
            self.connection.putheader(name, value)
        self.connection.endheaders()
        # Preserve the legacy timestamp: after the request is sent, before response reading.
        self.last_request_at = self.monotonic()
        response = self.connection.getresponse()
        return response.status, response.reason, response.headers, response.read()

    def wait_until_allowed(self) -> None:
        if self.last_request_at is None:
            return
        remaining = self.delay_seconds - (self.monotonic() - self.last_request_at)
        if remaining > 0:
            self.sleep(remaining)


def category_to_set(category: str) -> str:
    archive, _, subject = category.partition(".")
    if not subject:
        return archive
    return f"{archive}:{archive}:{subject}"


def collapse(value: str | None) -> str:
    return " ".join((value or "").split())


def parse_date(value: str | None) -> dt.date | None:
    if not value:
        return None
    text = value.strip()
    for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%SZ"):
        try:
            return dt.datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    return None


def retry_after_seconds(headers: Any, now: dt.datetime) -> float | None:
    """Seconds to wait per a Retry-After header, capped; None when absent or unparseable."""
    value = headers.get("Retry-After") if headers else None
    if not value:
        return None
    seconds: float | None = None
    try:
        seconds = float(value)
    except (TypeError, ValueError):
        try:
            parsed = email.utils.parsedate_to_datetime(value)
        except (TypeError, ValueError):
            return None
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=dt.timezone.utc)
        seconds = (parsed - now).total_seconds()
    return min(max(seconds, 0.0), MAX_RETRY_AFTER_SECONDS)


def retry_delay(attempt: int, retry_sleep: float) -> float:
    return retry_sleep * (2**attempt)


def oai_get(client: OAIClient, params: dict[str, str], retries: int, retry_sleep: float) -> ET.Element:
    attempt = 0
    while True:
        try:
            payload = client.get(params)
            break
        except HTTPStatusError as exc:
            if exc.status == 429:
                raise
            if exc.status != 503 or attempt >= retries:
                raise
            delay = retry_after_seconds(exc.headers, client.now()) or retry_delay(attempt, retry_sleep)
            print(f"  ! HTTP {exc.status}; backing off for {delay:.0f}s before retry", file=sys.stderr)
            client.sleep(delay)
            attempt += 1
        except (OSError, http.client.HTTPException) as exc:
            # TimeoutError, ConnectionResetError and RemoteDisconnected all land here;
            # the client has already closed the connection, so the retry reconnects.
            if attempt >= retries:
                raise
            delay = retry_delay(attempt, retry_sleep)
            print(f"  ! request failed ({exc!r}); backing off for {delay:.0f}s before retry", file=sys.stderr)
            client.sleep(delay)
            attempt += 1
    root = ET.fromstring(payload)
    error = root.find(f"{OAI_NS}error")
    if error is not None:
        code = error.get("code", "unknown")
        if code == "noRecordsMatch":
            return root
        raise OAIError(code, (error.text or "").strip())
    return root


def arxiv_url(arxiv_id: str) -> str:
    return f"https://arxiv.org/abs/{arxiv_id}"


def parse_record(record: ET.Element) -> dict[str, Any] | None:
    header = record.find(f"{OAI_NS}header")
    metadata = record.find(f"{OAI_NS}metadata")
    if header is None or metadata is None:
        return None
    if (header.get("status") or "").strip() == "deleted":
        return None
    datestamp = parse_date(header.findtext(f"{OAI_NS}datestamp"))

    arxiv = metadata.find(f"{ARXIV_NS}arXiv")
    if arxiv is None:
        return None

    arxiv_id = (arxiv.findtext(f"{ARXIV_NS}id") or "").strip()
    if not arxiv_id:
        return None
    title = collapse(arxiv.findtext(f"{ARXIV_NS}title"))
    summary = collapse(arxiv.findtext(f"{ARXIV_NS}abstract"))
    created = parse_date(arxiv.findtext(f"{ARXIV_NS}created"))
    updated = parse_date(arxiv.findtext(f"{ARXIV_NS}updated"))
    categories_text = arxiv.findtext(f"{ARXIV_NS}categories") or ""
    categories = [item for item in categories_text.split() if item]

    authors: list[str] = []
    for author in arxiv.findall(f"{ARXIV_NS}authors/{ARXIV_NS}author"):
        forenames = collapse(author.findtext(f"{ARXIV_NS}forenames"))
        keyname = collapse(author.findtext(f"{ARXIV_NS}keyname"))
        full = " ".join(part for part in (forenames, keyname) if part)
        if not full:
            full = collapse(author.findtext(f"{ARXIV_NS}suffix"))
        if full:
            authors.append(full)

    return {
        "id": arxiv_id,
        "title": title,
        "summary": summary,
        "authors": authors,
        "categories": categories,
        "created": created,
        "updated": updated,
        "datestamp": datestamp,
    }


def harvest_category(
    client: OAIClient,
    category: str,
    start_date: dt.date,
    end_date: dt.date,
    max_results: int,
    retries: int,
    retry_sleep: float,
    anchors: list[str],
    topic_phrases: list[str],
) -> tuple[list[dict[str, Any]], bool]:
    """Return matched records and whether --max-per-category stopped the read early."""
    params: dict[str, str] = {
        "verb": "ListRecords",
        "set": category_to_set(category),
        "from": start_date.isoformat(),
        "until": end_date.isoformat(),
        "metadataPrefix": "arXiv",
    }
    output: list[dict[str, Any]] = []
    pages = 0
    while True:
        pages += 1
        if pages > MAX_OAI_PAGES_PER_CATEGORY:
            raise OAIError(
                "localPageLimit",
                f"{category} exceeded {MAX_OAI_PAGES_PER_CATEGORY} OAI pages; narrow the window",
            )
        root = oai_get(client, params, retries, retry_sleep)
        list_records = root.find(f"{OAI_NS}ListRecords")
        if list_records is None:
            break
        for record in list_records.findall(f"{OAI_NS}record"):
            entry = parse_record(record)
            if entry is None:
                continue
            haystack = f"{entry['title']} {entry['summary']}"
            anchor_matches = match_phrases(haystack, anchors) if anchors else []
            topic_matches = match_phrases(haystack, topic_phrases)
            if anchors and not anchor_matches:
                continue
            if not topic_matches:
                continue
            entry["matched_anchors"] = anchor_matches
            entry["matched_topics"] = topic_matches
            output.append(entry)
            if len(output) >= max_results:
                break
        if len(output) >= max_results:
            print(f"  ! {category}: stopped at --max-per-category {max_results}; later matches in the window were not read", file=sys.stderr)
            return output, True
        token_element = list_records.find(f"{OAI_NS}resumptionToken")
        if token_element is None or not (token_element.text or "").strip():
            break
        params = {
            "verb": "ListRecords",
            "resumptionToken": token_element.text.strip(),
        }
    return output, False


