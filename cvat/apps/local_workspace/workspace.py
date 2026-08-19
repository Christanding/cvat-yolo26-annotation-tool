# SPDX-License-Identifier: MIT

import os
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path


EXTENSION_KINDS = {
    ".jpg": "image",
    ".png": "image",
    ".mp4": "video",
    ".mov": "video",
    ".zip": "archive",
}
INTERNAL_DIRECTORY = ".cvat-local"


@dataclass(frozen=True)
class WorkspaceEntry:
    path: str
    kind: str


class WorkspacePathError(ValueError):
    pass


def _is_internal_name(name: str) -> bool:
    return name.casefold() == INTERNAL_DIRECTORY.casefold()


def _resolve_directory(root: Path, relative_path: str) -> tuple[Path, Path]:
    try:
        resolved_root = root.resolve(strict=True)
    except OSError as error:
        raise WorkspacePathError("workspace root is unavailable") from error

    requested_path = Path(relative_path)
    if requested_path.is_absolute() or any(
        _is_internal_name(part) for part in requested_path.parts
    ):
        raise WorkspacePathError("workspace paths must be relative")

    try:
        directory = (resolved_root / requested_path).resolve(strict=True)
        directory.relative_to(resolved_root)
    except (OSError, ValueError) as error:
        raise WorkspacePathError("workspace path is invalid") from error

    if not directory.is_dir():
        raise WorkspacePathError("workspace path is not a directory")

    return resolved_root, directory


def _iter_candidates(directory: Path, recursive: bool) -> Iterator[Path]:
    if not recursive:
        yield from directory.iterdir()
        return

    for current_directory, directory_names, file_names in os.walk(directory):
        directory_names[:] = [name for name in directory_names if not _is_internal_name(name)]
        current_path = Path(current_directory)
        yield from (current_path / name for name in file_names)


def _is_inside_workspace(root: Path, candidate: Path) -> bool:
    try:
        candidate.resolve(strict=True).relative_to(root)
    except (OSError, ValueError):
        return False
    return True


def scan_workspace(
    root: Path,
    *,
    relative_path: str = "",
    recursive: bool = False,
) -> list[WorkspaceEntry]:
    resolved_root, directory = _resolve_directory(root, relative_path)
    entries: list[WorkspaceEntry] = []
    for candidate in _iter_candidates(directory, recursive):
        if _is_internal_name(candidate.name) or not _is_inside_workspace(
            resolved_root, candidate
        ):
            continue
        if candidate.is_dir():
            if not recursive:
                entries.append(
                    WorkspaceEntry(
                        path=candidate.relative_to(resolved_root).as_posix(),
                        kind="directory",
                    )
                )
            continue

        if kind := EXTENSION_KINDS.get(candidate.suffix.lower()):
            entries.append(
                WorkspaceEntry(
                    path=candidate.relative_to(resolved_root).as_posix(),
                    kind=kind,
                )
            )

    return sorted(
        entries,
        key=lambda entry: (entry.kind != "directory", entry.path.casefold()),
    )
