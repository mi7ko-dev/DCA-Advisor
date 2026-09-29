"""Build a deterministic SteadyFolio plugin installation archive."""

from __future__ import annotations

import argparse
import hashlib
import os
from pathlib import Path
import tempfile
import zipfile

import build_plugin


ARCHIVE_TIMESTAMP = (1980, 1, 1, 0, 0, 0)
ARCHIVE_FILE_MODE = 0o100644


def archive_name() -> str:
    """Return the canonical filename for the current plugin release."""

    return f"steadyfolio-{build_plugin.PLUGIN_VERSION}.zip"


def sha256_file(path: Path) -> str:
    """Return the lowercase SHA-256 digest for a file."""

    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def inspect_archive(path: Path) -> tuple[str, ...]:
    """Validate deterministic metadata and return the archive inventory."""

    expected = build_plugin.expected_inventory()
    with zipfile.ZipFile(path, "r") as archive:
        entries = archive.infolist()
        names = tuple(entry.filename for entry in entries)
        if names != expected:
            raise RuntimeError("Release archive inventory does not match the allowlist.")
        if len(names) != len(set(names)):
            raise RuntimeError("Release archive contains duplicate paths.")
        for entry in entries:
            parts = Path(entry.filename).parts
            if entry.is_dir() or not parts or ".." in parts:
                raise RuntimeError("Release archive contains an unsafe path.")
            if entry.date_time != ARCHIVE_TIMESTAMP:
                raise RuntimeError("Release archive contains non-deterministic timestamps.")
            if entry.create_system != 3:
                raise RuntimeError("Release archive contains non-Unix metadata.")
            if entry.external_attr >> 16 != ARCHIVE_FILE_MODE:
                raise RuntimeError("Release archive contains unexpected file modes.")
    return names


def build_release_archive(output: Path) -> tuple[Path, str, tuple[str, ...]]:
    """Build the allowlisted marketplace and package it deterministically."""

    output = output.absolute()
    if output.name != archive_name():
        raise ValueError(f"Release archive must be named {archive_name()}.")

    repository_root = build_plugin.REPOSITORY_ROOT.resolve()
    resolved_output = output.resolve()
    if resolved_output == repository_root or resolved_output.is_relative_to(
        repository_root
    ):
        raise ValueError("Release archive output must be outside the repository.")
    if output.exists():
        raise FileExistsError(f"Release archive already exists: {output}")

    output.parent.mkdir(parents=True, exist_ok=True)
    for component in (output.parent, *output.parent.parents):
        if component.is_symlink():
            raise RuntimeError("Release archive output cannot traverse a symlink.")

    file_descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{output.stem}-",
        suffix=".tmp",
        dir=output.parent,
    )
    os.close(file_descriptor)
    temporary_archive = Path(temporary_name)

    try:
        with tempfile.TemporaryDirectory(prefix="steadyfolio-release-build-") as root:
            marketplace_root = Path(root) / "marketplace"
            inventory = build_plugin.build_plugin(marketplace_root)
            with zipfile.ZipFile(
                temporary_archive,
                "w",
                compression=zipfile.ZIP_DEFLATED,
                compresslevel=9,
                strict_timestamps=True,
            ) as archive:
                for relative in inventory:
                    source = marketplace_root / relative
                    if source.is_symlink() or source.stat().st_nlink > 1:
                        raise RuntimeError("Release input cannot contain links.")
                    info = zipfile.ZipInfo(relative, date_time=ARCHIVE_TIMESTAMP)
                    info.create_system = 3
                    info.compress_type = zipfile.ZIP_DEFLATED
                    info.external_attr = ARCHIVE_FILE_MODE << 16
                    archive.writestr(
                        info,
                        source.read_bytes(),
                        compress_type=zipfile.ZIP_DEFLATED,
                        compresslevel=9,
                    )
        inventory = inspect_archive(temporary_archive)
        temporary_archive.replace(output)
    except BaseException:
        temporary_archive.unlink(missing_ok=True)
        raise

    return output, sha256_file(output), inventory


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build a deterministic SteadyFolio installation archive."
    )
    parser.add_argument(
        "--output",
        required=True,
        type=Path,
        help=f"Outside-repository output path named {archive_name()}.",
    )
    args = parser.parse_args()
    path, checksum, inventory = build_release_archive(args.output)
    print(
        f"Built {path.name} with {len(inventory)} allowlisted files at "
        f"{path.resolve()}"
    )
    print(f"SHA-256 {checksum}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
