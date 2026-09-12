"""Ordered, case-insensitive phrase matching at word boundaries."""

from functools import lru_cache
import re

# Accepted on the text side of a phrase's last word: plural and verb inflections.
INFLECTION_SUFFIXES = ("s", "es", "ed", "ing")


@lru_cache(maxsize=4096)
def _pattern(key: str) -> re.Pattern:
    suffixes = "|".join(re.escape(suffix) for suffix in INFLECTION_SUFFIXES)
    return re.compile(r"(?<!\w)" + re.escape(key) + "(?:" + suffixes + r")?(?!\w)")


def match_phrases(text: str, phrases: list[str]) -> list[str]:
    """Return phrases found in text, in phrase order, deduplicated case-insensitively."""
    matched: list[str] = []
    seen: set[str] = set()
    haystack = text.lower()
    for phrase in phrases:
        key = phrase.lower()
        if key in seen:
            continue
        # Substring presence is necessary for a boundary match and is cheap to
        # test, so it screens out most phrases before the regex runs.
        if key in haystack and _pattern(key).search(haystack):
            matched.append(phrase)
            seen.add(key)
    return matched
