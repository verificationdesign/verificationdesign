#!/usr/bin/env python3
"""Local mechanical checks for the research notes."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path


from research_tools.profile import Profile, load_profile
from research_tools import records, scout


DATE_RE = re.compile(r"\b20\d{2}-\d{2}-\d{2}\b")
# A dated update note (date and the word update on one line) or an undated one
# (a line that opens with an "Update:" marker, after any blockquote or bullet).
UPDATE_NOTE_RE = re.compile(
    r"\b20\d{2}-\d{2}-\d{2}\b.*\bupdate\b|\bupdate\b.*\b20\d{2}-\d{2}-\d{2}\b"
    r"|^\s*(?:>\s*)*(?:[-*]\s+)?\**update\**\s*:",
    re.IGNORECASE,
)
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


def url_ok(url: str, fetch=None) -> tuple[bool, str]:
    fetch = urllib.request.urlopen if fetch is None else fetch
    request = urllib.request.Request(url, method="HEAD", headers={"User-Agent": "ai-research-verify/1.0"})
    try:
        with fetch(request, timeout=15) as response:
            return 200 <= response.status < 400, f"HTTP {response.status}"
    except urllib.error.HTTPError as exc:
        if exc.code in {403, 405}:
            get_request = urllib.request.Request(url, headers={"User-Agent": "ai-research-verify/1.0"})
            try:
                with fetch(get_request, timeout=15) as response:
                    return 200 <= response.status < 400, f"HTTP {response.status}"
            except Exception as get_exc:  # noqa: BLE001
                return False, str(get_exc)
        return False, f"HTTP {exc.code}"
    except Exception as exc:  # noqa: BLE001
        return False, str(exc)


def load_link_confirmations(link_confirmations: Path) -> dict[str, str]:
    if not link_confirmations.exists():
        return {}
    confirmations: dict[str, str] = {}
    for line in link_confirmations.read_text(encoding="utf-8").splitlines():
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


def check_links(paths: list[Path], link_confirmations: Path, fetch=None) -> Check:
    urls: list[str] = []
    for path in paths:
        urls.extend(collect_links(path))
    confirmations = load_link_confirmations(link_confirmations)
    failures: list[str] = []
    manually_confirmed = 0
    for url in sorted(set(urls)):
        ok, status = url_ok(url, fetch)
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


def reviewed_source_labels(review_dir: Path) -> tuple[set[str], set[str]]:
    reviewed_labels: set[str] = set()
    legacy_labels: set[str] = set()
    notes = sorted(path for path in review_dir.glob("*.md") if path.name != "TEMPLATE.md")
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


def check_citation_review_provenance(path: Path, review_dir: Path) -> Check:
    canonical = canonical_citation_labels(path)
    reviewed, legacy = reviewed_source_labels(review_dir)
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


def check_update_provenance(path: Path, root: Path) -> Check:
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
            failures.append(f"{path.name}:{idx}: update note does not name a source")
    return Check(
        "provenance",
        not failures,
        f"{path.relative_to(root)}: {len(update_blocks)} update note blocks inspected; {len(failures)} failures",
        failures,
    )


def check_review_notes(root: Path, review_dir: Path) -> Check:
    notes = sorted(path for path in review_dir.glob("*.md") if path.name not in {"TEMPLATE.md", "LEGACY-CITATIONS.md"})
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
                failures.append(f"{note.relative_to(root)} missing or invalid {name}")
    return Check(
        "review note metadata",
        not failures,
        f"{len(notes)} reviewed source notes inspected; {len(failures)} failures",
        failures,
    )


def check_triage_notes(root: Path, triage_dir: Path) -> Check:
    excluded = {"TEMPLATE.md", "README.md", "anchors.md", "ranking_design.md"}
    notes = sorted(path for path in triage_dir.glob("*.md") if path.name not in excluded)
    failures: list[str] = []
    candidate_count = 0
    for note in notes:
        try:
            doc = records.parse_triage(note.read_text(encoding="utf-8"))
        except records.RecordError as exc:
            failures.append(f"{note.relative_to(root)} missing or invalid {exc}")
            continue
        candidate_count += len(doc.candidates)
        for name, value in (("Source scout", doc.header.source_scout), ("Reviewer", doc.header.reviewer)):
            if not value or not value.strip():
                failures.append(f"{note.relative_to(root)} missing or invalid {name}")
        for candidate in doc.candidates:
            fields = {
                "Source": bool(candidate.source.strip()),
                "Initial label": candidate.initial_label.strip() in {"challenges", "narrows", "extends", "operational technique", "ignore"},
                "Confidence": candidate.confidence.strip() in {"low", "medium", "high"},
                "Abstract Paraphrase": any(s.heading.strip() == "### Abstract Paraphrase" for s in candidate.sections),
                "Key Findings": any(s.heading.strip() == "### Key Findings" for s in candidate.sections),
                "Decision": candidate.decision.strip() in {"promote", "keep-in-triage", "keep-in-scout", "ignore"},
            }
            for name, valid in fields.items():
                if not valid:
                    failures.append(f"{note.relative_to(root)} candidate {candidate.title!r} missing or invalid {name}")
    return Check(
        "triage note metadata",
        not failures,
        f"{len(notes)} triage notes inspected; {candidate_count} candidates inspected; {len(failures)} failures",
        failures,
    )


def check_append_only(root: Path, base_ref: str) -> Check:
    try:
        diff = subprocess.run(
            ["git", "diff", base_ref, "--", "research/synthesis.md"],
            cwd=root,
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except OSError as exc:
        return Check("append-not-overwrite", False, "could not run git diff", [str(exc)])
    if diff.returncode != 0:
        return Check("append-not-overwrite", False, f"could not diff against {base_ref}", [diff.stderr.strip()])
    hunk_lines = []
    in_hunk = False
    for line in diff.stdout.splitlines():
        if line.startswith("@@"):
            in_hunk = True
        elif in_hunk:
            hunk_lines.append(line)
    added_lines = {
        line[1:].strip()
        for line in hunk_lines
        if line.startswith("+")
    }
    deleted_lines = []
    for line in hunk_lines:
        if not line.startswith("-"):
            continue
        normalized = line[1:].strip()
        if not normalized or normalized in added_lines or normalized.startswith("Status:"):
            continue
        deleted_lines.append(line)
    return Check(
        "append-not-overwrite",
        not deleted_lines,
        f"research/synthesis.md: {len(deleted_lines)} deleted non-blank lines without an allowed replacement in git diff against {base_ref}",
        deleted_lines,
    )


def check_scout_config(config_path: Path) -> Check:
    """Validate the selected profile file, the same one the other checks and scout use."""
    if not config_path.exists():
        return Check("scout config / query shape", False, "profile missing", [str(config_path)])
    try:
        raw = json.loads(config_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return Check("scout config / query shape", False, "profile invalid JSON", [str(exc)])

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
            profile = load_profile(config_path)
            # Query shape is independent of today's date; keep this check deterministic.
            lines = scout.plan_requests(profile, dt.date(2000, 1, 1), dt.date(2000, 3, 31))
            for line in lines:
                tag, _, url = line.partition(": ")
                dry_run_lines.append((tag, url))
        except (OSError, ValueError, SystemExit) as exc:
            details.append(f"scout --dry-run failed: {exc}")

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
        parser = argparse.ArgumentParser()
        commands = parser.add_subparsers()
        scout.register(commands)
        if any("--sleep" in action.option_strings
               for action in commands.choices["scout"]._actions):
            details.append("scout unexpectedly accepts --sleep; delay must stay fixed in code")

    return Check(
        "scout config / query shape",
        not details,
        f"{n_cats} categories; {n_groups} groups; {n_anchors} anchors; {topic_phrases} topic phrases; {len(dry_run_lines)} dry-run requests",
        details,
    )


def check_legacy_citations(root: Path, base_ref: str) -> Check:
    legacy_path = "research/reviewed/LEGACY-CITATIONS.md"
    legacy_file = root / legacy_path
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
            cwd=root,
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


def check_principles(path: Path, profile: Profile) -> Check:
    titles = re.findall(r"^### \d+\. (.+)$", path.read_text(encoding="utf-8"), re.MULTILINE)
    expected = list(profile.principles.values())
    failures = []
    if len(titles) != len(expected):
        failures.append(f"principle count observed {len(titles)}, expected {len(expected)}")
    for index, (title, wanted) in enumerate(zip(titles, expected), 1):
        if title != wanted:
            failures.append(f"principle {index} title observed {title!r}, expected {wanted!r}")
    return Check("principles match canonical doc", not failures,
                 f"{len(expected)} profile principles; {len(titles)} canonical headings; {len(failures)} failures", failures)


def run(root: Path, profile: Profile, *, skip_links: bool, include_scout_links: bool,
        base_ref: str, fetch=None, profile_path: Path | None = None) -> list[Check]:
    if profile_path is None:
        profile_path = root / "research/scouts/config.json"
    docs = [root / path for path in profile.canonical_docs]
    review_dir = root / "research/reviewed"
    triage_dir = root / "research/triage"
    scout_dir = root / "research/scouts"
    paths = docs + [root / "README.md", root / "AGENTS.md"]
    checks = [
        check_citations(docs[0]),
        check_source_label_parser(),
        check_citation_review_provenance(docs[0], review_dir),
        check_numbering_and_anchors(docs[0]),
        check_update_provenance(docs[0], root),
        check_update_provenance(root / "research/synthesis.md", root),
        check_review_notes(root, review_dir),
        check_triage_notes(root, triage_dir),
        check_append_only(root, base_ref),
        check_legacy_citations(root, base_ref),
        check_scout_config(profile_path),
        check_principles(docs[0], profile),
    ]
    if not skip_links:
        link_paths = paths + [root / "research/synthesis.md"] + sorted(review_dir.glob("*.md")) + sorted(triage_dir.rglob("*.md"))
        if include_scout_links:
            link_paths += sorted(scout_dir.glob("*.md"))
        checks.insert(0, check_links(link_paths, root / "research/link-confirmations.txt", fetch))
    return checks


def _arguments(parser):
    root = Path(__file__).resolve().parents[1]
    parser.add_argument("--skip-links", action="store_true", help="skip network link liveness checks")
    parser.add_argument("--include-scout-links", action="store_true", help="include research/scouts/*.md in link checks")
    parser.add_argument("--base-ref", default=os.environ.get("VERIFY_BASE_REF", "HEAD"), help="git base ref for append-only diff (default: HEAD or VERIFY_BASE_REF)")
    parser.add_argument("--profile", type=Path, default=root / "research/scouts/config.json")
    parser.set_defaults(run=_execute)


def register(subparsers):
    _arguments(subparsers.add_parser("verify", help=__doc__))


def _execute(args) -> int:
    root = Path(__file__).resolve().parents[1]
    checks = run(root, load_profile(args.profile), skip_links=args.skip_links,
                 include_scout_links=args.include_scout_links, base_ref=args.base_ref,
                 profile_path=args.profile)
    failed = False
    for check in checks:
        status = "PASS" if check.ok else "FAIL"
        print(f"[{status}] {check.name}: {check.observed}")
        for detail in check.details:
            print(f"  - {detail}")
        failed = failed or not check.ok
    return 1 if failed else 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    _arguments(parser)
    return _execute(parser.parse_args(argv))


if __name__ == "__main__":
    sys.exit(main())
