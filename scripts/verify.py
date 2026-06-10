#!/usr/bin/env python3
"""Local mechanical checks for the research notes."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOCS = [ROOT / "verification_design.md"]
REVIEW_DIR = ROOT / "research" / "reviewed"
SCOUT_DIR = ROOT / "research" / "scouts"
TRIAGE_DIR = ROOT / "research" / "triage"
LINK_CONFIRMATIONS = ROOT / "research" / "link-confirmations.txt"
DATE_RE = re.compile(r"\b20\d{2}-\d{2}-\d{2}\b")
UPDATE_NOTE_RE = re.compile(r"\b20\d{2}-\d{2}-\d{2}\b.*\bupdate\b|\bupdate\b.*\b20\d{2}-\d{2}-\d{2}\b", re.IGNORECASE)
URL_RE = re.compile(r"https?://[^\s)<>\"]+")
LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
CITATION_LABEL_RE = re.compile(
    r"^(arXiv:\d{4}\.\d{4,5}|doi:[^ ]+|openreview:[A-Za-z0-9]+|aaai:\d+|acm:10\.[^ ]+)$",
    re.IGNORECASE,
)

LEGACY_BASELINE = 13


@dataclass
class Check:
    name: str
    ok: bool
    observed: str
    details: list[str]


def slugify_heading(text: str) -> str:
    text = text.strip().lower()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"\s+", "-", text)
    return text


def split_references(text: str) -> tuple[str, str]:
    marker = "\n## References"
    if marker not in text:
        return text, ""
    before, after = text.split(marker, 1)
    return before, "## References" + after


def collect_links(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8")
    text = re.sub(r"```.*?```", "", text, flags=re.DOTALL)
    text = re.sub(r"`[^`\n]+`", "", text)
    markdown_urls = [url for _label, url in LINK_RE.findall(text) if url.startswith(("http://", "https://"))]
    bare_urls = [match.group(0).rstrip(".,") for match in URL_RE.finditer(LINK_RE.sub("", text))]
    return markdown_urls + bare_urls


def url_ok(url: str) -> tuple[bool, str]:
    request = urllib.request.Request(url, method="HEAD", headers={"User-Agent": "ai-research-verify/1.0"})
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            return 200 <= response.status < 400, f"HTTP {response.status}"
    except urllib.error.HTTPError as exc:
        if exc.code in {403, 405}:
            get_request = urllib.request.Request(url, headers={"User-Agent": "ai-research-verify/1.0"})
            try:
                with urllib.request.urlopen(get_request, timeout=15) as response:
                    return 200 <= response.status < 400, f"HTTP {response.status}"
            except Exception as get_exc:  # noqa: BLE001
                return False, str(get_exc)
        return False, f"HTTP {exc.code}"
    except Exception as exc:  # noqa: BLE001
        return False, str(exc)


def load_link_confirmations() -> dict[str, str]:
    if not LINK_CONFIRMATIONS.exists():
        return {}
    confirmations: dict[str, str] = {}
    for line in LINK_CONFIRMATIONS.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if " " not in line:
            continue
        date, rest = line.split(" ", 1)
        if not DATE_RE.fullmatch(date):
            continue
        url, _, reason = rest.partition(" -- ")
        if url.startswith(("http://", "https://")) and reason:
            confirmations[url] = f"{date}: {reason}"
    return confirmations


def check_links(paths: list[Path]) -> Check:
    urls: list[str] = []
    for path in paths:
        urls.extend(collect_links(path))
    confirmations = load_link_confirmations()
    failures: list[str] = []
    manually_confirmed = 0
    for url in sorted(set(urls)):
        ok, status = url_ok(url)
        if not ok:
            if url in confirmations:
                manually_confirmed += 1
            else:
                failures.append(f"{url} -> {status}")
    return Check(
        "link liveness",
        not failures,
        f"{len(set(urls))} unique URLs checked; {manually_confirmed} manually confirmed; {len(failures)} failures",
        failures,
    )


def check_citations(path: Path) -> Check:
    text = path.read_text(encoding="utf-8")
    body, refs = split_references(text)
    if not refs:
        return Check("citation/reference balance", False, "References section missing", [])

    inline_labels = {
        label
        for label, _url in LINK_RE.findall(body)
        if CITATION_LABEL_RE.match(label)
    }
    ref_labels = {
        label
        for label, _url in LINK_RE.findall(refs)
        if CITATION_LABEL_RE.match(label)
    }
    missing_refs = sorted(inline_labels - ref_labels)
    orphan_refs = sorted(ref_labels - inline_labels)
    details = [f"inline citation without reference row: {label}" for label in missing_refs]
    details.extend(f"reference row not cited inline: {label}" for label in orphan_refs)
    return Check(
        "citation/reference balance",
        not details,
        f"{len(inline_labels)} inline citation labels; {len(ref_labels)} reference labels; {len(details)} imbalances",
        details,
    )


def canonical_citation_labels(path: Path) -> set[str]:
    text = path.read_text(encoding="utf-8")
    body, _refs = split_references(text)
    return {
        label
        for label, _url in LINK_RE.findall(body)
        if CITATION_LABEL_RE.match(label)
    }


def source_to_citation_label(source: str) -> str | None:
    value = source.strip().rstrip(".,")
    lowered = value.lower()
    if CITATION_LABEL_RE.match(value):
        return normalize_citation_label(value)
    arxiv = re.search(r"(?:arxiv\.org/(?:abs|html)/|arxiv:)(\d{4}\.\d{4,5})", lowered)
    if arxiv:
        return f"arXiv:{arxiv.group(1)}"
    openreview = re.search(r"(?:openreview\.net/forum\?id=|openreview:)([A-Za-z0-9]+)", value, re.IGNORECASE)
    if openreview:
        return f"openreview:{openreview.group(1)}"
    aaai = re.search(r"aaai:(\d+)", lowered)
    if aaai:
        return f"aaai:{aaai.group(1)}"
    aaai_url = re.search(r"ojs\.aaai\.org/.+?/(\d+)(?:/|$)", value)
    if aaai_url:
        return f"aaai:{aaai_url.group(1)}"
    acm = re.search(r"acm:(10\.[^\s)]+)", value, re.IGNORECASE)
    if acm:
        return f"acm:{acm.group(1)}"
    acm_url = re.search(r"dl\.acm\.org/doi/(10\.[^\s)]+)", value)
    if acm_url:
        return f"acm:{acm_url.group(1)}"
    mit_tacl = re.search(r"direct\.mit\.edu/.+?/doi/(10\.1162/[^/\s)]+)", value)
    if mit_tacl:
        return f"doi:{mit_tacl.group(1)}"
    doi = re.search(r"(?:doi:|doi\.org/|/doi/)(10\.\d{4,9}/[A-Za-z0-9._;()/:+-]+)", value, re.IGNORECASE)
    if doi:
        return f"doi:{doi.group(1).rstrip('/')}"
    return None


def normalize_citation_label(label: str) -> str:
    prefix, value = label.split(":", 1)
    normalized_prefix = prefix.lower()
    if normalized_prefix == "arxiv":
        return f"arXiv:{value}"
    return f"{normalized_prefix}:{value}"


def reviewed_source_labels() -> tuple[set[str], set[str]]:
    reviewed_labels: set[str] = set()
    legacy_labels: set[str] = set()
    notes = sorted(path for path in REVIEW_DIR.glob("*.md") if path.name != "TEMPLATE.md")
    for note in notes:
        text = note.read_text(encoding="utf-8")
        for source in re.findall(r"^Source:\s+(.+)$", text, flags=re.MULTILINE):
            label = source_to_citation_label(source)
            if label:
                reviewed_labels.add(label)
        if note.name == "LEGACY-CITATIONS.md":
            legacy_labels.update(
                normalize_citation_label(label)
                for label, _url in LINK_RE.findall(text)
                if CITATION_LABEL_RE.match(label)
            )
    return reviewed_labels, legacy_labels


def check_citation_review_provenance(path: Path) -> Check:
    canonical = canonical_citation_labels(path)
    reviewed, legacy = reviewed_source_labels()
    covered = reviewed | legacy
    missing = sorted(canonical - covered, key=str.lower)
    return Check(
        "citation reviewed-note provenance",
        not missing,
        f"{len(canonical)} canonical citation labels; {len(reviewed)} reviewed-note labels; {len(legacy)} legacy labels; {len(missing)} missing reviewed notes",
        [f"canonical citation lacks reviewed note source: {label}" for label in missing],
    )


def check_source_label_parser() -> Check:
    cases = {
        "https://arxiv.org/abs/2510.16062": "arXiv:2510.16062",
        "arXiv:2510.16062": "arXiv:2510.16062",
        "https://direct.mit.edu/tacl/article/doi/10.1162/tacl_a_00713/125177/": "doi:10.1162/tacl_a_00713",
        "doi:10.1162/tacl_a_00713": "doi:10.1162/tacl_a_00713",
        "https://ojs.aaai.org/index.php/AIES/article/download/36598/38736/40673": "aaai:36598",
        "aaai:36598": "aaai:36598",
        "https://dl.acm.org/doi/10.1145/2635868.2635920": "acm:10.1145/2635868.2635920",
        "acm:10.1145/2635868.2635920": "acm:10.1145/2635868.2635920",
        "https://openreview.net/forum?id=MTvYflAH62": "openreview:MTvYflAH62",
    }
    failures = []
    for source, expected in cases.items():
        observed = source_to_citation_label(source)
        if observed != expected:
            failures.append(f"{source} -> {observed!r}, expected {expected!r}")
    return Check(
        "source label parser",
        not failures,
        f"{len(cases)} parser cases checked; {len(failures)} failures",
        failures,
    )


def check_numbering_and_anchors(path: Path) -> Check:
    text = path.read_text(encoding="utf-8")
    numbers = [int(match.group(1)) for match in re.finditer(r"^### (\d+)\. ", text, flags=re.MULTILINE)]
    expected = list(range(1, len(numbers) + 1))
    details: list[str] = []
    if numbers != expected:
        details.append(f"principle numbering observed {numbers}, expected {expected}")

    headings = {
        slugify_heading(match.group(1))
        for match in re.finditer(r"^#{1,6}\s+(.+)$", text, flags=re.MULTILINE)
    }
    for _label, target in LINK_RE.findall(text):
        if target.startswith("#") and target[1:] not in headings:
            details.append(f"unresolved internal anchor: {target}")
    return Check(
        "format / anchor lint",
        not details,
        f"{len(numbers)} numbered principles; {len(headings)} anchors; {len(details)} failures",
        details,
    )


def check_update_provenance(path: Path) -> Check:
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    update_blocks: list[tuple[int, str]] = []
    for idx, line in enumerate(lines):
        if not UPDATE_NOTE_RE.search(line):
            continue
        block_lines = [line]
        for following in lines[idx + 1 :]:
            if not following.strip() or UPDATE_NOTE_RE.search(following) or following.startswith("#"):
                break
            block_lines.append(following)
        update_blocks.append((idx + 1, "\n".join(block_lines)))
    failures = []
    for idx, block in update_blocks:
        lowered = block.lower()
        if "source" not in lowered and "arxiv" not in lowered and "doi" not in lowered:
            failures.append(f"{path.name}:{idx}: dated update note does not name a source")
    return Check(
        "provenance",
        not failures,
        f"{len(update_blocks)} dated update note blocks inspected; {len(failures)} failures",
        failures,
    )


def check_review_notes() -> Check:
    notes = sorted(path for path in REVIEW_DIR.glob("*.md") if path.name not in {"TEMPLATE.md", "LEGACY-CITATIONS.md"})
    required_patterns = {
        "Reviewed": re.compile(r"^Reviewed:\s+\d{4}-\d{2}-\d{2}\s*$", re.MULTILINE),
        "Reviewer": re.compile(r"^Reviewer:\s+.+$", re.MULTILINE),
        "Source": re.compile(r"^Source:\s+.+$", re.MULTILINE),
        "Evidence grade": re.compile(r"^Evidence grade:\s+[ABCD]\s*$", re.MULTILINE),
        "Grade confidence": re.compile(r"^Grade confidence:\s+(low|medium|high)\s*$", re.MULTILINE),
        "Limitations": re.compile(r"^## Limitations\s*$", re.MULTILINE),
        "Claims Needing Human Review": re.compile(r"^## Claims Needing Human Review\s*$", re.MULTILINE),
    }
    failures: list[str] = []
    for note in notes:
        text = note.read_text(encoding="utf-8")
        for name, pattern in required_patterns.items():
            if not pattern.search(text):
                failures.append(f"{note.relative_to(ROOT)} missing or invalid {name}")
    return Check(
        "review note metadata",
        not failures,
        f"{len(notes)} reviewed source notes inspected; {len(failures)} failures",
        failures,
    )


def check_triage_notes() -> Check:
    excluded = {"TEMPLATE.md", "README.md", "anchors.md", "ranking_design.md"}
    notes = sorted(path for path in TRIAGE_DIR.glob("*.md") if path.name not in excluded)
    note_patterns = {
        "Date": re.compile(r"^Date:\s+\d{4}-\d{2}-\d{2}\s*$", re.MULTILINE),
        "Source scout": re.compile(r"^Source scout:\s+.+$", re.MULTILINE),
        "Reviewer": re.compile(r"^Reviewer:\s+.+$", re.MULTILINE),
    }
    block_patterns = {
        "Source": re.compile(r"^Source:\s+.+$", re.MULTILINE),
        "Initial label": re.compile(r"^Initial label:\s+(challenges|narrows|extends|operational technique|ignore)\s*$", re.MULTILINE),
        "Confidence": re.compile(r"^Confidence:\s+(low|medium|high)\s*$", re.MULTILINE),
        "Abstract Paraphrase": re.compile(r"^### Abstract Paraphrase\s*$", re.MULTILINE),
        "Key Findings": re.compile(r"^### Key Findings\s*$", re.MULTILINE),
        "Decision": re.compile(r"^Decision:\s+(promote|keep-in-triage|keep-in-scout|ignore)\s*$", re.MULTILINE),
    }
    failures: list[str] = []
    candidate_count = 0
    for note in notes:
        text = note.read_text(encoding="utf-8")
        for name, pattern in note_patterns.items():
            if not pattern.search(text):
                failures.append(f"{note.relative_to(ROOT)} missing or invalid {name}")
        parts = re.split(r"(?m)^## Candidate:\s+", text)
        candidates = parts[1:]
        candidate_count += len(candidates)
        if not candidates:
            failures.append(f"{note.relative_to(ROOT)} has no candidate blocks")
            continue
        for candidate in candidates:
            title = candidate.splitlines()[0].strip() if candidate.splitlines() else "(untitled)"
            for name, pattern in block_patterns.items():
                if not pattern.search(candidate):
                    failures.append(f"{note.relative_to(ROOT)} candidate {title!r} missing or invalid {name}")
    return Check(
        "triage note metadata",
        not failures,
        f"{len(notes)} triage notes inspected; {candidate_count} candidates inspected; {len(failures)} failures",
        failures,
    )


def check_append_only(base_ref: str) -> Check:
    try:
        diff = subprocess.run(
            ["git", "diff", base_ref, "--", "verification_design.md"],
            cwd=ROOT,
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except OSError as exc:
        return Check("append-not-overwrite", False, "could not run git diff", [str(exc)])
    if diff.returncode != 0:
        return Check("append-not-overwrite", False, f"could not diff against {base_ref}", [diff.stderr.strip()])
    added_lines = {
        line[1:].strip()
        for line in diff.stdout.splitlines()
        if line.startswith("+") and not line.startswith("+++")
    }
    deleted_callouts = []
    for line in diff.stdout.splitlines():
        if not line.startswith("-") or line.startswith("---"):
            continue
        normalized = line[1:].strip()
        if normalized in added_lines:
            continue
        if "**Research**" in line or "update" in line.lower() or DATE_RE.search(line):
            deleted_callouts.append(line)
    return Check(
        "append-not-overwrite",
        not deleted_callouts,
        f"{len(deleted_callouts)} deleted research/update callout lines in git diff against {base_ref}",
        deleted_callouts,
    )


def check_scout_config() -> Check:
    config_path = SCOUT_DIR / "config.json"
    if not config_path.exists():
        return Check("scout config / query shape", False, "config.json missing", [str(config_path)])
    try:
        raw = json.loads(config_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return Check("scout config / query shape", False, "config.json invalid JSON", [str(exc)])

    details: list[str] = []
    categories = raw.get("categories")
    groups = raw.get("keyword_groups")
    anchors = raw.get("anchor_phrases")

    if not isinstance(categories, dict) or not categories:
        details.append("categories block missing or empty")
    else:
        for key, value in categories.items():
            if not isinstance(key, str) or not key.strip():
                details.append(f"categories key invalid (empty or non-string): {key!r}")
            if not isinstance(value, str):
                details.append(f"categories[{key!r}] description is not a string: {value!r}")
    if not isinstance(groups, dict) or not groups:
        details.append("keyword_groups block missing or empty")
    else:
        for name, phrases in groups.items():
            if not isinstance(name, str) or not name.strip():
                details.append(f"keyword_groups key invalid (empty or non-string): {name!r}")
            if not isinstance(phrases, list) or not phrases:
                details.append(f"keyword_groups[{name!r}] is not a non-empty list")
                continue
            for phrase in phrases:
                if not isinstance(phrase, str) or not phrase.strip():
                    details.append(f"keyword_groups[{name!r}] has empty or non-string entry: {phrase!r}")
    if anchors is not None:
        if not isinstance(anchors, list) or not anchors:
            details.append("anchor_phrases present but not a non-empty list")
        else:
            for phrase in anchors:
                if not isinstance(phrase, str) or not phrase.strip():
                    details.append(f"anchor_phrases has empty or non-string entry: {phrase!r}")

    seen_phrase_source: dict[str, str] = {}
    if isinstance(anchors, list):
        for phrase in anchors:
            if not isinstance(phrase, str):
                continue
            key = phrase.strip().lower()
            if not key:
                continue
            if key in seen_phrase_source:
                details.append(f"duplicate phrase {phrase!r} (also in {seen_phrase_source[key]})")
            else:
                seen_phrase_source[key] = "anchor_phrases"
    if isinstance(groups, dict):
        for group_name, phrases in groups.items():
            if not isinstance(phrases, list):
                continue
            for phrase in phrases:
                if not isinstance(phrase, str):
                    continue
                key = phrase.strip().lower()
                if not key:
                    continue
                if key in seen_phrase_source:
                    details.append(
                        f"duplicate phrase {phrase!r} in {group_name} (also in {seen_phrase_source[key]})"
                    )
                else:
                    seen_phrase_source[key] = group_name

    topic_phrases = sum(
        len(phrases) for phrases in (groups.values() if isinstance(groups, dict) else []) if isinstance(phrases, list)
    )
    n_cats = len(categories) if isinstance(categories, dict) else 0
    n_groups = len(groups) if isinstance(groups, dict) else 0
    n_anchors = len(anchors) if isinstance(anchors, list) else 0

    dry_run_lines: list[tuple[str, str]] = []
    if isinstance(categories, dict) and isinstance(groups, dict):
        try:
            result = subprocess.run(
                ["python3", str(ROOT / "scripts" / "scout.py"), "--dry-run"],
                cwd=ROOT,
                check=False,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
        except OSError as exc:
            details.append(f"could not run scout.py --dry-run: {exc}")
        else:
            if result.returncode != 0:
                details.append(f"scout.py --dry-run failed: {result.stderr.strip() or result.stdout.strip()}")
            else:
                for line in result.stdout.splitlines():
                    if not line.strip():
                        continue
                    tag, _, url = line.partition(": ")
                    dry_run_lines.append((tag, url))

        if len(dry_run_lines) != n_cats:
            details.append(
                f"dry-run produced {len(dry_run_lines)} requests, expected {n_cats} (one per category)"
            )
        for tag, url in dry_run_lines:
            if not url.startswith("https://oaipmh.arxiv.org/oai?"):
                details.append(f"dry-run request for {tag} does not use arXiv OAI-PMH endpoint")
            if "verb=ListRecords" not in url:
                details.append(f"dry-run request for {tag} missing verb=ListRecords")
            if "metadataPrefix=arXiv" not in url:
                details.append(f"dry-run request for {tag} missing metadataPrefix=arXiv")
            if "set=" not in url:
                details.append(f"dry-run request for {tag} missing set parameter")
            if "from=" not in url or "until=" not in url:
                details.append(f"dry-run request for {tag} missing from/until parameters")
        sleep_result = subprocess.run(
            ["python3", str(ROOT / "scripts" / "scout.py"), "--dry-run", "--sleep", "10"],
            cwd=ROOT,
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        if sleep_result.returncode == 0:
            details.append("scout.py unexpectedly accepts --sleep; delay must stay fixed in code")

    return Check(
        "scout config / query shape",
        not details,
        f"{n_cats} categories; {n_groups} groups; {n_anchors} anchors; {topic_phrases} topic phrases; {len(dry_run_lines)} dry-run requests",
        details,
    )


def check_legacy_citations(base_ref: str) -> Check:
    legacy_path = "research/reviewed/LEGACY-CITATIONS.md"
    legacy_file = ROOT / legacy_path
    if not legacy_file.exists():
        return Check("legacy citation bridge", False, "legacy bridge missing", [legacy_path])
    text = legacy_file.read_text(encoding="utf-8")
    labels = {
        normalize_citation_label(label)
        for label, _url in LINK_RE.findall(text)
        if CITATION_LABEL_RE.match(label)
    }
    details: list[str] = []
    if len(labels) > LEGACY_BASELINE:
        details.append(f"legacy label count is {len(labels)}, expected at most baseline {LEGACY_BASELINE}")
    try:
        diff = subprocess.run(
            ["git", "diff", base_ref, "--", legacy_path],
            cwd=ROOT,
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except OSError as exc:
        return Check("legacy citation bridge", False, "could not run git diff", [str(exc)])
    if diff.returncode != 0:
        return Check("legacy citation bridge", False, f"could not diff against {base_ref}", [diff.stderr.strip()])
    added_labels = [
        normalize_citation_label(label)
        for line in diff.stdout.splitlines()
        if line.startswith("+") and not line.startswith("+++")
        for label, _url in LINK_RE.findall(line)
        if CITATION_LABEL_RE.match(label)
    ]
    if added_labels:
        details.append(f"added legacy labels are not allowed: {', '.join(sorted(set(added_labels), key=str.lower))}")
    return Check(
        "legacy citation bridge",
        not details,
        f"{len(labels)} legacy labels; ceiling {LEGACY_BASELINE}; {len(added_labels)} added labels in git diff against {base_ref}",
        details,
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--skip-links", action="store_true", help="skip network link liveness checks")
    parser.add_argument("--include-scout-links", action="store_true", help="include research/scouts/*.md in link checks")
    parser.add_argument("--base-ref", default=os.environ.get("VERIFY_BASE_REF", "HEAD"), help="git base ref for append-only diff (default: HEAD or VERIFY_BASE_REF)")
    args = parser.parse_args()

    paths = DOCS + [ROOT / "README.md", ROOT / "AGENTS.md"]
    checks = [
        check_citations(DOCS[0]),
        check_source_label_parser(),
        check_citation_review_provenance(DOCS[0]),
        check_numbering_and_anchors(DOCS[0]),
        check_update_provenance(DOCS[0]),
        check_review_notes(),
        check_triage_notes(),
        check_append_only(args.base_ref),
        check_legacy_citations(args.base_ref),
        check_scout_config(),
    ]
    if not args.skip_links:
        link_paths = paths + sorted(REVIEW_DIR.glob("*.md")) + sorted(TRIAGE_DIR.rglob("*.md"))
        if args.include_scout_links:
            link_paths += sorted(SCOUT_DIR.glob("*.md"))
        checks.insert(0, check_links(link_paths))

    failed = False
    for check in checks:
        status = "PASS" if check.ok else "FAIL"
        print(f"[{status}] {check.name}: {check.observed}")
        for detail in check.details:
            print(f"  - {detail}")
        failed = failed or not check.ok
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
