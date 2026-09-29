"""Regression tests for append-only research and durable-context persistence."""

from __future__ import annotations

from dataclasses import replace
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPOSITORY_ROOT / "src"))

from steadyfolio.errors import StorageSafetyError, ValidationError
from steadyfolio.private_records import (
    create_durable_context_record,
    create_research_cache_record,
    research_cache_record_from_dict,
    validate_research_cache_record,
)
from steadyfolio.storage import (
    list_durable_context_records,
    list_research_cache_records,
    save_durable_context_record,
    save_research_cache_record,
)


def _research_record(*, cache_mode: str = "derived_summary"):
    return create_research_cache_record(
        asset_identity="Synthetic Global Fund",
        ticker="SYN",
        currency="EUR",
        data_kind="fund_fee",
        conclusion="The disclosed synthetic fee is 0.20%.",
        facts=() if cache_mode == "citation_metadata" else ("Fee: 0.20%.",),
        source_title="Synthetic factsheet",
        publisher="Synthetic issuer",
        source_reference="https://example.invalid/synthetic-factsheet",
        primary_source=True,
        source_as_of="2026-09-29",
        source_period=None,
        retrieved_at="2026-09-29T12:30:00+03:00",
        methodology="Read the disclosed ongoing-charge field.",
        coverage="Single synthetic fund.",
        limitations=("Synthetic test evidence.",),
        assumptions=(),
        freshness_basis="Refresh after a newer factsheet.",
        refresh_after="2026-10-29T12:30:00+03:00",
        material_event_trigger="Issuer fee update.",
        terms_reference="Synthetic source terms permit a derived summary.",
        cache_mode=cache_mode,
        redistribution_permitted=False,
    )


def _git_workspace() -> tempfile.TemporaryDirectory[str]:
    temporary = tempfile.TemporaryDirectory(prefix="steadyfolio-private-records-")
    workspace = Path(temporary.name)
    subprocess.run(
        ["git", "init", "--quiet"],
        cwd=workspace,
        check=True,
        capture_output=True,
    )
    (workspace / ".gitignore").write_text("/private/\n", encoding="utf-8")
    return temporary


class PrivateRecordTests(unittest.TestCase):
    def test_research_cache_uses_validated_append_only_storage(self) -> None:
        record = _research_record()
        with _git_workspace() as temporary:
            workspace = Path(temporary)
            path = save_research_cache_record(workspace, record)

            self.assertEqual(path.parent, workspace / "private" / "research")
            self.assertRegex(
                path.name,
                r"^research-\d{8}T\d{12}Z-[0-9a-f]{32}\.json$",
            )
            self.assertEqual(list_research_cache_records(workspace), (record,))
            with self.assertRaisesRegex(FileExistsError, "overwrite was not approved"):
                save_research_cache_record(workspace, record)

    def test_research_cache_fails_closed_on_terms_and_unknown_fields(self) -> None:
        record = _research_record()
        with self.assertRaisesRegex(ValidationError, "cannot retain"):
            validate_research_cache_record(
                replace(record, cache_mode="citation_metadata")
            )

        payload = json.loads(json.dumps(record.__dict__))
        payload["unknown"] = "not allowed"
        with self.assertRaisesRegex(ValidationError, "unknown fields"):
            research_cache_record_from_dict(payload)

    def test_research_cache_rejects_unignored_git_target_before_write(self) -> None:
        record = _research_record()
        with tempfile.TemporaryDirectory(prefix="steadyfolio-private-records-") as temporary:
            workspace = Path(temporary)
            subprocess.run(
                ["git", "init", "--quiet"],
                cwd=workspace,
                check=True,
                capture_output=True,
            )
            with self.assertRaisesRegex(StorageSafetyError, "must be ignored"):
                save_research_cache_record(workspace, record)
            self.assertFalse((workspace / "private").exists())

    def test_context_records_are_append_only_and_corrections_link_history(self) -> None:
        first = create_durable_context_record(
            category="temporary_assumption",
            statement="Use the synthetic limit until confirmed.",
            source_kind="user_message",
            status="pending",
            recorded_at="2026-09-29T12:35:00+03:00",
            review_after="2026-10-06",
        )
        correction = create_durable_context_record(
            category="user_decision",
            statement="The synthetic limit is confirmed.",
            source_kind="user_confirmation",
            status="active",
            recorded_at="2026-09-29T12:36:00+03:00",
            effective_as_of="2026-09-29",
            supersedes_record_id=first.record_id,
        )
        with _git_workspace() as temporary:
            workspace = Path(temporary)
            with self.assertRaisesRegex(ValidationError, "existing record"):
                save_durable_context_record(workspace, correction)
            first_path = save_durable_context_record(workspace, first)
            correction_path = save_durable_context_record(workspace, correction)

            self.assertNotEqual(first_path, correction_path)
            self.assertEqual(
                list_durable_context_records(workspace),
                (first, correction),
            )

    def test_context_directory_symlink_is_rejected(self) -> None:
        record = create_durable_context_record(
            category="confirmed_fact",
            statement="Synthetic preference.",
            source_kind="user_message",
            status="active",
            recorded_at="2026-09-29T12:35:00+03:00",
        )
        with tempfile.TemporaryDirectory(prefix="steadyfolio-private-records-") as temporary:
            base = Path(temporary)
            workspace = base / "workspace"
            outside = base / "outside"
            (workspace / "private").mkdir(parents=True)
            outside.mkdir()
            try:
                os.symlink(outside, workspace / "private" / "context", target_is_directory=True)
            except OSError as error:
                self.skipTest(f"Directory symlinks are unavailable: {error}")
            with self.assertRaises(StorageSafetyError):
                save_durable_context_record(workspace, record)

    def test_invalid_loaded_record_is_never_reused(self) -> None:
        with _git_workspace() as temporary:
            workspace = Path(temporary)
            directory = workspace / "private" / "research"
            directory.mkdir(parents=True)
            path = directory / ("research-20260929T123000000000Z-" + "0" * 32 + ".json")
            path.write_text('{"schema_version":"1.0"}\n', encoding="utf-8")
            with self.assertRaisesRegex(ValidationError, "cannot be reused"):
                list_research_cache_records(workspace)


if __name__ == "__main__":
    unittest.main()
