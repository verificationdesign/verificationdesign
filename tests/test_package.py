"""Package dependency, parser ownership and entry-point checks."""

import ast
import contextlib
import io
from pathlib import Path
import sys
import unittest

from research_tools.__main__ import main


class PackageTests(unittest.TestCase):
    def test_no_command_prints_help_and_exits_two(self):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            code = main([])
        self.assertEqual(code, 2)
        self.assertIn("usage:", output.getvalue())

    def test_help_exits_zero(self):
        with contextlib.redirect_stdout(io.StringIO()), self.assertRaises(SystemExit) as caught:
            main(["--help"])
        self.assertEqual(caught.exception.code, 0)

    def test_imports_stdlib_and_regex_owner(self):
        root = Path(__file__).resolve().parents[1]
        allowed = set(sys.stdlib_module_names) | {"research_tools", "tests"}
        for directory in ("research_tools", "tests"):
            for path in (root / directory).rglob("*.py"):
                tree = ast.parse(path.read_text(), feature_version=(3, 11))
                for node in ast.walk(tree):
                    imports = []
                    if isinstance(node, ast.Import):
                        imports = [alias.name for alias in node.names]
                    elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                        imports = [node.module]
                    for name in imports:
                        self.assertIn(name.split(".")[0], allowed, (str(path), name))
                        if directory == "research_tools" and path.name != "records.py":
                            self.assertNotEqual(name, "re", "field extraction belongs in records.py")
