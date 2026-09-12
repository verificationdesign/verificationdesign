"""Mechanical scout configuration, orchestration and markdown production."""

from __future__ import annotations

import datetime as dt
import sys
import urllib.parse
from collections import OrderedDict
from pathlib import Path
from typing import Any

from research_tools.profile import Profile, load_profile
from research_tools.arxiv_oai import (
    HTTPStatusError, OAIError, OAIClient, MIN_DELAY_SECONDS, OAI_HOST, OAI_PATH,
    arxiv_url, category_to_set, harvest_category,
)

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = ROOT / "research" / "scouts" / "config.json"
DEFAULT_OUTDIR = ROOT / "research" / "scouts"


def load_config(
    profile: Profile,
) -> tuple[
    OrderedDict[str, str],
    OrderedDict[str, list[str]],
    list[str],
    OrderedDict[str, dict[str, Any]],
]:
    categories = OrderedDict((str(k), str(v)) for k, v in profile.categories.items())
    groups = OrderedDict((str(k), [str(item) for item in v]) for k, v in profile.keyword_groups.items())
    anchors = [str(item) for item in profile.anchor_phrases]
    expand_on = OrderedDict()
    for slug, entry in profile.expand_on.items():
        slug = str(slug)
        if slug in groups:
            raise SystemExit(f"expand_on slug collides with keyword group: {slug}")
        phrases = [str(item) for item in entry["phrases"]]
        expand_on[slug] = {
            "note": str(entry["note"]),
            "phrases": phrases,
        }
        groups[slug] = phrases
    return categories, groups, anchors, expand_on


def select_keys(all_keys: list[str], selected: str | None, label: str) -> list[str]:
    if not selected:
        return all_keys
    wanted = [item.strip() for item in selected.split(",") if item.strip()]
    unknown = sorted(set(wanted) - set(all_keys))
    if unknown:
        raise SystemExit(f"unknown {label}: {', '.join(unknown)}")
    return wanted


def plan_requests(profile: Profile, start_date: dt.date, end_date: dt.date,
                  categories: str | None = None, groups: str | None = None) -> list[str]:
    """Return the ordered dry-run lines without transport, clocks or file access."""
    configured, keywords, _, _ = load_config(profile)
    selected = select_keys(list(configured), categories, "categories")
    select_keys(list(keywords), groups, "groups")
    if start_date > end_date:
        raise SystemExit("--start-date must be on or before --end-date")
    lines = []
    for category in selected:
        params = {
            "verb": "ListRecords",
            "set": category_to_set(category),
            "from": start_date.isoformat(),
            "until": end_date.isoformat(),
            "metadataPrefix": "arXiv",
        }
        url = f"https://{OAI_HOST}{OAI_PATH}?{urllib.parse.urlencode(params)}"
        lines.append(f"{category}: {url}")
    return lines


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
    expand_on: OrderedDict[str, dict[str, Any]],
    capped_categories: set[str] | None = None,
    max_per_category: int | None = None,
) -> str:
    new_id_set = set(new_ids)
    active_expand_on = [
        f"{slug} ({expand_on[slug]['note']})" for slug in selected_groups if slug in expand_on
    ]
    lines: list[str] = [
        f"# Scout {end_date.isoformat()}",
        "",
        f"Query window: {start_date.isoformat()} to {end_date.isoformat()}",
        "Window semantics: OAI-PMH metadata datestamp, not original submission date",
        "Sources: arXiv OAI-PMH",
        f"Categories: {', '.join(selected_categories)}",
        f"Keyword groups: {', '.join(selected_groups)}",
        f"Expand-on slugs: {', '.join(active_expand_on) if active_expand_on else '(none)'}",
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
        heading = f"### Category: `{category}` (set `{category_to_set(category)}`)"
        if capped_categories and category in capped_categories:
            heading += f" (capped at --max-per-category {max_per_category}; later matches in the window were not read)"
        lines.append(heading)
        fresh = [record for record in records if record["id"] in new_id_set]
        if not fresh:
            lines.append("- (no new results)")
        for record in fresh:
            lines.extend(entry_block(record))
    return "\n".join(lines).rstrip() + "\n"


def register(subparsers):
    parser = subparsers.add_parser("scout", description="Mechanical arXiv scout via OAI-PMH. No judgment inside.")
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
    parser.set_defaults(run=main)


def main(args) -> int:
    profile = load_profile(args.config)
    return run(args, profile)


def run(args, profile: Profile) -> int:
    categories, groups, anchors, expand_on = load_config(profile)
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
        for line in plan_requests(profile, start_date, end_date, args.categories, args.groups):
            print(line)
        return 0

    seen_before = load_ledger(args.ledger)
    per_category: OrderedDict[str, list[dict[str, Any]]] = OrderedDict()
    capped_categories: set[str] = set()
    deduped: OrderedDict[str, dict[str, Any]] = OrderedDict()
    client = OAIClient(delay_seconds=MIN_DELAY_SECONDS, timeout=args.timeout)

    try:
        for category in selected_categories:
            print(f"harvesting {category} ...", file=sys.stderr)
            records, capped = harvest_category(
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
            if capped:
                capped_categories.add(category)
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
        expand_on,
        capped_categories,
        args.max_per_category,
    )

    outfile = args.outfile or args.outdir / f"scout-{end_date.isoformat()}.md"
    outfile.parent.mkdir(parents=True, exist_ok=True)
    outfile.write_text(output, encoding="utf-8")
    append_ledger(args.ledger, new_ids)
    print(f"wrote {outfile}: {len(new_ids)} new candidates ({skipped_count} suppressed by ledger)", file=sys.stderr)
    return 0
