"""Boundary contract written before implementation; accepted suffixes are s, es, ed and ing."""

import unittest

from research_tools.matching import match_phrases, INFLECTION_SUFFIXES


# Text, ordered phrases, exact ordered matches. Suffixes apply to the last word.
CASES = [
    ("bellman", ["llm"], []),
    ("LLM", ["llm"], ["llm"]),
    ("LLMs", ["llm"], ["llm"]),
    ("llm-based", ["llm"], ["llm"]),
    ("(LlM), AI agents!", ["AI agent", "llm"], ["AI agent", "llm"]),
    ("large language models", ["large language model"], ["large language model"]),
    ("AI agents", ["AI agent"], ["AI agent"]),
    ("AI agentic", ["AI agent"], []),
    ("toolboxes", ["toolbox"], ["toolbox"]),
    ("sandboxed", ["sandbox"], ["sandbox"]),
    ("sandboxing agents", ["sandbox", "AI agent"], ["sandbox"]),
    ("sandboxedly", ["sandbox"], []),
    ("judging", ["judge"], []),
    ("prellm llmish llmsuffix", ["llm"], []),
    ("large language modelers", ["large language model"], []),
    ("LLMs and agents", ["agent", "LLM", "llm", "Agent", "absent"], ["agent", "LLM"]),
    ("LLM", ["absent", "ABSENT", "llm", "LLM"], ["llm"]),
    ("llm_foo", ["llm"], []),
    ("a.b", ["a.b"], ["a.b"]),
    ("axb", ["a.b"], []),
    ("nothing", [], []),
]


class MatchingTests(unittest.TestCase):
    def test_contract(self):
        """Removing boundaries, suffix alternatives or ordered dedup fails the table."""
        self.assertEqual(INFLECTION_SUFFIXES, ("s", "es", "ed", "ing"))
        for text, phrases, expected in CASES:
            with self.subTest(text=text, phrases=phrases):
                self.assertEqual(match_phrases(text, phrases), expected)
