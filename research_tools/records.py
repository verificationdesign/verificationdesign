"""Lossless scout and triage records.

Scalar fields retain their literal spelling, including comma-separated lists,
unknown markers and wrapped prose. None means a field was absent. Syntax spans
retain whitespace and punctuation independently of values: renderers substitute
values into those spans, so edits to present fields also render correctly.
Unknown scout trailing sections and triage third-level sections are opaque prose.
"""

from dataclasses import dataclass, field
from datetime import date
import re


class RecordError(ValueError):
    def __init__(self, line: int, expected: str):
        self.line = line
        self.expected = expected
        super().__init__(f"line {line}: expected {expected}")


@dataclass(frozen=True, kw_only=True)
class _Syntax:
    _text: str = field(repr=False, compare=False)
    _spans: dict[str, tuple[int, int]] = field(default_factory=dict, repr=False, compare=False)

    def render(self) -> str:
        result, end = [], 0
        for name, (start, stop) in sorted(self._spans.items(), key=lambda x: x[1]):
            value = getattr(self, name)
            result.extend((self._text[end:start], value if isinstance(value, str) else value.render()))
            end = stop
        result.append(self._text[end:])
        return "".join(result)


@dataclass(frozen=True)
class Header(_Syntax):
    title: str
    date: str
    window: str | None = None
    source_scout: str | None = None
    reviewer: str | None = None


@dataclass(frozen=True)
class Section:
    heading: str
    body: str
    decision: str | None = None
    _decision_span: tuple[int, int] | None = field(default=None, repr=False, compare=False)

    def render(self) -> str:
        if self._decision_span is None:
            return self.heading + self.body
        start, stop = self._decision_span
        return self.heading + self.body[:start] + self.decision + self.body[stop:]


@dataclass(frozen=True)
class ScoutEntry(_Syntax):
    id: str
    url: str
    title: str
    authors: str
    categories: str
    created: str
    updated: str
    oai_datestamp: str | None
    matched_anchors: str | None
    matched_keywords: str
    abstract_excerpt: str
    appeared_in: str | None = None


@dataclass(frozen=True)
class QueueEntry(_Syntax):
    id: str
    url: str
    title: str
    checked: str
    label: str
    reason: str


@dataclass(frozen=True)
class EntrySection:
    prefix: str
    entries: tuple[ScoutEntry | QueueEntry, ...]

    def render(self) -> str:
        return self.prefix + "".join(entry.render() for entry in self.entries)


@dataclass(frozen=True)
class Category:
    heading: str
    records: EntrySection
    capped_at: int | None = None

    def render(self) -> str:
        return self.heading + self.records.render()


@dataclass(frozen=True)
class CategorySection:
    prefix: str
    categories: tuple[Category, ...]

    def render(self) -> str:
        return self.prefix + "".join(category.render() for category in self.categories)


@dataclass(frozen=True)
class ScoutDocument:
    header: Header
    review_queue: EntrySection
    deduped_candidates: EntrySection
    category_results: CategorySection
    trailing_sections: tuple[Section, ...]


@dataclass(frozen=True)
class TriageCandidate(_Syntax):
    title: str
    source: str
    initial_label: str
    confidence: str
    sections: tuple[Section, ...]

    @property
    def decision(self) -> str:
        return next(s.decision for s in self.sections if s.decision is not None)

    def render(self) -> str:
        return super().render() + "".join(s.render() for s in self.sections)


@dataclass(frozen=True)
class TriageDocument:
    header: Header
    candidates: tuple[TriageCandidate, ...]
    trailing_sections: tuple[Section, ...]


def _line(text, offset, base):
    return base + text.count("\n", 0, offset)


def _capture(text, pattern, name, values, spans, base, required=True):
    matches = list(re.finditer(pattern, text, re.MULTILINE))
    if not matches:
        if required:
            raise RecordError(base, name)
        values[name] = None
        return
    if len(matches) != 1:
        raise RecordError(_line(text, matches[1].start(), base), f"one {name} field")
    match = matches[0]
    values[name] = match.group(1)
    spans[name] = match.span(1)


def _field(text, label, name, values, spans, base, *, bullet=False, required=True):
    prefix = r"  - " if bullet else ""
    # A wrapped field ends at the next metadata bullet or heading, not the first
    # newline; blank separators remain syntax rather than part of its value.
    pattern = (r"^" + prefix + re.escape(label) + r":[ \t]?([^\r\n]*"
               + (r"(?:\r?\n    [^\r\n]+)*" if bullet else "") + r")")
    _capture(text, pattern, name, values, spans, base, required)


def _header(text, kind, base=1):
    values, spans = {}, {}
    _capture(text, r"^# (" + kind + r"[^\r\n]+)", "title", values, spans, base)
    if kind == "Scout ":
        _capture(text, r"^# Scout (\d{4}-\d{2}-\d{2})\r?$", "date", values, {}, base)
        _field(text, "Query window", "window", values, spans, base)
    else:
        for label, name in (("Date", "date"), ("Source scout", "source_scout"), ("Reviewer", "reviewer")):
            _field(text, label, name, values, spans, base)
    try:
        date.fromisoformat(values["date"])
    except ValueError:
        raise RecordError(base, "ISO calendar date") from None
    return Header(_text=text, _spans=spans, **values)


def _blocks(text, pattern):
    matches = list(re.finditer(pattern, text, re.MULTILINE))
    return [(m.start(), matches[i + 1].start() if i + 1 < len(matches) else len(text))
            for i, m in enumerate(matches)]


def _section(text):
    end = text.find("\n") + 1 or len(text)
    return Section(text[:end], text[end:])


def _entry(text, base, queue=False):
    values, spans = {}, {}
    link_pattern = r"\[(?:arXiv:)?([^\]\s]+)\]\(([^)\r\n]+)\)"
    first_line_end = text.find("\n")
    first_line_end = len(text) if first_line_end < 0 else first_line_end
    link = re.search(link_pattern, text[:first_line_end])
    if link is None and not queue:
        link = re.search(r"^  - arXiv: " + link_pattern, text, re.MULTILINE)
    if link is None:
        raise RecordError(base, "entry arXiv id and URL")
    for name, group in (("id", 1), ("url", 2)):
        values[name], spans[name] = link.group(group), link.span(group)
    first = text.splitlines()[0]
    start = 6 if queue else 2
    if queue:
        _capture(text, r"^- \[([ xX])\] ", "checked", values, spans, base)
    end = len(first)
    if link.start() < len(first):
        end = link.start()
        # The old renderer used a dash separator; the current one uses parens.
        while end > start and first[end - 1] in " (\u2014":
            end -= 1
    values["title"], spans["title"] = text[start:end], (start, end)
    if not values["title"]:
        raise RecordError(base, "entry title")
    if queue:
        labels = (("Label", "label"), ("Reason", "reason"))
    else:
        labels = (("Authors", "authors"), ("Categories", "categories"),
                  ("Updated", "updated"), ("Matched keywords", "matched_keywords"),
                  ("Abstract excerpt", "abstract_excerpt"))
        created_label = "Created" if "  - Created:" in text else "Published"
        _field(text, created_label, "created", values, spans, base, bullet=True)
        for label, name in (("OAI datestamp", "oai_datestamp"),
                            ("Matched anchors", "matched_anchors"), ("Appeared in", "appeared_in")):
            _field(text, label, name, values, spans, base, bullet=True, required=False)
    for label, name in labels:
        _field(text, label, name, values, spans, base, bullet=True)
    cls = QueueEntry if queue else ScoutEntry
    return cls(_text=text, _spans=spans, **values)


def _entries(text, base, queue=False):
    spans = _blocks(text, r"^- (?!\(no new )")
    prefix_end = spans[0][0] if spans else len(text)
    entries = tuple(_entry(text[a:b], _line(text, a, base), queue) for a, b in spans)
    return EntrySection(text[:prefix_end], entries)


def parse_scout(text: str) -> ScoutDocument:
    blocks = _blocks(text, r"^## ")
    if not blocks:
        raise RecordError(1, "scout sections")
    header = _header(text[:blocks[0][0]], "Scout ")
    expected = ("## Review Queue", "## Deduped Candidates")
    parsed = []
    for i, heading in enumerate(expected):
        if i >= len(blocks) or text[blocks[i][0]:blocks[i][1]].splitlines()[0] != heading:
            line = _line(text, blocks[min(i, len(blocks) - 1)][0], 1)
            raise RecordError(line, heading)
        a, b = blocks[i]
        parsed.append(_entries(text[a:b], _line(text, a, 1), queue=i == 0))
    if len(blocks) < 3:
        raise RecordError(text.count("\n") + 1, "## Category Results")
    a, b = blocks[2]
    category_text = text[a:b]
    if category_text.splitlines()[0] not in ("## Category Results", "## Query Results"):
        raise RecordError(_line(text, a, 1), "## Category Results or ## Query Results")
    category_spans = _blocks(category_text, r"^### ")
    categories = []
    for start, stop in category_spans:
        section = _section(category_text[start:stop])
        if not section.heading.startswith(("### Category: ", "### Query: ")):
            raise RecordError(_line(text, a + start, 1), "category or query heading")
        cap = re.search(r"capped at --max-per-category (\d+)", section.heading)
        categories.append(Category(section.heading,
                                   _entries(section.body, _line(text, a + start + len(section.heading), 1)),
                                   int(cap.group(1)) if cap else None))
    prefix_end = category_spans[0][0] if category_spans else len(category_text)
    result = CategorySection(category_text[:prefix_end], tuple(categories))
    return ScoutDocument(header, *parsed, result, tuple(_section(text[a:b]) for a, b in blocks[3:]))


def render_scout(doc: ScoutDocument) -> str:
    return (doc.header.render() + doc.review_queue.render() + doc.deduped_candidates.render()
            + doc.category_results.render() + "".join(s.render() for s in doc.trailing_sections))


def parse_triage(text: str) -> TriageDocument:
    blocks = _blocks(text, r"^## ")
    if not blocks:
        raise RecordError(1, "## Candidate: block")
    header = _header(text[:blocks[0][0]], "Triage: ")
    candidates, trailing = [], []
    for a, b in blocks:
        chunk, base = text[a:b], _line(text, a, 1)
        heading = chunk.splitlines()[0]
        if not heading.startswith("## Candidate: "):
            if heading not in ("## Ignore", "## Deferred", "## Batch accounting", "## Run Complete"):
                raise RecordError(base, "candidate or supported trailing heading")
            trailing.append(_section(chunk))
            continue
        if trailing:
            raise RecordError(base, "trailing section, not another candidate")
        values, spans = {}, {}
        _capture(chunk, r"^## Candidate: ([^\r\n]+)", "title", values, spans, base)
        section_spans = _blocks(chunk, r"^### ")
        meta_end = section_spans[0][0] if section_spans else len(chunk)
        for label, name in (("Source", "source"), ("Initial label", "initial_label"), ("Confidence", "confidence")):
            _field(chunk[:meta_end], label, name, values, spans, base)
        sections = []
        for start, stop in section_spans:
            section = _section(chunk[start:stop])
            if section.heading.rstrip() == "### Decision":
                decision_values, decision_spans = {}, {}
                decision_base = _line(chunk, start + len(section.heading), base)
                _field(section.body, "Decision", "decision", decision_values, decision_spans, decision_base)
                section = Section(section.heading, section.body, decision_values["decision"], decision_spans["decision"])
            sections.append(section)
        if sum(s.decision is not None for s in sections) != 1:
            raise RecordError(base, "one ### Decision section")
        candidates.append(TriageCandidate(_text=chunk[:meta_end], _spans=spans, sections=tuple(sections), **values))
    if not candidates:
        raise RecordError(_line(text, blocks[0][0], 1), "## Candidate: block")
    return TriageDocument(header, tuple(candidates), tuple(trailing))


def render_triage(doc: TriageDocument) -> str:
    return (doc.header.render() + "".join(c.render() for c in doc.candidates)
            + "".join(s.render() for s in doc.trailing_sections))
