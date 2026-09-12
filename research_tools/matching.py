"""Ordered, case-insensitive phrase matching at word boundaries."""

import re

PLURAL_SUFFIXES = ("s", "es")


def match_phrases(text: str, phrases: list[str]) -> list[str]:
    """Accept a simple plural suffix on the text side of the last word."""
    matched: list[str] = []
    seen: set[str] = set()
    haystack = text.lower()
    suffixes = "|".join(re.escape(suffix) for suffix in PLURAL_SUFFIXES)
    for phrase in phrases:
        key = phrase.lower()
        if key in seen:
            continue
        if re.search(r"(?<!\w)" + re.escape(key) + "(?:" + suffixes + r")?(?!\w)", haystack):
            matched.append(phrase)
            seen.add(key)
    return matched
