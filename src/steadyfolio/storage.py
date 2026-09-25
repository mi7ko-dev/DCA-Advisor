"""Private-workspace JSON and report persistence with atomic writes."""

from __future__ import annotations

import json
import os
from pathlib import Path
import re
import tempfile
from typing import Any

from .errors import StorageSafetyError, ValidationError
from .models import AnalysisResult, ContributionPlan, PortfolioState, to_json_value
from .validation import state_from_dict, state_to_dict


_SAFE_FILENAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")


def _workspace_root(workspace_root: str | Path) -> Path:
    supplied = Path(workspace_root)
    if not supplied.exists() or not supplied.is_dir():
        raise StorageSafetyError("The explicit workspace root must be a directory.")
    if supplied.is_symlink():
        raise StorageSafetyError("The workspace root cannot be a symlink.")
    return supplied.resolve(strict=True)


def _private_root(workspace_root: str | Path, *, create: bool) -> Path:
    root = _workspace_root(workspace_root)
    private = root / "private"
    if not private.exists() and not create:
        raise FileNotFoundError("The private workspace does not exist.")
    if private.exists() and private.is_symlink():
        raise StorageSafetyError("The private workspace cannot be a symlink.")
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
    private = _private_root(workspace_root, create=create_directories)
    directory = private / category
    if not directory.exists() and not create_directories:
        raise FileNotFoundError("The requested private output directory does not exist.")
    if directory.exists() and directory.is_symlink():
        raise StorageSafetyError("A private output directory cannot be a symlink.")
    if create_directories:
        directory.mkdir(mode=0o700, exist_ok=True)
    resolved_directory = directory.resolve(strict=True)
    if not resolved_directory.is_relative_to(private):
        raise StorageSafetyError("A private output directory escaped the workspace.")
    target = resolved_directory / filename
    if target.exists() and target.is_symlink():
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
