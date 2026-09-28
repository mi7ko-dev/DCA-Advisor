"""Private-workspace JSON and report persistence with atomic writes."""

from __future__ import annotations

import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
from typing import Any

from .errors import StorageSafetyError, ValidationError
from .committee_models import CommitteeResult
from .equity import validate_equity_review_result
from .equity_models import EquityReviewResult
from .models import AnalysisResult, ContributionPlan, PortfolioState, to_json_value
from .portfolio_policy import (
    PortfolioPolicyResult,
    validate_portfolio_policy_result,
)
from .research_models import PortfolioIntelligenceResult, ThesisReviewResult
from .validation import state_from_dict, state_to_dict
from .validation import validate_analysis_result, validate_contribution_plan


_SAFE_FILENAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")


def _workspace_root(workspace_root: str | Path) -> Path:
    supplied = Path(workspace_root)
    if not supplied.exists() or not supplied.is_dir():
        raise StorageSafetyError("The explicit workspace root must be a directory.")
    if supplied.is_symlink():
        raise StorageSafetyError("The workspace root cannot be a symlink.")
    return supplied.resolve(strict=True)


def _containing_git_worktree(root: Path) -> Path | None:
    for candidate in (root, *root.parents):
        marker = candidate / ".git"
        if marker.exists() or marker.is_symlink():
            return candidate
    return None


def _require_ignored_git_target(root: Path, target: Path) -> None:
    worktree = _containing_git_worktree(root)
    if worktree is None:
        return
    relative = target.relative_to(worktree).as_posix()
    try:
        tracked = subprocess.run(
            [
                "git",
                "-C",
                str(worktree),
                "--literal-pathspecs",
                "ls-files",
                "--error-unmatch",
                "--",
                relative,
            ],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
        ignored = subprocess.run(
            [
                "git",
                "-C",
                str(worktree),
                "check-ignore",
                "--quiet",
                "--no-index",
                "--",
                relative,
            ],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
    except OSError as error:
        raise StorageSafetyError(
            "Git safety could not be verified for the private output."
        ) from error
    if tracked.returncode == 0:
        raise StorageSafetyError("The private output target is already tracked by Git.")
    if tracked.returncode not in {0, 1} or ignored.returncode not in {0, 1}:
        raise StorageSafetyError(
            "Git safety could not be verified for the private output."
        )
    if ignored.returncode != 0:
        raise StorageSafetyError(
            "The private output target must be ignored by its containing Git repository."
        )


def _private_root(workspace_root: str | Path, *, create: bool) -> Path:
    root = _workspace_root(workspace_root)
    private = root / "private"
    if private.is_symlink():
        raise StorageSafetyError("The private workspace cannot be a symlink.")
    if not private.exists() and not create:
        raise FileNotFoundError("The private workspace does not exist.")
    if create:
        private.mkdir(mode=0o700, exist_ok=True)
    resolved = private.resolve(strict=True)
    if not resolved.is_relative_to(root):
        raise StorageSafetyError("The private workspace escaped its selected root.")
    return resolved


def _safe_target(
    workspace_root: str | Path,
    category: str,
    filename: str,
    *,
    create_directories: bool = True,
) -> Path:
    if not _SAFE_FILENAME.fullmatch(category) or not _SAFE_FILENAME.fullmatch(filename):
        raise StorageSafetyError("Private output names contain unsafe characters.")
    root = _workspace_root(workspace_root)
    _require_ignored_git_target(root, root / "private" / category / filename)
    private = _private_root(root, create=create_directories)
    directory = private / category
    if directory.is_symlink():
        raise StorageSafetyError("A private output directory cannot be a symlink.")
    if not directory.exists() and not create_directories:
        raise FileNotFoundError("The requested private output directory does not exist.")
    if create_directories:
        directory.mkdir(mode=0o700, exist_ok=True)
    resolved_directory = directory.resolve(strict=True)
    if not resolved_directory.is_relative_to(private):
        raise StorageSafetyError("A private output directory escaped the workspace.")
    target = resolved_directory / filename
    if target.is_symlink():
        raise StorageSafetyError("A private output file cannot be a symlink.")
    return target


def _atomic_write_text(target: Path, content: str, *, overwrite: bool) -> Path:
    if target.exists() and not overwrite:
        raise FileExistsError("Private output already exists; overwrite was not approved.")
    descriptor, temporary_name = tempfile.mkstemp(
        dir=target.parent, prefix=".steadyfolio-", suffix=".tmp", text=True
    )
    temporary = Path(temporary_name)
    try:
        try:
            os.chmod(temporary, 0o600)
        except OSError:
            pass
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        if overwrite:
            os.replace(temporary, target)
        else:
            try:
                os.link(temporary, target)
            except FileExistsError as error:
                raise FileExistsError(
                    "Private output appeared during the write; overwrite was not approved."
                ) from error
            except OSError as error:
                raise StorageSafetyError(
                    "The workspace does not support atomic non-overwriting writes."
                ) from error
            temporary.unlink()
        return target
    finally:
        if temporary.exists():
            temporary.unlink()


def _json_text(value: Any) -> str:
    return json.dumps(value, indent=2, ensure_ascii=True, sort_keys=True) + "\n"


def _validate_persisted_allocation_versions(
    existing: PortfolioState, replacement: PortfolioState
) -> None:
    replacement_by_id = {
        allocation.id: allocation for allocation in replacement.target_allocations
    }
    for allocation in existing.target_allocations:
        if allocation.status not in {"approved", "superseded"}:
            continue
        updated = replacement_by_id.get(allocation.id)
        if updated is None:
            raise ValidationError(
                "Approved allocation versions cannot be removed during overwrite."
            )
        immutable_fields = (
            allocation.effective_date,
            allocation.targets,
            allocation.rationale,
        )
        if immutable_fields != (
            updated.effective_date,
            updated.targets,
            updated.rationale,
        ):
            raise ValidationError(
                "Approved allocation version contents are immutable."
            )
        allowed_statuses = (
            {"approved", "superseded"}
            if allocation.status == "approved"
            else {"superseded"}
        )
        if updated.status not in allowed_statuses:
            raise ValidationError("An allocation version has an invalid status transition.")


def initialize_workspace(
    workspace_root: str | Path, initial_state: PortfolioState
) -> Path:
    """Create the initial private state without overwriting an existing state."""

    return save_state(workspace_root, initial_state, overwrite=False)


def save_state(
    workspace_root: str | Path,
    state: PortfolioState,
    *,
    overwrite: bool = False,
) -> Path:
    payload = state_to_dict(state)
    reparsed = state_from_dict(payload)
    if reparsed != state:
        raise ValidationError("Portfolio state did not round-trip through its schema.")
    target = _safe_target(workspace_root, "state", "portfolio.json")
    if overwrite and target.exists():
        try:
            existing = state_from_dict(json.loads(target.read_text(encoding="utf-8")))
        except (OSError, json.JSONDecodeError, ValidationError) as error:
            raise ValidationError(
                "The existing private portfolio state cannot be safely replaced."
            ) from error
        _validate_persisted_allocation_versions(existing, state)
    return _atomic_write_text(target, _json_text(payload), overwrite=overwrite)


def load_state(workspace_root: str | Path) -> PortfolioState:
    target = _safe_target(
        workspace_root,
        "state",
        "portfolio.json",
        create_directories=False,
    )
    if not target.is_file():
        raise FileNotFoundError("The private portfolio state does not exist.")
    try:
        raw = json.loads(target.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValidationError("The private portfolio state is not valid JSON.") from error
    return state_from_dict(raw)


def save_analysis_result(
    workspace_root: str | Path,
    result: AnalysisResult,
    *,
    filename: str = "analysis.json",
    overwrite: bool = False,
) -> Path:
    validate_analysis_result(result)
    target = _safe_target(workspace_root, "results", filename)
    return _atomic_write_text(
        target, _json_text(to_json_value(result)), overwrite=overwrite
    )


def save_contribution_plan(
    workspace_root: str | Path,
    plan: ContributionPlan,
    *,
    filename: str = "contribution-plan.json",
    overwrite: bool = False,
) -> Path:
    validate_contribution_plan(plan)
    target = _safe_target(workspace_root, "results", filename)
    return _atomic_write_text(
        target, _json_text(to_json_value(plan)), overwrite=overwrite
    )


def save_report(
    workspace_root: str | Path,
    report: str,
    *,
    filename: str = "portfolio-review.md",
    overwrite: bool = False,
) -> Path:
    if not report.strip():
        raise ValidationError("A private report cannot be empty.")
    target = _safe_target(workspace_root, "reports", filename)
    return _atomic_write_text(target, report.rstrip() + "\n", overwrite=overwrite)


def save_intelligence_result(
    workspace_root: str | Path,
    result: PortfolioIntelligenceResult,
    *,
    filename: str = "portfolio-intelligence.json",
    overwrite: bool = False,
) -> Path:
    target = _safe_target(workspace_root, "research", filename)
    return _atomic_write_text(
        target, _json_text(to_json_value(result)), overwrite=overwrite
    )


def save_thesis_review(
    workspace_root: str | Path,
    review: ThesisReviewResult,
    *,
    filename: str = "thesis-review.json",
    overwrite: bool = False,
) -> Path:
    target = _safe_target(workspace_root, "reviews", filename)
    return _atomic_write_text(
        target, _json_text(to_json_value(review)), overwrite=overwrite
    )


def save_committee_review(
    workspace_root: str | Path,
    result: CommitteeResult,
    *,
    filename: str = "committee-review.json",
    overwrite: bool = False,
) -> Path:
    """Persist an explicitly authorized review without changing portfolio state."""

    target = _safe_target(workspace_root, "reviews", filename)
    return _atomic_write_text(
        target, _json_text(to_json_value(result)), overwrite=overwrite
    )


def save_equity_review(
    workspace_root: str | Path,
    result: EquityReviewResult,
    *,
    filename: str = "equity-review.json",
    overwrite: bool = False,
) -> Path:
    """Persist an explicitly authorized equity review below private/reviews."""

    validate_equity_review_result(result)
    target = _safe_target(workspace_root, "reviews", filename)
    return _atomic_write_text(
        target, _json_text(to_json_value(result)), overwrite=overwrite
    )


def save_portfolio_policy_result(
    workspace_root: str | Path,
    result: PortfolioPolicyResult,
    *,
    filename: str = "portfolio-policy-result.json",
    overwrite: bool = False,
) -> Path:
    """Persist an explicitly authorized policy check below private/reviews."""

    validate_portfolio_policy_result(result)
    target = _safe_target(workspace_root, "reviews", filename)
    return _atomic_write_text(
        target, _json_text(to_json_value(result)), overwrite=overwrite
    )
