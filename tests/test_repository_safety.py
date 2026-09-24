"""Tests for the public-repository safety boundary."""

from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
TOOLS_DIRECTORY = REPOSITORY_ROOT / "tools"
sys.path.insert(0, str(TOOLS_DIRECTORY))

import repository_safety  # noqa: E402
import run_repository_checks  # noqa: E402


class RepositorySafetyTests(unittest.TestCase):
    def test_sensitive_and_runtime_paths_are_ignored(self) -> None:
        for relative_path in repository_safety.IGNORED_PATHS:
            with self.subTest(path=relative_path):
                self.assertTrue(
                    repository_safety.is_ignored(REPOSITORY_ROOT, relative_path)
                )

    def test_required_public_paths_are_trackable(self) -> None:
        for relative_path in repository_safety.TRACKABLE_PATHS:
            with self.subTest(path=relative_path):
                self.assertFalse(
                    repository_safety.is_ignored(REPOSITORY_ROOT, relative_path)
                )

    def test_index_contains_no_forbidden_or_ignored_paths(self) -> None:
        report = repository_safety.inspect_index(REPOSITORY_ROOT)
        self.assertTrue(report.is_safe)

    def test_blueprint_public_index_exception_is_narrow(self) -> None:
        self.assertFalse(
            repository_safety.is_explicitly_forbidden(
                "blueprint/BLUEPRINT_SOURCES.md"
            )
        )
        self.assertTrue(
            repository_safety.is_explicitly_forbidden("blueprint/cofolio/README.md")
        )

    def test_force_added_synthetic_private_file_is_detected(self) -> None:
        with tempfile.TemporaryDirectory(prefix="steadyfolio-safety-test-") as temporary:
            repository = Path(temporary)
            subprocess.run(
                ["git", "init", "--quiet"],
                cwd=repository,
                check=True,
                capture_output=True,
                text=True,
            )
            (repository / ".gitignore").write_text("/private/\n", encoding="utf-8")
            private_directory = repository / "private"
            private_directory.mkdir()
            (private_directory / "synthetic-portfolio.json").write_text(
                '{"synthetic": true}\n', encoding="utf-8"
            )
            subprocess.run(
                ["git", "add", "--", ".gitignore"],
                cwd=repository,
                check=True,
                capture_output=True,
                text=True,
            )
            subprocess.run(
                ["git", "add", "-f", "--", "private/synthetic-portfolio.json"],
                cwd=repository,
                check=True,
                capture_output=True,
                text=True,
            )

            report = repository_safety.inspect_index(repository)

            self.assertEqual(report.tracked_count, 2)
            self.assertEqual(report.ignored_tracked_count, 1)
            self.assertEqual(report.forbidden_tracked_count, 1)


class PublicScanSnapshotTests(unittest.TestCase):
    def test_snapshot_uses_index_blob_for_a_modified_staged_file(self) -> None:
        with tempfile.TemporaryDirectory(prefix="steadyfolio-snapshot-test-") as temporary:
            repository = Path(temporary) / "repository"
            snapshot = Path(temporary) / "snapshot"
            repository.mkdir()
            snapshot.mkdir()
            subprocess.run(
                ["git", "init", "--quiet"],
                cwd=repository,
                check=True,
                capture_output=True,
                text=True,
            )

            candidate = repository / "candidate.txt"
            candidate.write_text("staged-version", encoding="utf-8")
            subprocess.run(
                ["git", "add", "--", "candidate.txt"],
                cwd=repository,
                check=True,
                capture_output=True,
                text=True,
            )
            candidate.write_text("working-tree-version", encoding="utf-8")

            copied = run_repository_checks.create_public_scan_snapshot(
                repository, snapshot
            )

            self.assertEqual(copied, 1)
            self.assertEqual(
                (snapshot / "candidate.txt").read_text(encoding="utf-8"),
                "staged-version",
            )

    def test_snapshot_includes_untracked_public_file(self) -> None:
        with tempfile.TemporaryDirectory(prefix="steadyfolio-snapshot-test-") as temporary:
            repository = Path(temporary) / "repository"
            snapshot = Path(temporary) / "snapshot"
            repository.mkdir()
            snapshot.mkdir()
            subprocess.run(
                ["git", "init", "--quiet"],
                cwd=repository,
                check=True,
                capture_output=True,
                text=True,
            )
            (repository / "candidate.txt").write_text(
                "untracked-version", encoding="utf-8"
            )

            copied = run_repository_checks.create_public_scan_snapshot(
                repository, snapshot
            )

            self.assertEqual(copied, 1)
            self.assertEqual(
                (snapshot / "candidate.txt").read_text(encoding="utf-8"),
                "untracked-version",
            )


if __name__ == "__main__":
    unittest.main()
