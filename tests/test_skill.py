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

    def test_current_source_cache_and_context_contract_is_explicit(self) -> None:
        skill = SKILL_PATH.read_text(encoding="utf-8")
        protocol = (
            SKILL_ROOT / "references" / "research-and-context.md"
        ).read_text(encoding="utf-8")
        normalized = " ".join(protocol.split())

        self.assertIn("references/research-and-context.md", skill)
        self.assertIn("Do not ask for permission to research", skill)
        self.assertIn("`private/research/`", normalized)
        self.assertIn("`private/context/`", normalized)
        self.assertIn("append-only", normalized)
        self.assertIn("cache and redistribution permission", normalized)
        self.assertIn("single lead-owned evidence-gathering phase", normalized)
        self.assertIn("only direct user confirmation", normalized)
        self.assertIn("at most four targeted search queries", normalized)
        self.assertIn("eight source documents", normalized)
        self.assertIn("public instrument identity", normalized)
        self.assertIn("Unknown or ambiguous cache terms fail closed", normalized)
        self.assertIn("symlink", normalized)
        self.assertIn("exclusive-create", normalized)
        self.assertIn("`list_research_cache_records`", normalized)
        self.assertIn("`save_research_cache_record`", normalized)
        self.assertIn("`save_durable_context_record`", normalized)
        self.assertIn("use it only in memory", normalized)
        self.assertNotIn("cannot be cached safely", normalized)
        self.assertIn("routine contribution is missing a price", normalized)
        for category in (
            "confirmed_fact",
            "user_decision",
            "temporary_assumption",
            "proposal",
            "external_evidence",
        ):
            self.assertIn(f"`{category}`", normalized)

    def test_multi_agent_trigger_is_bounded_and_has_a_true_fallback(self) -> None:
        skill = SKILL_PATH.read_text(encoding="utf-8")
        protocol = (
            SKILL_ROOT / "references" / "multi-agent-review.md"
        ).read_text(encoding="utf-8")
        normalized = " ".join(protocol.split())

        self.assertIn("references/multi-agent-review.md", skill)
        self.assertIn("at least two independent Codex subagent roles", normalized)
        self.assertIn("one critic", normalized)
        self.assertIn("no retries or debate loop", normalized)
        self.assertIn("Do not start agents for a routine contribution", normalized)
        self.assertIn("no true multi-agent run", normalized)
        self.assertIn("`fork_turns=none`", normalized)
        self.assertIn("reject every unknown field", normalized)
        self.assertIn("remain memory-only by default", normalized)
        self.assertIn("`single_thread_sequential`", normalized)
        self.assertIn("`generic_agent_result_from_dict`", normalized)
        self.assertIn("`validate_generic_agent_result`", normalized)
        self.assertIn("`build_generic_critic_packet`", normalized)
        self.assertIn("generic-specialist-result.schema.json", normalized)
        self.assertIn("fewer than two valid independent specialist results", normalized)
        self.assertIn("A routine contribution stops", " ".join(skill.split()))
        self.assertIn("Broker access and order placement are prohibited", skill)

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

    def test_all_skill_files_are_tracked_or_public_candidates(self) -> None:
        tracked_result = subprocess.run(
            ["git", "ls-files", "-z", "--", ".agents/skills/steadyfolio"],
            cwd=REPOSITORY_ROOT,
            check=True,
            capture_output=True,
        )
        tracked = {
            item.decode("utf-8").replace("\\", "/")
            for item in tracked_result.stdout.split(b"\0")
            if item
        }
        candidate_result = subprocess.run(
            [
                "git",
                "ls-files",
                "--others",
                "--exclude-standard",
                "-z",
                "--",
                ".agents/skills/steadyfolio",
            ],
            cwd=REPOSITORY_ROOT,
            check=True,
            capture_output=True,
        )
        candidates = {
            item.decode("utf-8").replace("\\", "/")
            for item in candidate_result.stdout.split(b"\0")
            if item
        }
        expected = {
            path.relative_to(REPOSITORY_ROOT).as_posix()
            for path in SKILL_ROOT.rglob("*")
            if path.is_file()
        }
        self.assertEqual(tracked | candidates, expected)


if __name__ == "__main__":
    unittest.main()
