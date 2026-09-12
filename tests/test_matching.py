"""Boundary contract written before implementation; accepted suffixes are s and es."""

import unittest

from research_tools.matching import match_phrases, PLURAL_SUFFIXES


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
        """Removing boundaries, plural alternatives or ordered dedup fails the table."""
        self.assertEqual(PLURAL_SUFFIXES, ("s", "es"))
        for text, phrases, expected in CASES:
            with self.subTest(text=text, phrases=phrases):
                self.assertEqual(match_phrases(text, phrases), expected)
