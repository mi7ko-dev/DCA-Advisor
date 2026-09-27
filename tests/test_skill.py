"""Structural tests for the public repo-local SteadyFolio skill."""

from __future__ import annotations

from pathlib import Path
import re
import subprocess
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = REPOSITORY_ROOT / ".agents" / "skills" / "steadyfolio"
SKILL_PATH = SKILL_ROOT / "SKILL.md"
OPENAI_CONFIG = SKILL_ROOT / "agents" / "openai.yaml"


class SkillStructureTests(unittest.TestCase):
    def test_frontmatter_name_matches_directory_and_description_is_actionable(self) -> None:
        content = SKILL_PATH.read_text(encoding="utf-8")
        lines = content.splitlines()
        self.assertEqual(lines[0], "---")
        closing_delimiter = lines.index("---", 1)
        frontmatter = "\n".join(lines[1:closing_delimiter])
        self.assertRegex(frontmatter, r"(?m)^name: steadyfolio$")
        self.assertRegex(frontmatter, r"(?m)^description: .+Use for .+do not use")
        self.assertEqual(SKILL_ROOT.name, "steadyfolio")

    def test_referenced_skill_files_exist_and_remain_inside_skill_root(self) -> None:
        content = SKILL_PATH.read_text(encoding="utf-8")
        references = re.findall(r"\((references/[^)]+)\)", content)
        self.assertTrue(references)
        resolved_root = SKILL_ROOT.resolve()
        for relative_path in references:
            with self.subTest(path=relative_path):
                resolved = (SKILL_ROOT / relative_path).resolve()
                self.assertTrue(resolved.is_relative_to(resolved_root))
                self.assertTrue(resolved.is_file())

    def test_host_metadata_supports_explicit_and_implicit_invocation(self) -> None:
        content = OPENAI_CONFIG.read_text(encoding="utf-8")
        self.assertIn('default_prompt: "Use $steadyfolio', content)
        self.assertIn("allow_implicit_invocation: true", content)

    def test_skill_contains_no_runtime_state_directories(self) -> None:
        forbidden_names = {
            "private",
            "state",
            "sessions",
            "logs",
            "cache",
            "memory",
        }
        discovered = {
            path.name.lower()
            for path in SKILL_ROOT.rglob("*")
            if path.is_dir()
        }
        self.assertFalse(discovered & forbidden_names)

    def test_all_skill_files_are_tracked(self) -> None:
        result = subprocess.run(
            ["git", "ls-files", "-z", "--", ".agents/skills/steadyfolio"],
            cwd=REPOSITORY_ROOT,
            check=True,
            capture_output=True,
        )
        tracked = {
            item.decode("utf-8").replace("\\", "/")
            for item in result.stdout.split(b"\0")
            if item
        }
        expected = {
            path.relative_to(REPOSITORY_ROOT).as_posix()
            for path in SKILL_ROOT.rglob("*")
            if path.is_file()
        }
        self.assertEqual(tracked, expected)


if __name__ == "__main__":
    unittest.main()
