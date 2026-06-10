#!/usr/bin/env python3
"""Mechanical arXiv discovery via OAI-PMH for the research notes.

This script harvests arXiv metadata via the OAI-PMH ListRecords interface,
filters client-side against anchor and topic phrases from the scout config,
and emits a markdown artifact for human triage. Classification and research
judgment happen after this output is reviewed.

Window semantics: the --start-date and --end-date arguments map to OAI-PMH
from and until, which select records whose metadata datestamp falls inside
the window. A record may appear because it was newly submitted in the
window, replaced by a new version, or had its bibliographic metadata
corrected. Each output entry prints the OAI datestamp alongside the arXiv
Created and Updated fields so triage can tell the cases apart.

anchor_phrases in the scout config become required client-side filters: a
record must contain at least one anchor phrase in its title or abstract to
be kept. topic phrases (keyword groups) follow the same client-side match,
and a record must hit at least one of them too.
"""

from __future__ import annotations

import argparse
import datetime as dt
import email.utils
import http.client
import json
import sys
import time
import urllib.error
import urllib.parse
import xml.etree.ElementTree as ET
from collections import OrderedDict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = ROOT / "research" / "scouts" / "config.json"
DEFAULT_OUTDIR = ROOT / "research" / "scouts"
OAI_HOST = "oaipmh.arxiv.org"
OAI_PATH = "/oai"
OAI_NS = "{http://www.openarchives.org/OAI/2.0/}"
ARXIV_NS = "{http://arxiv.org/OAI/arXiv/}"
USER_AGENT = "ai-research-scout/2.0 (mechanical arxiv discovery)"
MIN_DELAY_SECONDS = 10.0
MAX_OAI_PAGES_PER_CATEGORY = 20


class HTTPStatusError(Exception):
    def __init__(self, status: int, reason: str, headers: http.client.HTTPMessage) -> None:
        super().__init__(f"HTTP {status} {reason}".strip())
        self.status = status
        self.headers = headers


class OAIError(Exception):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"OAI {code}: {message}".strip())
        self.code = code


class OAIClient:
    def __init__(self, delay_seconds: float, timeout: float) -> None:
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
        if self.connection is None:
            self.connection = http.client.HTTPSConnection(OAI_HOST, timeout=self.timeout)
        try:
            self.connection.request("GET", path, headers={"User-Agent": USER_AGENT})
            self.last_request_at = time.monotonic()
            response = self.connection.getresponse()
            payload = response.read()
        except Exception:
            self.close()
            raise
        if response.status != 200:
            if response.status >= 500:
                self.close()
            raise HTTPStatusError(response.status, response.reason, response.headers)
        return payload

    def wait_until_allowed(self) -> None:
        if self.last_request_at is None:
            return
        remaining = self.delay_seconds - (time.monotonic() - self.last_request_at)
        if remaining > 0:
            time.sleep(remaining)


def load_config(
    path: Path,
) -> tuple[OrderedDict[str, str], OrderedDict[str, list[str]], list[str]]:
    raw = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=OrderedDict)
    categories = OrderedDict((str(k), str(v)) for k, v in raw["categories"].items())
    groups = OrderedDict((str(k), [str(item) for item in v]) for k, v in raw["keyword_groups"].items())
    anchors = [str(item) for item in raw.get("anchor_phrases", [])]
    return categories, groups, anchors


def select_keys(all_keys: list[str], selected: str | None, label: str) -> list[str]:
    if not selected:
        return all_keys
    wanted = [item.strip() for item in selected.split(",") if item.strip()]
    unknown = sorted(set(wanted) - set(all_keys))
    if unknown:
        raise SystemExit(f"unknown {label}: {', '.join(unknown)}")
    return wanted


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


def retry_after_seconds(headers: Any) -> float | None:
    value = headers.get("Retry-After") if headers else None
    if not value:
        return None
    try:
        return max(float(value), 0.0)
    except ValueError:
        parsed = email.utils.parsedate_to_datetime(value)
        if parsed is None:
            return None
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=dt.timezone.utc)
        return max((parsed - dt.datetime.now(dt.timezone.utc)).total_seconds(), 0.0)


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
            delay = retry_after_seconds(exc.headers) or retry_delay(attempt, retry_sleep)
            print(f"  ! HTTP {exc.status}; backing off for {delay:.0f}s before retry", file=sys.stderr)
            time.sleep(delay)
            attempt += 1
        except (TimeoutError, urllib.error.URLError) as exc:
            if attempt >= retries:
                raise
            delay = retry_delay(attempt, retry_sleep)
            print(f"  ! request timed out ({exc}); backing off for {delay:.0f}s before retry", file=sys.stderr)
            time.sleep(delay)
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


def match_phrases(text: str, phrases: list[str]) -> list[str]:
    matched: list[str] = []
    seen: set[str] = set()
    haystack = text.lower()
    for phrase in phrases:
        key = phrase.lower()
        if key in seen:
            continue
        if key in haystack:
            matched.append(phrase)
            seen.add(key)
    return matched


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
) -> list[dict[str, Any]]:
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
            break
        token_element = list_records.find(f"{OAI_NS}resumptionToken")
        if token_element is None or not (token_element.text or "").strip():
            break
        params = {
            "verb": "ListRecords",
            "resumptionToken": token_element.text.strip(),
        }
    return output


def load_ledger(path: Path | None) -> set[str]:
    if path is None or not path.exists():
        return set()
    return {line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()}


def append_ledger(path: Path | None, ids: list[str]) -> None:
    if path is None or not ids:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        for arxiv_id in ids:
            handle.write(f"{arxiv_id}\n")


def format_authors(authors: list[str], limit: int = 6) -> str:
    if not authors:
        return "(unknown)"
    if len(authors) <= limit:
        return ", ".join(authors)
    return f"{', '.join(authors[:limit])}, +{len(authors) - limit} more"


def excerpt(summary: str, limit: int = 360) -> str:
    if len(summary) <= limit:
        return summary
    return f"{summary[:limit].rstrip()}..."


def format_date(value: dt.date | None) -> str:
    return value.isoformat() if value else "(unknown)"


def entry_block(record: dict[str, Any], indent: str = "  ") -> list[str]:
    lines = [
        f"- {record['title']}",
        f"{indent}- arXiv: [{record['id']}]({arxiv_url(record['id'])})",
        f"{indent}- Created: {format_date(record['created'])}",
        f"{indent}- Updated: {format_date(record['updated'])}",
        f"{indent}- OAI datestamp: {format_date(record['datestamp'])}",
        f"{indent}- Categories: {', '.join(record['categories']) or '(none)'}",
        f"{indent}- Authors: {format_authors(record['authors'])}",
    ]
    if "matched_anchors" in record:
        lines.append(f"{indent}- Matched anchors: {', '.join(record['matched_anchors']) or '(none)'}")
    lines.append(f"{indent}- Matched keywords: {', '.join(record.get('matched_topics', [])) or '(none)'}")
    lines.append(f"{indent}- Abstract excerpt: {excerpt(record['summary'])}")
    return lines


def render_markdown(
    end_date: dt.date,
    start_date: dt.date,
    per_category: OrderedDict[str, list[dict[str, Any]]],
    deduped: OrderedDict[str, dict[str, Any]],
    new_ids: list[str],
    skipped_count: int,
    ledger: Path | None,
    selected_categories: list[str],
    selected_groups: list[str],
    anchors: list[str],
) -> str:
    new_id_set = set(new_ids)
    lines: list[str] = [
        f"# Scout {end_date.isoformat()}",
        "",
        f"Query window: {start_date.isoformat()} to {end_date.isoformat()}",
        "Window semantics: OAI-PMH metadata datestamp, not original submission date",
        "Sources: arXiv OAI-PMH",
        f"Categories: {', '.join(selected_categories)}",
        f"Keyword groups: {', '.join(selected_groups)}",
        f"Anchor phrases: {', '.join(anchors) if anchors else '(none)'}",
    ]
    if ledger:
        lines.append(f"Ledger: {ledger} ({skipped_count} already-seen candidates suppressed)")
    lines.extend(
        [
            "",
            "## Review Queue",
            "",
            "Add judgment outside the mechanical generation step. Suggested labels: challenges, narrows, extends, operational technique, ignore.",
            "",
        ]
    )
    if not new_ids:
        lines.append("- (no new candidates this run)")
    for arxiv_id in new_ids:
        record = deduped[arxiv_id]
        lines.append(f"- [ ] {record['title']} ([arXiv:{arxiv_id}]({arxiv_url(arxiv_id)}))")
        lines.append("  - Label:")
        lines.append("  - Reason:")
        lines.append("")

    lines.append("## Deduped Candidates")
    if not new_ids:
        lines.append("- (no new candidates this run)")
    for arxiv_id in new_ids:
        record = deduped[arxiv_id]
        lines.append(f"- {record['title']} ([arXiv:{arxiv_id}]({arxiv_url(arxiv_id)}))")
        lines.append(f"  - Appeared in: {', '.join(record['appeared'])}")
        lines.extend(entry_block(record, indent="  ")[2:])
        lines.append("")

    lines.append("## Category Results")
    for category, records in per_category.items():
        lines.append("")
        lines.append(f"### Category: `{category}` (set `{category_to_set(category)}`)")
        fresh = [record for record in records if record["id"] in new_id_set]
        if not fresh:
            lines.append("- (no new results)")
        for record in fresh:
            lines.extend(entry_block(record))
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Mechanical arXiv scout via OAI-PMH. No judgment inside.")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--days", type=int, default=90, help="lookback window when --start-date is not set")
    parser.add_argument("--start-date", default=None, help="YYYY-MM-DD; overrides --days; OAI-PMH from")
    parser.add_argument("--end-date", default=None, help="YYYY-MM-DD; OAI-PMH until; defaults to today")
    parser.add_argument("--categories", default=None, help="comma-separated category keys")
    parser.add_argument("--groups", default=None, help="comma-separated keyword group keys")
    parser.add_argument("--max-per-category", type=int, default=200, help="cap on matched records per category")
    parser.add_argument("--retries", type=int, default=2, help="503/timeout retries per OAI request")
    parser.add_argument("--retry-sleep", type=float, default=60.0, help="base seconds for 503/timeout backoff without Retry-After")
    parser.add_argument("--timeout", type=float, default=60.0, help="seconds before an OAI request times out")
    parser.add_argument("--outdir", type=Path, default=DEFAULT_OUTDIR)
    parser.add_argument("--outfile", type=Path, default=None)
    parser.add_argument("--ledger", type=Path, default=None)
    parser.add_argument("--dry-run", action="store_true", help="print planned OAI requests without fetching")
    args = parser.parse_args()

    categories, groups, anchors = load_config(args.config)
    selected_categories = select_keys(list(categories.keys()), args.categories, "categories")
    selected_groups = select_keys(list(groups.keys()), args.groups, "groups")
    selected_phrases: list[str] = []
    seen_phrases: set[str] = set()
    for group in selected_groups:
        for phrase in groups[group]:
            key = phrase.lower()
            if key in seen_phrases:
                continue
            seen_phrases.add(key)
            selected_phrases.append(phrase)

    end_date = dt.date.fromisoformat(args.end_date) if args.end_date else dt.date.today()
    start_date = dt.date.fromisoformat(args.start_date) if args.start_date else end_date - dt.timedelta(days=args.days)
    if start_date > end_date:
        raise SystemExit("--start-date must be on or before --end-date")
    if args.max_per_category < 1:
        raise SystemExit("--max-per-category must be positive")
    if args.retries < 0:
        raise SystemExit("--retries must be non-negative")
    if args.retry_sleep < 1.0:
        raise SystemExit("--retry-sleep must be at least 1.0")
    if args.timeout < 10.0:
        raise SystemExit("--timeout must be at least 10.0")

    if args.dry_run:
        for category in selected_categories:
            params = {
                "verb": "ListRecords",
                "set": category_to_set(category),
                "from": start_date.isoformat(),
                "until": end_date.isoformat(),
                "metadataPrefix": "arXiv",
            }
            url = f"https://{OAI_HOST}{OAI_PATH}?{urllib.parse.urlencode(params)}"
            print(f"{category}: {url}")
        return 0

    seen_before = load_ledger(args.ledger)
    per_category: OrderedDict[str, list[dict[str, Any]]] = OrderedDict()
    deduped: OrderedDict[str, dict[str, Any]] = OrderedDict()
    client = OAIClient(delay_seconds=MIN_DELAY_SECONDS, timeout=args.timeout)

    try:
        for category in selected_categories:
            print(f"harvesting {category} ...", file=sys.stderr)
            records = harvest_category(
                client,
                category,
                start_date,
                end_date,
                args.max_per_category,
                args.retries,
                args.retry_sleep,
                anchors,
                selected_phrases,
            )
            per_category[category] = records
            for record in records:
                arxiv_id = record["id"]
                if arxiv_id in deduped:
                    deduped[arxiv_id]["appeared"].append(category)
                else:
                    copy = dict(record)
                    copy["appeared"] = [category]
                    deduped[arxiv_id] = copy
    except HTTPStatusError as exc:
        if exc.status == 429:
            print("  ! rate limited by arXiv (HTTP 429); stop and retry later", file=sys.stderr)
        else:
            print(f"  ! request failed: {exc}", file=sys.stderr)
        return 1
    except OAIError as exc:
        print(f"  ! OAI error: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:  # noqa: BLE001
        print(f"  ! request failed: {exc}", file=sys.stderr)
        return 1
    finally:
        client.close()

    new_ids = [arxiv_id for arxiv_id in deduped if arxiv_id not in seen_before]
    skipped_count = len(deduped) - len(new_ids)
    output = render_markdown(
        end_date,
        start_date,
        per_category,
        deduped,
        new_ids,
        skipped_count,
        args.ledger,
        selected_categories,
        selected_groups,
        anchors,
    )

    outfile = args.outfile or args.outdir / f"scout-{end_date.isoformat()}.md"
    outfile.parent.mkdir(parents=True, exist_ok=True)
    outfile.write_text(output, encoding="utf-8")
    append_ledger(args.ledger, new_ids)
    print(f"wrote {outfile}: {len(new_ids)} new candidates ({skipped_count} suppressed by ledger)", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
