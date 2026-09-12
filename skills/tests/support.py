"""Shared offline fixtures and isolated skill imports for script tests."""
import importlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
AUDIT = ROOT / "skills/verification-audit"
DESIGN = ROOT / "skills/verification-design"


def module(name, kind="audit"):
    # Each skill resolves its own loader defaults. Restore the global import namespace
    # so discovery order cannot make another test silently use the wrong skill.
    folder = ROOT / "skills" / ("verification-" + kind) / "scripts"
    names = {p.stem for p in folder.glob("*.py")}
    saved = {n: sys.modules.pop(n) for n in names if n in sys.modules}
    old_path = sys.path[:]
    try:
        sys.path.insert(0, str(folder))
        return importlib.import_module(name)
    finally:
        for n in names:
            sys.modules.pop(n, None)
        sys.modules.update(saved)
        sys.path[:] = old_path


def fixture(kind="audit"):
    folder = "audit-known-defect" if kind == "audit" else "design-sound"
    return json.loads((ROOT / "skills/fixtures" / folder / "record.json").read_text())


class ScriptCase(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.record = self.root / "record.json"
        self.output = self.root / "output.json"

    def run_script(self, kind, name, *args):
        return subprocess.run([sys.executable, str(ROOT / "skills" / ("verification-" + kind) / "scripts" / name),
                               *map(str, args)], capture_output=True, text=True)

    def call(self, kind, name, record, *args):
        self.record.write_text(json.dumps(record), encoding="utf-8")
        return self.run_script(kind, name, self.record, *args)

    def assert_rules(self, result, rules):
        self.assertEqual(result.returncode, 3, result.stdout + result.stderr)
        self.assertEqual({e["rule"] for e in json.loads(result.stdout)}, set(rules))

    def assert_refused(self, kind, name, args, input_path):
        skill = ROOT / "skills" / ("verification-" + kind)
        inside = skill / "assets" / "b1-never-written.json"
        self.assertFalse(inside.exists())
        protected = {input_path: input_path.read_bytes(), skill / "SKILL.md": (skill / "SKILL.md").read_bytes()}
        alias = self.root / "input-alias"
        if not alias.exists():
            alias.symlink_to(input_path)
        skill_alias = self.root / "skill-alias"
        if not skill_alias.exists():
            skill_alias.symlink_to(skill, target_is_directory=True)
        for output in (input_path, self.root / "sub" / ".." / input_path.name, alias,
                       inside, skill / "SKILL.md", skill_alias / "assets" / inside.name):
            with self.subTest(output=str(output)):
                result = self.run_script(kind, name, *args, "--output", output)
                self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
                self.assertEqual({e["rule"] for e in json.loads(result.stdout)}, {"usage"})
                self.assertFalse(inside.exists())
                for path, before in protected.items():
                    self.assertEqual(path.read_bytes(), before)
