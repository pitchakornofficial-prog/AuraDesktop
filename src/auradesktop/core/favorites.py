"""Pure helpers for safely managing wallpaper favorite paths."""
from __future__ import annotations
from pathlib import Path
from typing import Iterable
import os


def _clean_paths(paths: Iterable[object]) -> list[str]:
    """Return a stable, duplicate-free list of non-empty string paths."""
    result: list[str] = []
    seen: set[str] = set()
    for value in paths:
        if not isinstance(value, (str, Path)):
            continue
        raw = str(value).strip()
        if not raw:
            continue
        # Use case-insensitive duplicate detection on Windows while preserving
        # the original path text for display and storage.
        key = raw.casefold() if os.name == 'nt' else raw
        if key not in seen:
            result.append(raw)
            seen.add(key)
    return result


def add_favorite_path(paths: Iterable[object], path: object) -> tuple[list[str], bool]:
    """Add a non-empty path if it is not already present."""
    favorites = _clean_paths(paths)
    if not isinstance(path, (str, Path)) or not str(path).strip():
        return favorites, False
    candidate = str(path).strip()
    key = candidate.casefold() if os.name == 'nt' else candidate
    existing = {p.casefold() if os.name == 'nt' else p for p in favorites}
    if key in existing:
        return favorites, False
    favorites.append(candidate)
    return favorites, True


def remove_favorite_path(paths: Iterable[object], path: object) -> list[str]:
    """Remove only the matching favorite entry; never touch the underlying file."""
    if not isinstance(path, (str, Path)):
        return _clean_paths(paths)
    candidate = str(path).strip()
    key = candidate.casefold() if os.name == 'nt' else candidate
    return [p for p in _clean_paths(paths)
            if (p.casefold() if os.name == 'nt' else p) != key]


def favorite_display_name(path: object) -> str:
    """Show missing favorite files explicitly rather than implying they work."""
    if not isinstance(path, (str, Path)) or not str(path).strip():
        return '(Invalid path)'
    item = Path(str(path))
    name = item.name or str(item)
    return name if item.is_file() else f'{name} (missing)'
