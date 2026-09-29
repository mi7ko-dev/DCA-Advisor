"""Tests for the deterministic SteadyFolio installation archive."""

from __future__ import annotations

import json
from pathlib import Path
import re
import sys
import tempfile
import unittest
import zipfile


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPOSITORY_ROOT / "tools"))

import build_plugin  # noqa: E402
import build_release  # noqa: E402


class ReleaseArchiveTests(unittest.TestCase):
    def test_release_version_is_consistent(self) -> None:
        project = (REPOSITORY_ROOT / "pyproject.toml").read_text(encoding="utf-8")
        match = re.search(r'^version = "([^"]+)"$', project, flags=re.MULTILINE)
        self.assertIsNotNone(match)
        self.assertEqual(match.group(1), build_plugin.PLUGIN_VERSION)

        manifest = json.loads(
            (
                REPOSITORY_ROOT
                / "plugins"
                / "steadyfolio"
                / ".codex-plugin"
                / "plugin.json"
            ).read_text(encoding="utf-8")
        )
        self.assertEqual(manifest["version"], build_plugin.PLUGIN_VERSION)

    def test_release_archive_is_reproducible_and_exact(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            first = root / "one" / build_release.archive_name()
            second = root / "two" / build_release.archive_name()

            _, first_digest, first_inventory = build_release.build_release_archive(
                first
            )
            _, second_digest, second_inventory = build_release.build_release_archive(
                second
            )

            self.assertEqual(first.read_bytes(), second.read_bytes())
            self.assertEqual(first_digest, second_digest)
            self.assertEqual(first_inventory, build_plugin.expected_inventory())
            self.assertEqual(second_inventory, build_plugin.expected_inventory())

            with zipfile.ZipFile(first, "r") as archive:
                manifest = json.loads(
                    archive.read(
                        "plugins/steadyfolio/.codex-plugin/plugin.json"
                    ).decode("utf-8")
                )
            self.assertEqual(manifest["version"], build_plugin.PLUGIN_VERSION)

    def test_release_archive_rejects_repository_output(self) -> None:
        output = REPOSITORY_ROOT / build_release.archive_name()
        with self.assertRaisesRegex(ValueError, "outside the repository"):
            build_release.build_release_archive(output)
        self.assertFalse(output.exists())

    def test_release_archive_rejects_wrong_name(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "steadyfolio.zip"
            with self.assertRaisesRegex(ValueError, build_release.archive_name()):
                build_release.build_release_archive(output)
            self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()
