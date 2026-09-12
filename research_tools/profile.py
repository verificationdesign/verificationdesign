"""Load topic data without interpreting or resolving its paths."""

from dataclasses import dataclass, field
import json
from pathlib import Path


@dataclass(frozen=True)
class Profile:
    categories: dict[str, str] = field(default_factory=dict)
    keyword_groups: dict[str, list[str]] = field(default_factory=dict)
    anchor_phrases: list[str] = field(default_factory=list)
    expand_on: dict[str, dict[str, str | list[str]]] = field(default_factory=dict)
    principles: dict[str, str] = field(default_factory=dict)
    canonical_docs: list[str] = field(default_factory=list)
    digest_heuristics: dict | None = None


def load_profile(path: Path) -> Profile:
    """Preserve JSON insertion order; reject unknown keys and invalid shapes."""
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("profile must be an object")
    for key in data:
        if key not in Profile.__dataclass_fields__:
            raise ValueError(f"unknown profile key: {key}")
    for key in ("principles", "canonical_docs"):
        if key not in data:
            raise ValueError(f"missing profile key: {key}")

    def strings(value):
        return isinstance(value, list) and all(isinstance(x, str) for x in value)

    for key in ("categories", "keyword_groups", "expand_on", "principles"):
        value = data.get(key, {})
        if not isinstance(value, dict):
            raise ValueError(f"{key} must be an object")
        for name, item in value.items():
            valid = isinstance(name, str)
            if key == "keyword_groups":
                valid = valid and strings(item)
            elif key == "expand_on":
                valid = (valid and isinstance(item, dict)
                         and set(item) == {"note", "phrases"}
                         and isinstance(item["note"], str) and strings(item["phrases"]))
            else:
                valid = valid and isinstance(item, str)
            if not valid:
                raise ValueError(f"invalid {key} entry: {name}")
    for key in ("anchor_phrases", "canonical_docs"):
        if not strings(data.get(key, [])):
            raise ValueError(f"{key} must be a list of strings")
    for slug in data.get("expand_on", {}):
        if slug in data.get("keyword_groups", {}):
            raise ValueError(f"expand_on slug collides with keyword group: {slug}")
    if "digest_heuristics" in data:
        tables = data["digest_heuristics"]
        keys = {"evidence_types", "evidence_fallback", "read_priority",
                "read_priority_fallback", "topic_clusters", "topic_fallback",
                "doc_impact", "doc_impact_fallback"}
        if not isinstance(tables, dict) or set(tables) != keys:
            raise ValueError("digest_heuristics must be an object with exactly: " + ", ".join(sorted(keys)))
        for key in ("evidence_types", "topic_clusters"):
            entries = tables[key]
            if not isinstance(entries, list) or not all(
                isinstance(entry, dict) and set(entry) == {"label", "terms"}
                and isinstance(entry["label"], str) and strings(entry["terms"])
                for entry in entries
            ):
                raise ValueError(f"digest_heuristics.{key} must be a list of label/terms objects")
        for key in ("evidence_fallback", "topic_fallback", "doc_impact_fallback"):
            if not isinstance(tables[key], str):
                raise ValueError(f"digest_heuristics.{key} must be a string")
        priorities = tables["read_priority"]
        if not isinstance(priorities, list) or len(priorities) != 2 or not all(
            strings(terms) for terms in priorities
        ):
            raise ValueError("digest_heuristics.read_priority must be two lists of strings")
        if type(tables["read_priority_fallback"]) is not int or tables["read_priority_fallback"] < 1:
            raise ValueError("digest_heuristics.read_priority_fallback must be a positive integer")
        impacts = tables["doc_impact"]
        if not isinstance(impacts, dict) or not all(
            isinstance(label, str) and isinstance(impact, str) for label, impact in impacts.items()
        ):
            raise ValueError("digest_heuristics.doc_impact must map labels to strings")
    return Profile(**data)
