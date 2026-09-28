"""Reproducibility, privacy, and runtime tests for the Codex plugin package."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPOSITORY_ROOT / "tools"))

import build_plugin  # noqa: E402


TRACKED_PLUGIN_ROOT = REPOSITORY_ROOT / "plugins" / "steadyfolio"
TRACKED_MARKETPLACE = (
    REPOSITORY_ROOT / ".agents" / "plugins" / "marketplace.json"
)


class PluginPackageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.temporary = tempfile.TemporaryDirectory()
        cls.generated_root = Path(cls.temporary.name) / "marketplace"
        cls.inventory = build_plugin.build_plugin(cls.generated_root)
        cls.plugin_root = (
            cls.generated_root / "plugins" / build_plugin.PLUGIN_NAME
        )

    @classmethod
    def tearDownClass(cls) -> None:
        cls.temporary.cleanup()

    def test_package_inventory_is_exact_and_contains_no_private_paths(self) -> None:
        self.assertEqual(self.inventory, build_plugin.expected_inventory())
        forbidden = {
            ".git",
            "private",
            "credentials",
            "secrets",
            "sessions",
            "state",
            "cache",
            "logs",
        }
        for relative in self.inventory:
            with self.subTest(path=relative):
                self.assertFalse({part.lower() for part in Path(relative).parts} & forbidden)

    def test_manifest_and_marketplace_are_installable_shapes(self) -> None:
        manifest = json.loads(
            (self.plugin_root / ".codex-plugin" / "plugin.json").read_text(
                encoding="utf-8"
            )
        )
        marketplace = json.loads(
            (
                self.generated_root
                / ".agents"
                / "plugins"
                / "marketplace.json"
            ).read_text(encoding="utf-8")
        )

        self.assertEqual(manifest["name"], build_plugin.PLUGIN_NAME)
        self.assertEqual(manifest["version"], build_plugin.PLUGIN_VERSION)
        self.assertEqual(manifest["skills"], "./skills/")
        self.assertEqual(marketplace["name"], build_plugin.MARKETPLACE_NAME)
        self.assertEqual(
            marketplace["plugins"][0]["source"]["path"],
            "./plugins/steadyfolio",
        )

    def test_bundled_skill_is_the_canonical_public_skill(self) -> None:
        canonical = (
            REPOSITORY_ROOT / ".agents" / "skills" / "steadyfolio" / "SKILL.md"
        )
        bundled = self.plugin_root / "skills" / "steadyfolio" / "SKILL.md"
        self.assertEqual(bundled.read_bytes(), canonical.read_bytes())

    def test_tracked_marketplace_reproduces_from_the_allowlist(self) -> None:
        tracked_files = [TRACKED_MARKETPLACE]
        tracked_files.extend(
            path for path in TRACKED_PLUGIN_ROOT.rglob("*") if path.is_file()
        )
        tracked_inventory = tuple(
            sorted(
                path.relative_to(REPOSITORY_ROOT).as_posix()
                for path in tracked_files
            )
        )
        self.assertEqual(tracked_inventory, self.inventory)
        for relative in self.inventory:
            with self.subTest(path=relative):
                self.assertEqual(
                    (REPOSITORY_ROOT / relative).read_bytes(),
                    (self.generated_root / relative).read_bytes(),
                )

    def test_bundled_runtime_imports_without_repository_source_path(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                "-S",
                "-c",
                (
                    "import sys; from pathlib import Path; "
                    "sys.path.insert(0, str(Path.cwd() / 'src')); "
                    "import steadyfolio; "
                    "assert callable(steadyfolio.run_committee_workflow); "
                    "assert callable(steadyfolio.review_equity)"
                ),
            ],
            cwd=self.plugin_root,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_builder_rejects_repository_local_output(self) -> None:
        output = REPOSITORY_ROOT / ".plugin-output-must-not-be-created"
        with self.assertRaisesRegex(ValueError, "outside the repository"):
            build_plugin.build_plugin(output)
        self.assertFalse(output.exists())

    def test_builder_rejects_existing_output_file_symlink(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            output = base / "marketplace"
            link = output / ".agents" / "plugins" / "marketplace.json"
            outside = base / "outside.json"
            link.parent.mkdir(parents=True)
            outside.write_text("outside\n", encoding="utf-8")
            try:
                link.symlink_to(outside)
            except OSError as error:
                self.skipTest(f"File symlinks are unavailable: {error}")

            with self.assertRaisesRegex(RuntimeError, "cannot contain symlinks"):
                build_plugin.build_plugin(output)
            self.assertEqual(outside.read_text(encoding="utf-8"), "outside\n")

    def test_builder_rejects_existing_output_directory_symlink(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            output = base / "marketplace"
            outside = base / "outside"
            output.mkdir()
            outside.mkdir()
            link = output / "plugins"
            try:
                link.symlink_to(outside, target_is_directory=True)
            except OSError as error:
                self.skipTest(f"Directory symlinks are unavailable: {error}")

            with self.assertRaisesRegex(RuntimeError, "cannot contain symlinks"):
                build_plugin.build_plugin(output)
            self.assertEqual(tuple(outside.iterdir()), ())


if __name__ == "__main__":
    unittest.main()
